"""
Fuzzy matching and confidence scoring for product normalization.

Confidence thresholds:
- >=85%: Auto-merge to existing product
- 65–84%: Near-miss — create product but flag for admin awareness ("review_flag")
- <65%: Create new product entry (data quality checked separately)
"""
from rapidfuzz import fuzz
from typing import Tuple, Optional, List
import logging
import re

logger = logging.getLogger(__name__)


class ProductMatcher:
    """Matches scraped products to existing master products using fuzzy matching"""

    # Confidence thresholds
    AUTO_MERGE_THRESHOLD = 0.85     # >=85% = automatic merge (lowered from 0.90)
    REVIEW_THRESHOLD = 0.65         # 65–84% = near-miss, create product + auto_missed flag
    # <65% = create new product (no flag)

    # Weights for scoring components
    # THC removed from scoring — mg vs % unit ambiguity makes it unreliable
    NAME_WEIGHT = 0.75
    BRAND_WEIGHT = 0.25
    THC_WEIGHT = 0.00

    @classmethod
    def score_match(
        cls,
        scraped_name: str,
        master_name: str,
        scraped_brand: str,
        master_brand: str,
        scraped_thc: Optional[float] = None,
        master_thc: Optional[float] = None
    ) -> Tuple[float, str]:
        """
        Calculate match confidence score between scraped and master product.

        Args:
            scraped_name: Product name from scraper
            master_name: Product name from database
            scraped_brand: Brand name from scraper
            master_brand: Brand name from database
            scraped_thc: THC percentage from scraper (optional)
            master_thc: THC percentage from database (optional)

        Returns:
            Tuple of (confidence_score, match_type)
            - confidence_score: 0.0 to 1.0
            - match_type: "auto_merge" | "review_flag" | "new_product"
        """
        # Normalize names for comparison
        normalized_scraped_name = cls.normalize_product_name(scraped_name)
        normalized_master_name = cls.normalize_product_name(master_name)
        normalized_scraped_brand = cls.normalize_brand_name(scraped_brand)
        normalized_master_brand = cls.normalize_brand_name(master_brand)

        # Name similarity (75% weight)
        # Use token_sort_ratio for word order independence
        name_similarity = fuzz.token_sort_ratio(
            normalized_scraped_name,
            normalized_master_name
        ) / 100.0

        # Brand similarity (25% weight)
        brand_similarity = fuzz.token_sort_ratio(
            normalized_scraped_brand,
            normalized_master_brand
        ) / 100.0

        # THC similarity (0% weight — disabled)
        thc_similarity = cls._calculate_thc_similarity(scraped_thc, master_thc)

        # Calculate weighted confidence score
        confidence = (
            name_similarity * cls.NAME_WEIGHT +
            brand_similarity * cls.BRAND_WEIGHT +
            thc_similarity * cls.THC_WEIGHT
        )

        # Determine match type based on thresholds
        if confidence >= cls.AUTO_MERGE_THRESHOLD:
            match_type = "auto_merge"
        elif confidence >= cls.REVIEW_THRESHOLD:
            match_type = "review_flag"
        else:
            match_type = "new_product"

        logger.debug(
            f"Match score: {confidence:.3f} ({match_type}) - "
            f"'{scraped_name}' vs '{master_name}' "
            f"[name={name_similarity:.2f}, brand={brand_similarity:.2f}]"
        )

        return confidence, match_type

    @classmethod
    def find_best_match(
        cls,
        scraped_name: str,
        scraped_brand: str,
        candidates: List[dict],
        scraped_thc: Optional[float] = None,
        min_threshold: float = 0.0,
        product_type: Optional[str] = None
    ) -> Tuple[Optional[dict], float, str]:
        """
        Find the best matching product from a list of candidates.

        Args:
            scraped_name: Product name from scraper
            scraped_brand: Brand name from scraper
            candidates: List of dicts with 'name', 'brand', 'thc_percentage', 'id',
                        and optionally 'product_type'
            scraped_thc: THC percentage from scraper
            min_threshold: Minimum confidence to consider a match
            product_type: Product type/category of the scraped product. When provided,
                          candidates are pre-filtered to the same type before scoring.
                          Falls back to all candidates if none of that type exist.

        Returns:
            Tuple of (best_match_dict, confidence_score, match_type)
            Returns (None, 0.0, "new_product") if no match found
        """
        # Pre-filter candidates by product_type if provided.
        # This significantly reduces false positives (flower won't match edibles)
        # and makes the threshold safer to lower.
        if product_type and product_type.lower() not in ("other", "unknown", ""):
            type_filtered = [
                c for c in candidates
                if c.get("product_type", "").lower() == product_type.lower()
            ]
            search_pool = type_filtered if type_filtered else candidates
        else:
            search_pool = candidates

        best_match = None
        best_score = 0.0
        best_type = "new_product"

        for candidate in search_pool:
            score, match_type = cls.score_match(
                scraped_name,
                candidate.get("name", ""),
                scraped_brand,
                candidate.get("brand", ""),
                scraped_thc,
                candidate.get("thc_percentage")
            )

            if score > best_score and score >= min_threshold:
                best_score = score
                best_match = candidate
                best_type = match_type

        return best_match, best_score, best_type

    @staticmethod
    def _calculate_thc_similarity(
        scraped_thc: Optional[float],
        master_thc: Optional[float]
    ) -> float:
        """
        Calculate THC percentage similarity.

        Returns 1.0 if both are None or if they're within tolerance.
        Returns lower score based on percentage difference.
        """
        if scraped_thc is None or master_thc is None:
            # If either is missing, don't penalize
            return 1.0

        # Calculate difference
        thc_diff = abs(scraped_thc - master_thc)

        # 30% THC difference = 0 score, linear interpolation
        max_diff = 30.0
        similarity = max(0.0, 1.0 - (thc_diff / max_diff))

        return similarity

    @staticmethod
    def normalize_product_name(name: str) -> str:
        """
        Normalize product name for comparison.

        - Lowercase
        - Remove trademark symbols
        - Collapse multiple spaces
        - Remove common suffixes
        """
        if not name:
            return ""

        normalized = (
            name.lower()
            .strip()
            .replace("®", "")
            .replace("™", "")
            .replace("  ", " ")
        )

        # Remove common size/weight suffixes that vary between sources
        normalized = re.sub(r'\s*\d+\.?\d*\s*(g|gram|grams|oz|mg)\s*$', '', normalized)

        return normalized.strip()

    @staticmethod
    def normalize_brand_name(name: str) -> str:
        """
        Normalize brand name for comparison.

        - Lowercase
        - Remove common suffixes (Inc., LLC, etc.)
        - Collapse spaces
        """
        if not name:
            return ""

        normalized = (
            name.lower()
            .strip()
            .replace("inc.", "")
            .replace("inc", "")
            .replace("llc", "")
            .replace("co.", "")
            .replace("  ", " ")
        )

        return normalized.strip()

    @classmethod
    def get_threshold_description(cls, confidence: float) -> str:
        """Get human-readable description of confidence level"""
        if confidence >= cls.AUTO_MERGE_THRESHOLD:
            return f"High confidence ({confidence:.0%}) - Auto-merge"
        elif confidence >= cls.REVIEW_THRESHOLD:
            return f"Near-miss ({confidence:.0%}) - Admin review recommended"
        else:
            return f"Low confidence ({confidence:.0%}) - New product"

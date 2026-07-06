"""
Fuzzy matching and confidence scoring for product normalization.

Confidence thresholds:
- >=85%: Auto-merge to existing product
- 65–84%: Near-miss — create product but flag for admin awareness ("review_flag")
- <65%: Create new product entry (data quality checked separately)
"""
from rapidfuzz import fuzz
from typing import Tuple, Optional, List, Set
import logging
import math
import re

from services.normalization.brand_aliases import BRAND_ALIASES

logger = logging.getLogger(__name__)

# Corporate suffixes stripped at word boundaries (\bco\b leaves "wholesomeco" intact)
_BRAND_SUFFIX_RE = re.compile(r"\b(inc|llc|co|corp|company|ltd)\b\.?", re.IGNORECASE)

# Product-form synonyms normalized to one spelling. Deliberately tiny —
# anything broader risks over-merging distinct products.
_NAME_SYNONYMS = {
    "cartridge": "cart",
    "pre-roll": "preroll",
    "pre roll": "preroll",
}


class ProductMatcher:
    """Matches scraped products to existing master products using fuzzy matching"""

    # Confidence thresholds
    AUTO_MERGE_THRESHOLD = 0.85     # >=85% = automatic merge (lowered from 0.90)
    REVIEW_THRESHOLD = 0.65         # 65–84% = near-miss, create product + auto_missed flag
    # <65% = create new product (no flag)

    # Weights for scoring components. When a signal is unavailable (e.g. weight
    # missing on either side) the remaining weights are renormalized:
    # 0.60/(0.60+0.20) and 0.20/(0.60+0.20) reproduce exactly the historical
    # 0.75/0.25 name/brand split, so the thresholds above stay valid for
    # weightless products.
    # THC removed from scoring — mg vs % unit ambiguity makes it unreliable.
    NAME_WEIGHT = 0.60
    BRAND_WEIGHT = 0.20
    WEIGHT_WEIGHT = 0.20

    # Relative tolerance for weight-in-grams equality (2% covers oz↔g rounding)
    WEIGHT_REL_TOL = 0.02

    @classmethod
    def score_match(
        cls,
        scraped_name: str,
        master_name: str,
        scraped_brand: str,
        master_brand: str,
        scraped_weight_g: Optional[float] = None,
        candidate_weight_set: Optional[Set[float]] = None
    ) -> Tuple[float, str]:
        """
        Calculate match confidence score between scraped and master product.

        Args:
            scraped_name: Product name from scraper
            master_name: Product name from database
            scraped_brand: Brand name from scraper
            master_brand: Brand name from database
            scraped_weight_g: Scraped weight normalized to grams (optional)
            candidate_weight_set: Weights (grams) of the master's variants (optional)

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

        # Use token_sort_ratio for word order independence
        name_similarity = fuzz.token_sort_ratio(
            normalized_scraped_name,
            normalized_master_name
        ) / 100.0

        brand_similarity = fuzz.token_sort_ratio(
            normalized_scraped_brand,
            normalized_master_brand
        ) / 100.0

        # Weight signal: 1.0 if the scraped weight matches any of the
        # candidate's variant weights, 0.0 if none match. Absent (not scored)
        # when either side lacks weight data.
        weight_similarity = cls._calculate_weight_similarity(
            scraped_weight_g, candidate_weight_set
        )

        # Weighted score with renormalization over the signals present, so a
        # missing weight signal reproduces the historical name/brand-only split.
        signals = [
            (name_similarity, cls.NAME_WEIGHT),
            (brand_similarity, cls.BRAND_WEIGHT),
        ]
        if weight_similarity is not None:
            signals.append((weight_similarity, cls.WEIGHT_WEIGHT))

        total_weight = sum(w for _, w in signals)
        confidence = sum(s * w for s, w in signals) / total_weight

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
            f"[name={name_similarity:.2f}, brand={brand_similarity:.2f}, "
            f"weight={weight_similarity if weight_similarity is not None else 'n/a'}]"
        )

        return confidence, match_type

    @classmethod
    def find_best_match(
        cls,
        scraped_name: str,
        scraped_brand: str,
        candidates: List[dict],
        scraped_weight_g: Optional[float] = None,
        min_threshold: float = 0.0,
        product_type: Optional[str] = None
    ) -> Tuple[Optional[dict], float, str]:
        """
        Find the best matching product from a list of candidates.

        Args:
            scraped_name: Product name from scraper
            scraped_brand: Brand name from scraper
            candidates: List of dicts with 'name', 'brand', 'id', and optionally
                        'product_type' and 'weight_grams_set' (variant weights)
            scraped_weight_g: Scraped weight normalized to grams
            min_threshold: Minimum confidence to consider a match
            product_type: Product type/category of the scraped product. When provided,
                          candidates are filtered to the same type before scoring —
                          no cross-type matching (a flower product never merges into
                          an edible; an empty same-type pool means new product).

        Returns:
            Tuple of (best_match_dict, confidence_score, match_type)
            Returns (None, 0.0, "new_product") if no match found
        """
        # Strict pre-filter by product_type. Products with a generic/unknown
        # category still search everything (we can't tell what they are).
        if product_type and product_type.lower() not in ("other", "unknown", ""):
            search_pool = [
                c for c in candidates
                if c.get("product_type", "").lower() == product_type.lower()
            ]
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
                scraped_weight_g=scraped_weight_g,
                candidate_weight_set=candidate.get("weight_grams_set")
            )

            if score > best_score and score >= min_threshold:
                best_score = score
                best_match = candidate
                best_type = match_type

        return best_match, best_score, best_type

    @classmethod
    def _calculate_weight_similarity(
        cls,
        scraped_weight_g: Optional[float],
        candidate_weight_set: Optional[Set[float]]
    ) -> Optional[float]:
        """
        Weight-match signal against a candidate's variant weights.

        Returns None (signal absent) when either side has no weight data, so
        the caller renormalizes over the remaining signals instead of guessing.
        """
        if scraped_weight_g is None or not candidate_weight_set:
            return None

        for w in candidate_weight_set:
            if w is not None and math.isclose(w, scraped_weight_g, rel_tol=cls.WEIGHT_REL_TOL):
                return 1.0
        return 0.0

    @staticmethod
    def normalize_product_name(name: str) -> str:
        """
        Normalize product name for comparison.

        - Lowercase
        - Remove trademark symbols and punctuation (keeps '#' for strain
          numbers like "GMO #4" and '.' for decimals)
        - Normalize form-word synonyms (cartridge→cart, pre-roll→preroll)
        - Collapse all whitespace
        - Remove trailing size/weight suffixes
        """
        if not name:
            return ""

        normalized = name.lower().strip()

        # Form-word synonyms before punctuation stripping ("pre-roll" has a hyphen)
        for variant, canonical in _NAME_SYNONYMS.items():
            normalized = normalized.replace(variant, canonical)

        # Strip punctuation except '#' (strain numbers) and '.' (decimals)
        normalized = re.sub(r"[^\w\s#.]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # Remove common size/weight suffixes that vary between sources
        normalized = re.sub(r'\s*\d+\.?\d*\s*(g|gram|grams|oz|mg)\s*$', '', normalized)

        return normalized.strip()

    @staticmethod
    def normalize_brand_name(name: str) -> str:
        """
        Normalize brand name for comparison.

        - Lowercase
        - Remove corporate suffixes (Inc., LLC, Co., ...) at word boundaries
          only — "Incredibles" and "WholesomeCo" stay intact
        - Strip punctuation, collapse whitespace
        - Resolve known aliases to a canonical form (BRAND_ALIASES)
        """
        if not name:
            return ""

        normalized = name.lower().strip()
        normalized = _BRAND_SUFFIX_RE.sub("", normalized)
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return BRAND_ALIASES.get(normalized, normalized)

    @classmethod
    def get_threshold_description(cls, confidence: float) -> str:
        """Get human-readable description of confidence level"""
        if confidence >= cls.AUTO_MERGE_THRESHOLD:
            return f"High confidence ({confidence:.0%}) - Auto-merge"
        elif confidence >= cls.REVIEW_THRESHOLD:
            return f"Near-miss ({confidence:.0%}) - Admin review recommended"
        else:
            return f"Low confidence ({confidence:.0%}) - New product"

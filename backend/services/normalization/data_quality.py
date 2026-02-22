"""
Data quality checks for scraped products.

Determines whether a newly created product should be flagged for admin
cleanup. Checks are intentionally limited to the user-confirmed triggers:
1. Junk/garbage still present in name after cleaning
2. Missing or zero price
3. Unknown/missing brand

NOT flagged (user explicitly excluded):
- Missing weight
- Missing category
"""
from typing import List, Tuple
from services.scrapers.base_scraper import ScrapedProduct
import logging
import re

logger = logging.getLogger(__name__)

# Patterns that indicate junk survived the name cleaner.
# Only checked against the CLEANED name (after clean_product_name() ran),
# so these catch junk the cleaner couldn't remove.
_JUNK_PATTERNS = [
    re.compile(r'<[^>]+>'),                   # HTML tags
    re.compile(r'&[a-z]+;', re.IGNORECASE),   # HTML entities
    re.compile(r'[\x00-\x1F\x7F]'),           # Actual control characters (NUL, DEL, etc.)
    re.compile(r'\s{3,}'),                     # Excessive whitespace (3+) — cleaner normalizes this
    # "Add to cart", "Add N/A to cart", "Add 1g to cart" — broader pattern
    re.compile(r'add\s+(?:\S+\s+)?to\s+cart', re.IGNORECASE),
    re.compile(r'\$\d+\.?\d*'),               # Stray prices
    re.compile(r'\d+\s*%\s*off', re.IGNORECASE),
]

# Brand values that count as "unknown"
_UNKNOWN_BRANDS = {"", "UNKNOWN", "N/A", "NULL", "NONE", "-", "NA"}


def check_data_quality(
    scraped: ScrapedProduct,
    cleaned_name: str,
) -> Tuple[bool, List[str]]:
    """
    Check if a scraped product has dirty data requiring admin cleanup.

    Args:
        scraped: The original ScrapedProduct from the scraper
        cleaned_name: The name after clean_product_name() has been applied

    Returns:
        Tuple of (is_dirty, issue_tags)
        - is_dirty: True if at least one quality check fails
        - issue_tags: List of string tags describing the issues found
    """
    issues: List[str] = []

    # 1. Junk still present in name after cleaning
    if _has_junk_in_name(scraped.name, cleaned_name):
        issues.append("junk_in_name")

    # 2. Missing or zero price
    if scraped.price is None or scraped.price <= 0:
        issues.append("missing_price")

    # 3. Unknown/missing brand (skip for hardware — accessories don't require a cannabis brand)
    if scraped.category != "hardware" and _is_unknown_brand(scraped.brand):
        issues.append("unknown_brand")

    is_dirty = len(issues) > 0

    if is_dirty:
        logger.info(
            f"Dirty data detected for '{cleaned_name}': {issues}"
        )

    return is_dirty, issues


def _has_junk_in_name(raw_name: str, cleaned_name: str) -> bool:
    """
    Check if the name still contains junk after cleaning.

    Only checks whether known junk patterns remain in the cleaned name.

    Note: a reduction-ratio check (raw vs cleaned length) was removed because
    it produced false positives whenever the cleaner correctly stripped
    Curaleaf-specific artifacts ("mg Wellness", "Add 30g to cart", etc.).
    If the cleaner did its job, the stored name is fine — no flag needed.
    """
    if not raw_name or not cleaned_name:
        return False

    # Check if known junk patterns remain in the cleaned name
    for pattern in _JUNK_PATTERNS:
        if pattern.search(cleaned_name):
            return True

    return False


def _is_unknown_brand(brand: str) -> bool:
    """Check if brand is effectively unknown."""
    if not brand:
        return True
    return brand.strip().upper() in _UNKNOWN_BRANDS

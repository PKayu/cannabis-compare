"""
Flag analyzer utilities for computing match types and data quality scores.

This module provides helper functions for the cleanup queue to categorize and prioritize flags.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from models import ScraperFlag, Price

# Valid product categories
VALID_CATEGORIES = [
    'flower', 'concentrate', 'edible', 'vaporizer',
    'topical', 'tincture', 'pre-roll', 'other'
]


def get_matched_product_dispensary_ids(matched_product_id: UUID, db: Session) -> List[UUID]:
    """
    Get list of dispensary IDs where the matched product is sold.

    Args:
        matched_product_id: UUID of the matched product
        db: Database session

    Returns:
        List of dispensary UUIDs where the product has prices
    """
    dispensary_ids = (
        db.query(Price.dispensary_id)
        .filter(Price.product_id == matched_product_id)
        .distinct()
        .all()
    )

    return [str(disp_id[0]) for disp_id in dispensary_ids]


def compute_match_type(flag: ScraperFlag, db: Session) -> Optional[str]:
    """
    Determine if a flag represents a cross-dispensary match or same-dispensary match.

    Compares the flag's dispensary with the dispensaries where the matched product is sold.

    Args:
        flag: ScraperFlag instance
        db: Database session

    Returns:
        "cross_dispensary" if matched product is sold at different dispensaries
        "same_dispensary" if matched product is sold at the same dispensary
        None if no matched product exists
    """
    if not flag.matched_product_id:
        return None

    matched_product_dispensary_ids = get_matched_product_dispensary_ids(
        flag.matched_product_id, db
    )

    flag_dispensary_str = str(flag.dispensary_id)

    # If matched product is sold at the same dispensary as the flag
    if flag_dispensary_str in matched_product_dispensary_ids:
        return "same_dispensary"
    else:
        return "cross_dispensary"


def compute_data_quality(flag: ScraperFlag) -> str:
    """
    Score flag data quality based on completeness and confidence.

    Checks for common quality issues:
    - Missing or invalid brand name
    - Missing weight
    - Missing or invalid category
    - Low confidence score
    - Missing product URL
    - Missing cannabinoid data

    Args:
        flag: ScraperFlag instance

    Returns:
        "good" if 0 quality issues (high quality data)
        "fair" if 1-2 quality issues (acceptable but needs review)
        "poor" if 3+ quality issues (low quality, needs cleanup)
    """
    quality_issues = []

    # Check brand name
    if (not flag.brand_name or
        flag.brand_name.upper() in ["N/A", "UNKNOWN", "NULL", ""]):
        quality_issues.append("missing_brand")

    # Check weight
    if not flag.original_weight or flag.original_weight.strip() == "":
        quality_issues.append("missing_weight")

    # Check category
    if (not flag.original_category or
        flag.original_category.lower() not in VALID_CATEGORIES):
        quality_issues.append("invalid_category")

    # Check confidence score
    if flag.confidence_score < 0.7:
        quality_issues.append("low_confidence")

    # Check product URL
    if not flag.original_url or flag.original_url.strip() == "":
        quality_issues.append("missing_url")

    # Check cannabinoid data
    if flag.original_thc is None and flag.original_cbd is None:
        quality_issues.append("missing_cannabinoids")

    # Score based on number of issues
    issue_count = len(quality_issues)

    if issue_count == 0:
        return "good"
    elif issue_count <= 2:
        return "fair"
    else:
        return "poor"

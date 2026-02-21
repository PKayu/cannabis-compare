"""
Tests for data quality checker.

Run with: pytest backend/tests/test_data_quality.py -v
"""
import pytest
from services.normalization.data_quality import check_data_quality
from services.scrapers.base_scraper import ScrapedProduct


def _make_scraped(
    name: str = "Blue Dream",
    brand: str = "WholesomeCo",
    price: float = 45.0,
    weight: str = "3.5g",
    category: str = "flower",
    thc_percentage: float = 22.0,
    cbd_percentage: float = 0.5,
    url: str = "https://example.com/product",
) -> ScrapedProduct:
    """Helper to build a ScrapedProduct with sensible defaults."""
    return ScrapedProduct(
        name=name,
        brand=brand,
        price=price,
        weight=weight,
        category=category,
        thc_percentage=thc_percentage,
        cbd_percentage=cbd_percentage,
        url=url,
    )


class TestCleanProduct:
    """Products with clean data should NOT be flagged."""

    def test_clean_product_returns_false(self):
        scraped = _make_scraped()
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is False
        assert issues == []

    def test_missing_weight_not_flagged(self):
        """Missing weight is explicitly excluded from dirty triggers."""
        scraped = _make_scraped(weight="")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is False
        assert "missing_weight" not in issues

    def test_missing_weight_none_not_flagged(self):
        scraped = _make_scraped(weight=None)
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is False

    def test_missing_category_not_flagged(self):
        """Missing category is explicitly excluded from dirty triggers."""
        scraped = _make_scraped(category="")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is False
        assert "missing_category" not in issues

    def test_missing_category_none_not_flagged(self):
        scraped = _make_scraped(category=None)
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is False


class TestMissingPrice:
    """Missing or zero price should be flagged."""

    def test_none_price(self):
        scraped = _make_scraped(price=None)
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is True
        assert "missing_price" in issues

    def test_zero_price(self):
        scraped = _make_scraped(price=0)
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is True
        assert "missing_price" in issues

    def test_negative_price(self):
        scraped = _make_scraped(price=-5.0)
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is True
        assert "missing_price" in issues

    def test_valid_price_not_flagged(self):
        scraped = _make_scraped(price=0.01)
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert "missing_price" not in issues


class TestUnknownBrand:
    """Unknown/missing brand should be flagged."""

    def test_none_brand(self):
        scraped = _make_scraped(brand=None)
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is True
        assert "unknown_brand" in issues

    def test_empty_brand(self):
        scraped = _make_scraped(brand="")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is True
        assert "unknown_brand" in issues

    def test_unknown_brand_string(self):
        scraped = _make_scraped(brand="UNKNOWN")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is True
        assert "unknown_brand" in issues

    def test_na_brand(self):
        scraped = _make_scraped(brand="N/A")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is True
        assert "unknown_brand" in issues

    def test_none_string_brand(self):
        scraped = _make_scraped(brand="None")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is True
        assert "unknown_brand" in issues

    def test_dash_brand(self):
        scraped = _make_scraped(brand="-")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is True
        assert "unknown_brand" in issues

    def test_valid_brand_not_flagged(self):
        scraped = _make_scraped(brand="WholesomeCo")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert "unknown_brand" not in issues

    def test_case_insensitive_unknown(self):
        scraped = _make_scraped(brand="unknown")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert "unknown_brand" in issues

    def test_whitespace_brand(self):
        scraped = _make_scraped(brand="  ")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert "unknown_brand" in issues


class TestJunkInName:
    """Names with junk should be flagged."""

    def test_html_tags_in_cleaned_name(self):
        scraped = _make_scraped(name="Blue Dream <b>Sale</b>")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream <b>Sale</b>")
        assert is_dirty is True
        assert "junk_in_name" in issues

    def test_html_entities_in_cleaned_name(self):
        scraped = _make_scraped(name="Blue Dream &amp; More")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream &amp; More")
        assert is_dirty is True
        assert "junk_in_name" in issues

    def test_excessive_whitespace_in_cleaned_name(self):
        scraped = _make_scraped(name="Blue   Dream   Flower")
        is_dirty, issues = check_data_quality(scraped, "Blue   Dream   Flower")
        assert is_dirty is True
        assert "junk_in_name" in issues

    def test_add_to_cart_in_cleaned_name(self):
        scraped = _make_scraped(name="Blue Dream Add to Cart")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream Add to Cart")
        assert is_dirty is True
        assert "junk_in_name" in issues

    def test_stray_price_in_cleaned_name(self):
        scraped = _make_scraped(name="Blue Dream $45.00")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream $45.00")
        assert is_dirty is True
        assert "junk_in_name" in issues

    def test_heavy_reduction_ratio(self):
        """If cleaning removed >30% of the name, that's suspicious."""
        raw = "Blue Dream - SALE! BUY NOW! Limited Time Offer!!!"
        cleaned = "Blue Dream"
        scraped = _make_scraped(name=raw)
        is_dirty, issues = check_data_quality(scraped, cleaned)
        assert is_dirty is True
        assert "junk_in_name" in issues

    def test_clean_name_not_flagged(self):
        scraped = _make_scraped(name="Blue Dream")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert "junk_in_name" not in issues

    def test_empty_names_not_flagged(self):
        """Edge case: empty raw/cleaned names should not crash."""
        scraped = _make_scraped(name="")
        is_dirty, issues = check_data_quality(scraped, "")
        assert "junk_in_name" not in issues


class TestMultipleIssues:
    """Multiple issues should all be detected."""

    def test_missing_price_and_unknown_brand(self):
        scraped = _make_scraped(price=None, brand="UNKNOWN")
        is_dirty, issues = check_data_quality(scraped, "Blue Dream")
        assert is_dirty is True
        assert "missing_price" in issues
        assert "unknown_brand" in issues
        assert len(issues) == 2

    def test_all_three_issues(self):
        scraped = _make_scraped(
            name="Blue Dream <b>Sale</b> Add to Cart",
            price=0,
            brand=""
        )
        is_dirty, issues = check_data_quality(
            scraped, "Blue Dream <b>Sale</b> Add to Cart"
        )
        assert is_dirty is True
        assert "junk_in_name" in issues
        assert "missing_price" in issues
        assert "unknown_brand" in issues
        assert len(issues) == 3

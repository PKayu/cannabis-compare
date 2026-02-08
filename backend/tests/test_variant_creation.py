"""Tests for variant creation logic"""
import pytest
from models import Product, Brand, Price
from services.normalization.scorer import find_or_create_variant
from services.scrapers.base_scraper import ScrapedProduct


@pytest.fixture
def setup_parent_product(db_session):
    """Create a parent product with brand for testing"""
    brand = Brand(id="brand-test", name="Test Brand")
    db_session.add(brand)

    parent = Product(
        id="parent-001",
        name="Blue Dream",
        product_type="flower",
        thc_percentage=22.5,
        cbd_percentage=0.1,
        brand_id="brand-test",
        is_master=True,
        normalization_confidence=1.0
    )
    db_session.add(parent)
    db_session.flush()
    return parent


@pytest.fixture
def scraped_product():
    """Create a test ScrapedProduct"""
    return ScrapedProduct(
        name="Blue Dream",
        brand="Test Brand",
        category="flower",
        price=45.00,
        thc_percentage=22.5,
        cbd_percentage=0.1,
        weight="3.5g"
    )


class TestFindOrCreateVariant:
    """Test find_or_create_variant() function"""

    def test_creates_new_variant(self, db_session, setup_parent_product, scraped_product):
        """Should create a new variant when none exists"""
        variant = find_or_create_variant(
            db_session,
            setup_parent_product.id,
            "3.5g",
            scraped_product
        )

        assert variant is not None
        assert variant.is_master is False
        assert variant.master_product_id == setup_parent_product.id
        assert variant.weight == "3.5g"
        assert variant.weight_grams == 3.5
        assert variant.name == "Blue Dream"

    def test_finds_existing_variant(self, db_session, setup_parent_product, scraped_product):
        """Should return existing variant if same weight exists"""
        # Create first variant
        variant1 = find_or_create_variant(
            db_session,
            setup_parent_product.id,
            "3.5g",
            scraped_product
        )

        # Try to create again with same weight
        variant2 = find_or_create_variant(
            db_session,
            setup_parent_product.id,
            "3.5g",
            scraped_product
        )

        assert variant1.id == variant2.id

    def test_creates_different_variants_for_different_weights(
        self, db_session, setup_parent_product, scraped_product
    ):
        """Should create separate variants for different weights"""
        variant_3g = find_or_create_variant(
            db_session,
            setup_parent_product.id,
            "3.5g",
            scraped_product
        )

        variant_7g = find_or_create_variant(
            db_session,
            setup_parent_product.id,
            "7g",
            scraped_product
        )

        assert variant_3g.id != variant_7g.id
        assert variant_3g.weight_grams == 3.5
        assert variant_7g.weight_grams == 7.0

    def test_variant_inherits_parent_fields(
        self, db_session, setup_parent_product, scraped_product
    ):
        """Variant should inherit product_type and brand from parent"""
        variant = find_or_create_variant(
            db_session,
            setup_parent_product.id,
            "1oz",
            scraped_product
        )

        assert variant.product_type == setup_parent_product.product_type
        assert variant.brand_id == setup_parent_product.brand_id

    def test_none_weight_creates_variant(
        self, db_session, setup_parent_product, scraped_product
    ):
        """Should handle None weight gracefully"""
        variant = find_or_create_variant(
            db_session,
            setup_parent_product.id,
            None,
            scraped_product
        )

        assert variant is not None
        assert variant.is_master is False
        assert variant.weight is None
        assert variant.weight_grams is None


class TestVariantPriceRelationship:
    """Test that prices correctly attach to variants"""

    def test_price_on_variant_not_parent(
        self, db_session, setup_parent_product, scraped_product
    ):
        """Prices should be created on variant products, not parents"""
        from models import Dispensary

        dispensary = Dispensary(
            id="disp-test",
            name="Test Dispensary",
            location="Test Location"
        )
        db_session.add(dispensary)

        variant = find_or_create_variant(
            db_session,
            setup_parent_product.id,
            "3.5g",
            scraped_product
        )

        price = Price(
            product_id=variant.id,
            dispensary_id="disp-test",
            amount=45.00,
            in_stock=True
        )
        db_session.add(price)
        db_session.flush()

        # Price should be on variant, not parent
        parent_prices = db_session.query(Price).filter(
            Price.product_id == setup_parent_product.id
        ).all()
        variant_prices = db_session.query(Price).filter(
            Price.product_id == variant.id
        ).all()

        assert len(parent_prices) == 0
        assert len(variant_prices) == 1
        assert variant_prices[0].amount == 45.00

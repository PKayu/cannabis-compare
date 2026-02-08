"""
Tests for product name cleaning in the ConfidenceScorer.

Verifies that weights are removed from product names when creating
parent products and stored separately in variant weight fields.
"""
import pytest
from database import SessionLocal, engine
from models import Base, Product, Brand, Price
from services.normalization.scorer import ConfidenceScorer
from services.scrapers.base_scraper import ScrapedProduct


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_brand(db):
    """Create a test brand."""
    brand = Brand(name="Test Brand")
    db.add(brand)
    db.commit()
    return brand


def test_scorer_removes_weight_from_parent_name(db, test_brand):
    """
    Test that creating a new product with weight in name results in:
    - Parent product with clean name (no weight)
    - Variant product with clean name + separate weight field
    """
    # Create a scraped product with weight in name
    scraped = ScrapedProduct(
        name="Blue Dream 3.5g",  # Weight embedded in name
        category="flower",
        brand="Test Brand",
        price=45.00,
        weight=None,  # Scraper didn't extract weight separately
        thc_percentage=22.5,
        cbd_percentage=0.1,
        in_stock=True
    )

    # Process the scraped product
    variant_id, action = ConfidenceScorer.process_scraped_product(
        db=db,
        scraped_product=scraped,
        dispensary_id="test-disp-001",
        candidates=[]
    )

    db.commit()

    # Verify action taken
    assert action == "new_product", "Should create a new product"
    assert variant_id is not None, "Should return a variant ID"

    # Get the created variant
    variant = db.query(Product).filter(Product.id == variant_id).first()
    assert variant is not None, "Variant should exist"
    assert variant.is_master == False, "Should be a variant product"

    # Get the parent product
    parent = db.query(Product).filter(Product.id == variant.master_product_id).first()
    assert parent is not None, "Parent should exist"
    assert parent.is_master == True, "Should be a parent product"

    # Verify names are clean (no weight)
    assert parent.name == "Blue Dream", f"Parent name should be clean, got: {parent.name}"
    assert variant.name == "Blue Dream", f"Variant name should match parent, got: {variant.name}"

    # Verify weight is stored separately in variant
    assert variant.weight == "3.5g", f"Variant should have weight field, got: {variant.weight}"
    assert variant.weight_grams == 3.5, f"Variant should have weight_grams, got: {variant.weight_grams}"

    # Verify parent has no weight fields
    assert parent.weight is None, "Parent should not have weight field"
    assert parent.weight_grams is None, "Parent should not have weight_grams field"


def test_scorer_extracts_weight_when_scraper_provides_it(db, test_brand):
    """
    Test that when scraper provides weight separately, it's used correctly.
    """
    scraped = ScrapedProduct(
        name="Gorilla Glue #4",  # No weight in name
        category="flower",
        brand="Test Brand",
        price=50.00,
        weight="7g",  # Scraper extracted weight
        thc_percentage=28.0,
        cbd_percentage=0.2,
        in_stock=True
    )

    variant_id, action = ConfidenceScorer.process_scraped_product(
        db=db,
        scraped_product=scraped,
        dispensary_id="test-disp-001",
        candidates=[]
    )

    db.commit()

    variant = db.query(Product).filter(Product.id == variant_id).first()
    parent = db.query(Product).filter(Product.id == variant.master_product_id).first()

    # Verify names
    assert parent.name == "Gorilla Glue #4"
    assert variant.name == "Gorilla Glue #4"

    # Verify weight from scraper is used
    assert variant.weight == "7g"
    assert variant.weight_grams == 7.0


def test_scorer_handles_fractional_weights(db, test_brand):
    """
    Test that fractional weights like "1/8 oz" are extracted and normalized.
    """
    scraped = ScrapedProduct(
        name="Wedding Cake 1/8 oz",  # Fractional weight in name
        category="flower",
        brand="Test Brand",
        price=40.00,
        weight=None,
        thc_percentage=25.0,
        cbd_percentage=0.1,
        in_stock=True
    )

    variant_id, action = ConfidenceScorer.process_scraped_product(
        db=db,
        scraped_product=scraped,
        dispensary_id="test-disp-001",
        candidates=[]
    )

    db.commit()

    variant = db.query(Product).filter(Product.id == variant_id).first()
    parent = db.query(Product).filter(Product.id == variant.master_product_id).first()

    # Verify clean name
    assert parent.name == "Wedding Cake"
    assert variant.name == "Wedding Cake"

    # Verify fractional weight is normalized to decimal grams
    assert variant.weight == "3.5g"  # Normalized to decimal grams
    assert variant.weight_grams == 3.5  # 1/8 oz = 3.5g


def test_scorer_auto_merge_uses_clean_names(db, test_brand):
    """
    Test that fuzzy matching uses clean names for better match quality.
    """
    # Create an existing parent product
    existing_parent = Product(
        name="Blue Dream",  # Clean name
        product_type="flower",
        brand_id=test_brand.id,
        thc_percentage=22.0,
        is_master=True,
        normalization_confidence=1.0
    )
    db.add(existing_parent)
    db.commit()

    # Create candidates cache
    candidates = [{
        "id": existing_parent.id,
        "name": existing_parent.name,
        "brand": test_brand.name,
        "thc_percentage": existing_parent.thc_percentage
    }]

    # Scrape a product with weight in name but same strain
    scraped = ScrapedProduct(
        name="Blue Dream 7g",  # Weight in name, should match existing
        category="flower",
        brand="Test Brand",
        price=60.00,
        weight=None,
        thc_percentage=22.5,  # Slightly different THC (within fuzzy match tolerance)
        cbd_percentage=0.1,
        in_stock=True
    )

    variant_id, action = ConfidenceScorer.process_scraped_product(
        db=db,
        scraped_product=scraped,
        dispensary_id="test-disp-001",
        candidates=candidates
    )

    db.commit()

    # Should auto-merge to existing product
    assert action == "auto_merge", f"Should auto-merge, got: {action}"

    variant = db.query(Product).filter(Product.id == variant_id).first()
    assert variant.master_product_id == existing_parent.id, "Should be variant of existing parent"
    assert variant.name == "Blue Dream", "Variant should inherit clean parent name"
    assert variant.weight == "7g", "Variant should have extracted weight"


def test_scorer_handles_name_without_weight(db, test_brand):
    """
    Test that products without weights in names work correctly.
    """
    scraped = ScrapedProduct(
        name="Super Lemon Haze",  # No weight anywhere
        category="flower",
        brand="Test Brand",
        price=55.00,
        weight=None,
        thc_percentage=24.0,
        cbd_percentage=0.1,
        in_stock=True
    )

    variant_id, action = ConfidenceScorer.process_scraped_product(
        db=db,
        scraped_product=scraped,
        dispensary_id="test-disp-001",
        candidates=[]
    )

    db.commit()

    variant = db.query(Product).filter(Product.id == variant_id).first()
    parent = db.query(Product).filter(Product.id == variant.master_product_id).first()

    # Name should remain unchanged
    assert parent.name == "Super Lemon Haze"
    assert variant.name == "Super Lemon Haze"

    # Weight fields should be None
    assert variant.weight is None
    assert variant.weight_grams is None


def test_scorer_prioritizes_scraper_weight_over_extracted(db, test_brand):
    """
    Test that if scraper provides weight, it takes priority over extracted weight.
    """
    scraped = ScrapedProduct(
        name="OG Kush 3.5g",  # Weight in name
        category="flower",
        brand="Test Brand",
        price=48.00,
        weight="7g",  # Scraper says 7g (different from name)
        thc_percentage=26.0,
        cbd_percentage=0.1,
        in_stock=True
    )

    variant_id, action = ConfidenceScorer.process_scraped_product(
        db=db,
        scraped_product=scraped,
        dispensary_id="test-disp-001",
        candidates=[]
    )

    db.commit()

    variant = db.query(Product).filter(Product.id == variant_id).first()
    parent = db.query(Product).filter(Product.id == variant.master_product_id).first()

    # Name should be clean
    assert parent.name == "OG Kush"
    assert variant.name == "OG Kush"

    # Scraper-provided weight should take priority
    assert variant.weight == "7g", "Should use scraper weight, not extracted"
    assert variant.weight_grams == 7.0

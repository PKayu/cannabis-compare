"""
Tests for the new data_cleanup flag processor methods:
  - clean_and_activate
  - delete_flagged_product

Run with: pytest backend/tests/test_flag_processor_cleanup.py -v
"""
import uuid
import pytest
from datetime import datetime

from models import ScraperFlag, Product, Brand, Dispensary
from services.normalization.flag_processor import ScraperFlagProcessor


def _make_dispensary(db, name="Test Dispensary"):
    """Create and persist a Dispensary."""
    d = Dispensary(id=str(uuid.uuid4()), name=name, location="UT")
    db.add(d)
    db.commit()
    return d


def _make_brand(db, name="TestBrand"):
    """Create and persist a Brand."""
    b = Brand(id=str(uuid.uuid4()), name=name)
    db.add(b)
    db.commit()
    return b


def _make_product(db, brand, name="Dirty Product", is_active=False, is_master=True):
    """Create and persist a Product."""
    p = Product(
        id=str(uuid.uuid4()),
        name=name,
        brand_id=brand.id,
        product_type="flower",
        is_active=is_active,
        is_master=is_master,
    )
    db.add(p)
    db.commit()
    return p


def _make_cleanup_flag(db, product, dispensary, brand_name="TestBrand", issue_tags=None):
    """Create and persist a data_cleanup ScraperFlag."""
    f = ScraperFlag(
        id=str(uuid.uuid4()),
        original_name=product.name,
        brand_name=brand_name,
        dispensary_id=dispensary.id,
        matched_product_id=product.id,
        confidence_score=0.0,
        flag_type="data_cleanup",
        status="pending",
        issue_tags=issue_tags or ["missing_price", "unknown_brand"],
    )
    db.add(f)
    db.commit()
    return f


def _make_legacy_flag(db, dispensary, brand_name="TestBrand"):
    """Create a legacy match_review flag (no linked product)."""
    f = ScraperFlag(
        id=str(uuid.uuid4()),
        original_name="Legacy Product",
        brand_name=brand_name,
        dispensary_id=dispensary.id,
        matched_product_id=None,
        confidence_score=0.75,
        flag_type="match_review",
        status="pending",
    )
    db.add(f)
    db.commit()
    return f


# ── clean_and_activate tests ────────────────────────────────────────────

class TestCleanAndActivate:

    def test_activates_product_and_resolves_flag(self, db_session):
        """Product should become active and flag should be 'cleaned'."""
        disp = _make_dispensary(db_session)
        brand = _make_brand(db_session)
        product = _make_product(db_session, brand, is_active=False)
        flag = _make_cleanup_flag(db_session, product, disp)

        admin_id = str(uuid.uuid4())
        result = ScraperFlagProcessor.clean_and_activate(
            db_session, flag.id, admin_id, notes="Fixed it"
        )

        # Refresh objects
        db_session.refresh(product)
        db_session.refresh(flag)

        assert product.is_active is True
        assert flag.status == "cleaned"
        assert flag.resolved_by == admin_id
        assert flag.resolved_at is not None
        assert result == product.id

    def test_applies_name_edit(self, db_session):
        """Name override should update the product."""
        disp = _make_dispensary(db_session)
        brand = _make_brand(db_session)
        product = _make_product(db_session, brand, name="Dirty N@me")
        flag = _make_cleanup_flag(db_session, product, disp)

        ScraperFlagProcessor.clean_and_activate(
            db_session, flag.id, str(uuid.uuid4()),
            name="Clean Name"
        )

        db_session.refresh(product)
        assert product.name == "Clean Name"

    def test_applies_brand_edit(self, db_session):
        """Brand override should find/create brand and update product."""
        disp = _make_dispensary(db_session)
        brand = _make_brand(db_session, name="OldBrand")
        product = _make_product(db_session, brand, is_active=False)
        flag = _make_cleanup_flag(db_session, product, disp)

        ScraperFlagProcessor.clean_and_activate(
            db_session, flag.id, str(uuid.uuid4()),
            brand_name="NewBrand"
        )

        db_session.refresh(product)
        new_brand = db_session.query(Brand).filter(Brand.name == "NewBrand").first()
        assert new_brand is not None
        assert product.brand_id == new_brand.id

    def test_tracks_corrections(self, db_session):
        """Corrections dict should record what changed."""
        disp = _make_dispensary(db_session)
        brand = _make_brand(db_session)
        product = _make_product(db_session, brand, name="Bad Name")
        flag = _make_cleanup_flag(db_session, product, disp)
        flag.original_name = "Bad Name"
        db_session.commit()

        ScraperFlagProcessor.clean_and_activate(
            db_session, flag.id, str(uuid.uuid4()),
            name="Good Name"
        )

        db_session.refresh(flag)
        assert flag.corrections is not None
        assert "name" in flag.corrections

    def test_rejects_non_pending_flag(self, db_session):
        """Already resolved flags should raise ValueError."""
        disp = _make_dispensary(db_session)
        brand = _make_brand(db_session)
        product = _make_product(db_session, brand)
        flag = _make_cleanup_flag(db_session, product, disp)
        flag.status = "cleaned"
        db_session.commit()

        with pytest.raises(ValueError, match="already resolved"):
            ScraperFlagProcessor.clean_and_activate(
                db_session, flag.id, str(uuid.uuid4())
            )

    def test_rejects_wrong_flag_type(self, db_session):
        """match_review flags should raise ValueError."""
        disp = _make_dispensary(db_session)
        flag = _make_legacy_flag(db_session, disp)

        with pytest.raises(ValueError, match="only for data_cleanup"):
            ScraperFlagProcessor.clean_and_activate(
                db_session, flag.id, str(uuid.uuid4())
            )

    def test_rejects_missing_product_link(self, db_session):
        """Flag with no matched_product_id should raise ValueError."""
        disp = _make_dispensary(db_session)
        brand = _make_brand(db_session)
        product = _make_product(db_session, brand)
        flag = _make_cleanup_flag(db_session, product, disp)
        flag.matched_product_id = None
        db_session.commit()

        with pytest.raises(ValueError, match="no linked product"):
            ScraperFlagProcessor.clean_and_activate(
                db_session, flag.id, str(uuid.uuid4())
            )


# ── delete_flagged_product tests ─────────────────────────────────────────

class TestDeleteFlaggedProduct:

    def test_deletes_product_and_dismisses_flag(self, db_session):
        """Product should be deleted and flag should be 'dismissed'."""
        disp = _make_dispensary(db_session)
        brand = _make_brand(db_session)
        product = _make_product(db_session, brand, is_active=False)
        product_id = product.id
        flag = _make_cleanup_flag(db_session, product, disp)

        admin_id = str(uuid.uuid4())
        ScraperFlagProcessor.delete_flagged_product(
            db_session, flag.id, admin_id, notes="Garbage"
        )

        db_session.refresh(flag)
        assert flag.status == "dismissed"
        assert flag.resolved_by == admin_id
        assert flag.matched_product_id is None  # Cleared

        # Product should be gone
        deleted = db_session.query(Product).filter(Product.id == product_id).first()
        assert deleted is None

    def test_deletes_variants_too(self, db_session):
        """Variants of the product should also be deleted."""
        disp = _make_dispensary(db_session)
        brand = _make_brand(db_session)
        parent = _make_product(db_session, brand, name="Parent", is_active=False)

        # Add a variant
        variant = Product(
            id=str(uuid.uuid4()),
            name="Parent",
            brand_id=brand.id,
            product_type="flower",
            is_active=False,
            is_master=False,
            master_product_id=parent.id,
            weight="3.5g",
            weight_grams=3.5,
        )
        db_session.add(variant)
        db_session.commit()
        variant_id = variant.id

        flag = _make_cleanup_flag(db_session, parent, disp)

        ScraperFlagProcessor.delete_flagged_product(
            db_session, flag.id, str(uuid.uuid4())
        )

        assert db_session.query(Product).filter(Product.id == parent.id).first() is None
        assert db_session.query(Product).filter(Product.id == variant_id).first() is None

    def test_rejects_non_pending_flag(self, db_session):
        disp = _make_dispensary(db_session)
        brand = _make_brand(db_session)
        product = _make_product(db_session, brand)
        flag = _make_cleanup_flag(db_session, product, disp)
        flag.status = "dismissed"
        db_session.commit()

        with pytest.raises(ValueError, match="already resolved"):
            ScraperFlagProcessor.delete_flagged_product(
                db_session, flag.id, str(uuid.uuid4())
            )

    def test_rejects_wrong_flag_type(self, db_session):
        disp = _make_dispensary(db_session)
        flag = _make_legacy_flag(db_session, disp)

        with pytest.raises(ValueError, match="only for data_cleanup"):
            ScraperFlagProcessor.delete_flagged_product(
                db_session, flag.id, str(uuid.uuid4())
            )

    def test_handles_missing_product_gracefully(self, db_session):
        """If the product was already deleted, just resolve the flag."""
        disp = _make_dispensary(db_session)
        brand = _make_brand(db_session)
        product = _make_product(db_session, brand, is_active=False)
        flag = _make_cleanup_flag(db_session, product, disp)

        # Delete the product manually before calling delete_flagged_product
        db_session.delete(product)
        db_session.commit()

        # Should not raise — just resolves the flag
        ScraperFlagProcessor.delete_flagged_product(
            db_session, flag.id, str(uuid.uuid4())
        )

        db_session.refresh(flag)
        assert flag.status == "dismissed"
        assert flag.matched_product_id is None

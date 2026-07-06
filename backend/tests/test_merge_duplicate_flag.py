"""
Regression tests for duplicate-product merging:
  - services.product_merge.merge_product_pair
  - ScraperFlagProcessor.merge_duplicate_flag (previously raised StopIteration
    because the flag only stored one product id)

Run with: pytest backend/tests/test_merge_duplicate_flag.py -v
"""
import uuid
import pytest

from models import ScraperFlag, Product, Brand, Dispensary, Price, Review, User, Watchlist
from services.product_merge import merge_product_pair
from services.normalization.flag_processor import ScraperFlagProcessor


def _brand(db, name="TestBrand"):
    b = Brand(id=str(uuid.uuid4()), name=name)
    db.add(b)
    db.commit()
    return b


def _dispensary(db, name):
    d = Dispensary(id=str(uuid.uuid4()), name=name, location="UT")
    db.add(d)
    db.commit()
    return d


def _master(db, brand, name):
    p = Product(
        id=str(uuid.uuid4()), name=name, brand_id=brand.id,
        product_type="flower", is_master=True, is_active=True,
    )
    db.add(p)
    db.commit()
    return p


def _variant(db, parent, weight_grams, weight=None):
    v = Product(
        id=str(uuid.uuid4()), name=parent.name, brand_id=parent.brand_id,
        product_type=parent.product_type, is_master=False, is_active=True,
        master_product_id=parent.id, weight_grams=weight_grams,
        weight=weight or (f"{weight_grams}g" if weight_grams else None),
    )
    db.add(v)
    db.commit()
    return v


def _price(db, product, dispensary, amount):
    pr = Price(product_id=product.id, dispensary_id=dispensary.id, amount=amount)
    db.add(pr)
    db.commit()
    return pr


def _pair_flag(db, product_a, product_b, dispensary=None, status="pending",
               flag_type="duplicate_pair", secondary=True):
    f = ScraperFlag(
        id=str(uuid.uuid4()),
        original_name=product_a.name,
        brand_name="TestBrand",
        dispensary_id=dispensary.id if dispensary else None,
        matched_product_id=product_a.id,
        secondary_product_id=product_b.id if secondary else None,
        confidence_score=0.75,
        flag_type=flag_type,
        status=status,
    )
    db.add(f)
    db.commit()
    return f


class TestMergeProductPair:
    def test_variants_reparented_and_loser_soft_deleted(self, db_session):
        brand = _brand(db_session)
        disp_a = _dispensary(db_session, "Disp A")
        winner = _master(db_session, brand, "Blue Dream")
        loser = _master(db_session, brand, "Blue Dream Flower")
        lv = _variant(db_session, loser, 7.0)
        _price(db_session, lv, disp_a, 40.0)

        result = merge_product_pair(db_session, winner.id, loser.id)
        db_session.commit()

        assert result["variants_reparented"] == 1
        assert lv.master_product_id == winner.id
        assert lv.is_active is True
        # Price stays on the re-parented variant
        assert db_session.query(Price).filter(Price.product_id == lv.id).count() == 1
        # Loser soft-deleted and pointed at winner
        assert loser.is_active is False
        assert loser.is_master is False
        assert loser.master_product_id == winner.id

    def test_weight_collision_moves_prices_and_merges_variant(self, db_session):
        brand = _brand(db_session)
        disp_a = _dispensary(db_session, "Disp A")
        disp_b = _dispensary(db_session, "Disp B")
        winner = _master(db_session, brand, "Blue Dream")
        loser = _master(db_session, brand, "Blue Dream Flower")
        wv = _variant(db_session, winner, 3.5)
        lv = _variant(db_session, loser, 3.5)
        _price(db_session, wv, disp_a, 35.0)   # winner already priced at A
        _price(db_session, lv, disp_a, 30.0)   # colliding price — dropped
        _price(db_session, lv, disp_b, 32.0)   # moves to winner variant

        result = merge_product_pair(db_session, winner.id, loser.id)
        db_session.commit()

        assert result["variants_merged"] == 1
        assert result["prices_moved"] == 1
        # Colliding loser variant soft-deleted
        assert lv.is_active is False
        # Winner variant now has both dispensaries, loser variant none
        wv_prices = db_session.query(Price).filter(Price.product_id == wv.id).all()
        assert {p.dispensary_id for p in wv_prices} == {disp_a.id, disp_b.id}
        assert db_session.query(Price).filter(Price.product_id == lv.id).count() == 0

    def test_close_weights_treated_as_collision(self, db_session):
        """3.5 vs 3.53 (rounding drift) merges instead of duplicating variants"""
        brand = _brand(db_session)
        winner = _master(db_session, brand, "Blue Dream")
        loser = _master(db_session, brand, "Blue Dream Flower")
        _variant(db_session, winner, 3.5)
        _variant(db_session, loser, 3.53)

        result = merge_product_pair(db_session, winner.id, loser.id)
        assert result["variants_merged"] == 1
        assert result["variants_reparented"] == 0

    def test_reviews_and_watchlist_moved(self, db_session):
        brand = _brand(db_session)
        winner = _master(db_session, brand, "Blue Dream")
        loser = _master(db_session, brand, "Blue Dream Flower")
        user = User(id=str(uuid.uuid4()), email="u@x.com", username="u1")
        db_session.add(user)
        db_session.commit()
        db_session.add(Review(user_id=user.id, product_id=loser.id, rating=5))
        db_session.add(Watchlist(user_id=user.id, product_id=loser.id))
        db_session.commit()

        result = merge_product_pair(db_session, winner.id, loser.id)
        db_session.commit()

        assert result["reviews_moved"] == 1
        assert result["watchlist_moved"] == 1
        assert db_session.query(Review).filter(Review.product_id == winner.id).count() == 1
        assert db_session.query(Watchlist).filter(Watchlist.product_id == winner.id).count() == 1

    def test_rejects_same_product(self, db_session):
        brand = _brand(db_session)
        p = _master(db_session, brand, "Blue Dream")
        with pytest.raises(ValueError):
            merge_product_pair(db_session, p.id, p.id)

    def test_rejects_missing_products(self, db_session):
        brand = _brand(db_session)
        p = _master(db_session, brand, "Blue Dream")
        with pytest.raises(ValueError):
            merge_product_pair(db_session, p.id, "nonexistent")
        with pytest.raises(ValueError):
            merge_product_pair(db_session, "nonexistent", p.id)


class TestMergeDuplicateFlag:
    def test_merge_keeping_matched_product(self, db_session):
        brand = _brand(db_session)
        disp = _dispensary(db_session, "Disp A")
        a = _master(db_session, brand, "Blue Dream")
        b = _master(db_session, brand, "Blue Dream Flower")
        bv = _variant(db_session, b, 7.0)
        _price(db_session, bv, disp, 40.0)
        flag = _pair_flag(db_session, a, b, disp)

        result = ScraperFlagProcessor.merge_duplicate_flag(
            db_session, flag.id, kept_product_id=a.id, admin_id="admin-1"
        )

        assert result["winner_id"] == a.id
        assert result["loser_id"] == b.id
        assert b.is_active is False
        assert bv.master_product_id == a.id
        assert flag.status == "merged"
        assert "duplicate_merged" in flag.issue_tags

    def test_merge_keeping_secondary_product(self, db_session):
        """Direction must work both ways — keeping product B merges A away"""
        brand = _brand(db_session)
        disp = _dispensary(db_session, "Disp A")
        a = _master(db_session, brand, "Blue Dream")
        b = _master(db_session, brand, "Blue Dream Flower")
        flag = _pair_flag(db_session, a, b, disp)

        result = ScraperFlagProcessor.merge_duplicate_flag(
            db_session, flag.id, kept_product_id=b.id, admin_id="admin-1"
        )

        assert result["winner_id"] == b.id
        assert result["loser_id"] == a.id
        assert a.is_active is False
        assert flag.status == "merged"

    def test_legacy_flag_without_secondary_raises_value_error(self, db_session):
        """Old flags lacking secondary_product_id fail loudly, not with StopIteration"""
        brand = _brand(db_session)
        disp = _dispensary(db_session, "Disp A")
        a = _master(db_session, brand, "Blue Dream")
        b = _master(db_session, brand, "Blue Dream Flower")
        flag = _pair_flag(db_session, a, b, disp, secondary=False)

        with pytest.raises(ValueError, match="does not reference two products"):
            ScraperFlagProcessor.merge_duplicate_flag(
                db_session, flag.id, kept_product_id=a.id, admin_id="admin-1"
            )

    def test_kept_product_must_be_in_pair(self, db_session):
        brand = _brand(db_session)
        disp = _dispensary(db_session, "Disp A")
        a = _master(db_session, brand, "Blue Dream")
        b = _master(db_session, brand, "Blue Dream Flower")
        c = _master(db_session, brand, "OG Kush")
        flag = _pair_flag(db_session, a, b, disp)

        with pytest.raises(ValueError, match="must be one of the flagged products"):
            ScraperFlagProcessor.merge_duplicate_flag(
                db_session, flag.id, kept_product_id=c.id, admin_id="admin-1"
            )

    def test_resolved_flag_rejected(self, db_session):
        brand = _brand(db_session)
        disp = _dispensary(db_session, "Disp A")
        a = _master(db_session, brand, "Blue Dream")
        b = _master(db_session, brand, "Blue Dream Flower")
        flag = _pair_flag(db_session, a, b, disp, status="merged")

        with pytest.raises(ValueError, match="already resolved"):
            ScraperFlagProcessor.merge_duplicate_flag(
                db_session, flag.id, kept_product_id=a.id, admin_id="admin-1"
            )

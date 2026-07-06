"""
Tests for near-miss (auto_missed) flag creation in ConfidenceScorer.

Covers:
- Same-dispensary near-misses now create flags, tagged same_dispensary_near_miss
- Cross-dispensary near-misses create untagged flags
- secondary_product_id records the newly created product (merge loser candidate)
- Re-runs don't duplicate flags

Run with: pytest backend/tests/test_scorer_flags.py -v
"""
import uuid
import pytest

from models import ScraperFlag, Product, Brand, Dispensary
from services.normalization.scorer import ConfidenceScorer
from services.scrapers.base_scraper import ScrapedProduct


# "Sour Diesel Premium Flower" vs "Sour Diesel" scores ~0.71 (review_flag band)
NEAR_MISS_NAME = "Sour Diesel Premium Flower"
CANDIDATE_NAME = "Sour Diesel"


def _dispensary(db, name):
    d = Dispensary(id=str(uuid.uuid4()), name=name, location="UT")
    db.add(d)
    db.commit()
    return d


def _existing_master(db, name=CANDIDATE_NAME):
    brand = Brand(id=str(uuid.uuid4()), name="Tryke")
    db.add(brand)
    db.commit()
    p = Product(
        id=str(uuid.uuid4()), name=name, brand_id=brand.id,
        product_type="flower", is_master=True, is_active=True,
    )
    db.add(p)
    db.commit()
    return p


def _candidates_for(master, dispensary_ids):
    return [{
        "id": master.id,
        "name": master.name,
        "brand": "Tryke",
        "product_type": "flower",
        "weight_grams_set": set(),
        "dispensary_ids": set(dispensary_ids),
    }]


def _scraped(name=NEAR_MISS_NAME):
    return ScrapedProduct(
        name=name, brand="Tryke", category="flower",
        price=40.0, weight="3.5g", thc_percentage=22.0,
    )


class TestNearMissFlags:
    def test_cross_dispensary_near_miss_flag(self, db_session):
        master = _existing_master(db_session)
        disp_other = _dispensary(db_session, "Other Disp")
        disp_scraping = _dispensary(db_session, "Scraping Disp")

        variant_id, action = ConfidenceScorer.process_scraped_product(
            db=db_session,
            scraped_product=_scraped(),
            dispensary_id=disp_scraping.id,
            candidates=_candidates_for(master, {disp_other.id}),
        )
        db_session.commit()

        assert action == "review_flag_created"
        flag = db_session.query(ScraperFlag).filter(
            ScraperFlag.status == "auto_missed"
        ).one()
        assert flag.matched_product_id == master.id
        # secondary_product_id records the newly created parent (merge loser)
        new_variant = db_session.query(Product).filter(Product.id == variant_id).one()
        assert flag.secondary_product_id == new_variant.master_product_id
        # Cross-dispensary: no same-dispensary tag
        assert not (flag.issue_tags or [])

    def test_same_dispensary_near_miss_now_flagged_and_tagged(self, db_session):
        """Previously invisible — same-dispensary near-misses must create a
        tagged flag so intra-store duplicates reach the admin queue."""
        master = _existing_master(db_session)
        disp = _dispensary(db_session, "Same Disp")

        _, action = ConfidenceScorer.process_scraped_product(
            db=db_session,
            scraped_product=_scraped(),
            dispensary_id=disp.id,
            candidates=_candidates_for(master, {disp.id}),
        )
        db_session.commit()

        assert action == "review_flag_created"
        flag = db_session.query(ScraperFlag).filter(
            ScraperFlag.status == "auto_missed"
        ).one()
        assert flag.issue_tags == ["same_dispensary_near_miss"]
        assert flag.secondary_product_id is not None

    def test_rerun_does_not_duplicate_flags(self, db_session):
        master = _existing_master(db_session)
        disp = _dispensary(db_session, "Scraping Disp")

        for _ in range(2):
            ConfidenceScorer.process_scraped_product(
                db=db_session,
                scraped_product=_scraped(),
                dispensary_id=disp.id,
                # Fresh candidate list each run, same master (simulates re-run)
                candidates=_candidates_for(master, set()),
            )
            db_session.commit()

        count = db_session.query(ScraperFlag).filter(
            ScraperFlag.status == "auto_missed",
            ScraperFlag.matched_product_id == master.id,
        ).count()
        assert count == 1

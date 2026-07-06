"""
Shared product-merge logic used by admin merge endpoints and flag resolution.

Merging keeps one master product (the "winner") and folds a duplicate master
(the "loser") into it: variants are re-parented (with weight-collision
handling), prices/reviews/watchlist entries are moved, and the loser is
soft-deleted. Prices always live on variants (parent/variant rules in
CLAUDE.md), so variant handling is the critical part.
"""
from sqlalchemy.orm import Session
from typing import Dict
import logging
import math

logger = logging.getLogger(__name__)

# Relative tolerance for treating two variant weights as the same
_WEIGHT_REL_TOL = 0.01


def merge_product_pair(db: Session, winner_id: str, loser_id: str) -> Dict:
    """
    Merge the loser master product into the winner.

    Does NOT commit — the caller owns the transaction (allows batch merges
    with per-pair savepoints).

    Steps:
    1. Re-parent the loser's variants to the winner. If the winner already
       has a variant with the same weight, move the loser variant's prices to
       the winner variant (dropping any that would collide on the
       product+dispensary unique constraint) and soft-delete the loser variant.
    2. Move prices attached directly to the loser parent (legacy safety net).
    3. Move reviews and watchlist entries (dropping watchlist duplicates).
    4. Soft-delete the loser: is_active=False, demoted to non-master, pointed
       at the winner for traceability.

    Returns:
        dict with winner_id, loser_id, variants_reparented, variants_merged,
        prices_moved, reviews_moved, watchlist_moved

    Raises:
        ValueError if products are missing, identical, or the winner
        is not an active master product.
    """
    from models import Product, Price, Review, Watchlist

    if winner_id == loser_id:
        raise ValueError("Winner and loser must be different products")

    winner = db.query(Product).filter(Product.id == winner_id).first()
    loser = db.query(Product).filter(Product.id == loser_id).first()
    if not winner:
        raise ValueError(f"Winner product not found: {winner_id}")
    if not loser:
        raise ValueError(f"Loser product not found: {loser_id}")
    if not winner.is_master:
        raise ValueError(f"Winner must be a master product: {winner_id}")

    winner_variants = (
        db.query(Product)
        .filter(
            Product.master_product_id == winner_id,
            Product.is_master.is_(False),
            Product.is_active.is_(True),
        )
        .all()
    )
    loser_variants = (
        db.query(Product)
        .filter(
            Product.master_product_id == loser_id,
            Product.is_master.is_(False),
            Product.is_active.is_(True),
        )
        .all()
    )

    def _same_weight(a, b) -> bool:
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        return math.isclose(a, b, rel_tol=_WEIGHT_REL_TOL)

    variants_reparented = 0
    variants_merged = 0
    prices_moved = 0

    for lv in loser_variants:
        collision = next(
            (wv for wv in winner_variants if _same_weight(wv.weight_grams, lv.weight_grams)),
            None,
        )
        if collision is None:
            lv.master_product_id = winner_id
            winner_variants.append(lv)
            variants_reparented += 1
            continue

        # Weight collision: move the loser variant's prices onto the winner's
        # variant, unless the winner variant already has a price at that
        # dispensary (unique product+dispensary constraint) — then drop the
        # loser's price and keep the winner's.
        existing_disp_ids = {
            p.dispensary_id
            for p in db.query(Price).filter(Price.product_id == collision.id).all()
        }
        for price in db.query(Price).filter(Price.product_id == lv.id).all():
            if price.dispensary_id in existing_disp_ids:
                db.delete(price)
            else:
                price.product_id = collision.id
                existing_disp_ids.add(price.dispensary_id)
                prices_moved += 1

        lv.is_active = False
        lv.master_product_id = winner_id
        variants_merged += 1

    # Legacy safety net: prices attached directly to the loser parent
    parent_price_disp_ids = {
        p.dispensary_id
        for p in db.query(Price).filter(Price.product_id == winner_id).all()
    }
    for price in db.query(Price).filter(Price.product_id == loser_id).all():
        if price.dispensary_id in parent_price_disp_ids:
            db.delete(price)
        else:
            price.product_id = winner_id
            parent_price_disp_ids.add(price.dispensary_id)
            prices_moved += 1

    # Reviews attach to master products — plain move
    reviews_moved = (
        db.query(Review)
        .filter(Review.product_id == loser_id)
        .update({Review.product_id: winner_id}, synchronize_session=False)
    )

    # Watchlist has a user+product unique constraint — drop rows that would collide
    watchlist_moved = 0
    winner_watch_users = {
        w.user_id
        for w in db.query(Watchlist).filter(Watchlist.product_id == winner_id).all()
    }
    for watch in db.query(Watchlist).filter(Watchlist.product_id == loser_id).all():
        if watch.user_id in winner_watch_users:
            db.delete(watch)
        else:
            watch.product_id = winner_id
            winner_watch_users.add(watch.user_id)
            watchlist_moved += 1

    # Soft-delete the loser, pointing at the winner for traceability
    loser.is_active = False
    loser.is_master = False
    loser.master_product_id = winner_id

    db.flush()

    logger.info(
        f"Merged product {loser_id} -> {winner_id} "
        f"(variants reparented={variants_reparented}, merged={variants_merged}, "
        f"prices moved={prices_moved}, reviews={reviews_moved}, watchlist={watchlist_moved})"
    )

    return {
        "winner_id": winner_id,
        "loser_id": loser_id,
        "variants_reparented": variants_reparented,
        "variants_merged": variants_merged,
        "prices_moved": prices_moved,
        "reviews_moved": reviews_moved,
        "watchlist_moved": watchlist_moved,
    }

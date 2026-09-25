"""Add scraper_flags.secondary_product_id, brands.normalized_name; relax dispensary_id

Revision ID: a7b8c9d0e1f2
Revises: 548777494dfe
Create Date: 2026-07-05 00:00:01.000000

- scraper_flags.secondary_product_id: second product reference.
  * match_review near-miss flags: the newly created product (merge "loser" candidate)
  * duplicate_pair flags: product B of the pair (matched_product_id = product A)
- brands.normalized_name: normalized brand name for dedup-safe lookups (backfilled)
- scraper_flags.dispensary_id becomes nullable (duplicate_pair flags span dispensaries)
- Backfills secondary_product_id on existing auto_missed flags from merge_reason text
"""
from typing import Sequence, Union
import re

from alembic import op
import sqlalchemy as sa


revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = '548777494dfe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_BRAND_SUFFIX_RE = re.compile(r"\b(inc|llc|co|corp|company|ltd)\b\.?", re.IGNORECASE)


def _normalize_brand_name(name: str) -> str:
    """Mirror of ProductMatcher.normalize_brand_name (kept inline so the
    migration stays self-contained if the app code moves)."""
    if not name:
        return ""
    s = name.lower().strip()
    s = _BRAND_SUFFIX_RE.sub("", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    try:
        from services.normalization.brand_aliases import BRAND_ALIASES
        return BRAND_ALIASES.get(s, s)
    except ImportError:
        return s


def upgrade() -> None:
    with op.batch_alter_table('scraper_flags') as batch_op:
        batch_op.add_column(sa.Column('secondary_product_id', sa.String(), nullable=True))
        batch_op.create_foreign_key(
            'fk_scraper_flags_secondary_product_id',
            'products', ['secondary_product_id'], ['id']
        )
        batch_op.create_index('ix_scraper_flags_secondary_product_id', ['secondary_product_id'])
        batch_op.alter_column('dispensary_id', existing_type=sa.String(), nullable=True)

    with op.batch_alter_table('brands') as batch_op:
        batch_op.add_column(sa.Column('normalized_name', sa.String(), nullable=True))
        batch_op.create_index('ix_brands_normalized_name', ['normalized_name'])

    conn = op.get_bind()

    # Backfill brands.normalized_name
    for brand_id, name in conn.execute(sa.text("SELECT id, name FROM brands")):
        conn.execute(
            sa.text("UPDATE brands SET normalized_name = :norm WHERE id = :id"),
            {"norm": _normalize_brand_name(name), "id": brand_id},
        )

    # Backfill secondary_product_id on auto_missed flags from merge_reason text
    # ("... New product id: <uuid>") — only where that product still exists.
    rows = conn.execute(sa.text(
        "SELECT id, merge_reason FROM scraper_flags "
        "WHERE status = 'auto_missed' AND merge_reason IS NOT NULL"
    )).fetchall()
    id_re = re.compile(r"New product id: ([0-9a-fA-F-]{36})")
    for flag_id, merge_reason in rows:
        m = id_re.search(merge_reason or "")
        if not m:
            continue
        product_id = m.group(1)
        exists = conn.execute(
            sa.text("SELECT 1 FROM products WHERE id = :pid"),
            {"pid": product_id},
        ).first()
        if exists:
            conn.execute(
                sa.text("UPDATE scraper_flags SET secondary_product_id = :pid WHERE id = :fid"),
                {"pid": product_id, "fid": flag_id},
            )


def downgrade() -> None:
    with op.batch_alter_table('brands') as batch_op:
        batch_op.drop_index('ix_brands_normalized_name')
        batch_op.drop_column('normalized_name')

    with op.batch_alter_table('scraper_flags') as batch_op:
        batch_op.alter_column('dispensary_id', existing_type=sa.String(), nullable=False)
        batch_op.drop_index('ix_scraper_flags_secondary_product_id')
        batch_op.drop_constraint('fk_scraper_flags_secondary_product_id', type_='foreignkey')
        batch_op.drop_column('secondary_product_id')

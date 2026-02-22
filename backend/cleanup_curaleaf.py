"""One-time script to clear Curaleaf scrape data for a fresh re-run."""
from database import SessionLocal
from models import Product, Price, ScraperFlag, Dispensary

db = SessionLocal()

# Count before
flags_before = db.query(ScraperFlag).filter(ScraperFlag.status == 'pending').count()
products_before = db.query(Product).count()
prices_before = db.query(Price).count()
print(f"Before: {flags_before} pending flags, {products_before} products, {prices_before} prices")

# 1. Delete all pending data_cleanup flags
db.query(ScraperFlag).filter(
    ScraperFlag.status == 'pending',
    ScraperFlag.flag_type == 'data_cleanup'
).delete(synchronize_session='fetch')
db.flush()

# 2. Find Curaleaf dispensary IDs
curaleaf_disps = db.query(Dispensary).filter(Dispensary.name.ilike('%curaleaf%')).all()
curaleaf_ids = [d.id for d in curaleaf_disps]
print(f"Curaleaf dispensary IDs: {curaleaf_ids}")

# 3. Delete all Curaleaf prices
deleted_prices = db.query(Price).filter(
    Price.dispensary_id.in_(curaleaf_ids)
).delete(synchronize_session='fetch')
db.flush()
print(f"Deleted {deleted_prices} Curaleaf prices")

# 4. Delete variants that now have no prices anywhere
from sqlalchemy import exists
orphan_variants = db.query(Product).filter(
    Product.is_master.is_(False),
    ~exists().where(Price.product_id == Product.id)
).all()
orphan_variant_ids = [v.id for v in orphan_variants]
print(f"Orphaned variants to delete: {len(orphan_variant_ids)}")
db.query(Product).filter(Product.id.in_(orphan_variant_ids)).delete(synchronize_session='fetch')
db.flush()

# 5. Delete master products that now have no variants
orphan_masters = db.query(Product).filter(
    Product.is_master.is_(True),
    ~exists().where(Product.master_product_id == Product.id)
).all()
print(f"Orphaned masters to delete: {len(orphan_masters)}")
for m in orphan_masters:
    db.delete(m)
db.flush()

db.commit()

flags_after = db.query(ScraperFlag).filter(ScraperFlag.status == 'pending').count()
products_after = db.query(Product).count()
prices_after = db.query(Price).count()
print(f"After:  {flags_after} pending flags, {products_after} products, {prices_after} prices")
db.close()
print("Done.")

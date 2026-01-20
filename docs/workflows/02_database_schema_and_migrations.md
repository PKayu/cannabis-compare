---
description: Implement database schema with Alembic migrations, adding ScraperFlags and Promotions tables for normalization and daily deals support.
auto_execution_mode: 1
---

## Context

This workflow implements the foundational database layer for the Utah Cannabis Aggregator as defined in PRD sections 6.2 and 4.2:
- 6 core tables: Products, Dispensaries, Prices, Reviews, Promotions, ScraperFlags
- Confidence-based normalization system (>90%, 60-90%, <60%)
- Support for recurring deals and promotions
- Performance optimization through proper indexing

## Steps

### 1. Review Current Schema

Read the following to understand current state:
- `backend/models.py` - Current SQLAlchemy models (User, Product, Brand, Dispensary, Price, Review)
- `backend/prisma/schema.prisma` - Schema reference
- `docs/prd.md` - Section 6.2 (High-Level Data Model) and 4.2 (Daily Deals & Promotions)

### 2. Install and Configure Alembic

```bash
cd backend
pip install alembic
alembic init alembic
```

Update `backend/alembic/env.py`:
```python
from backend.database import Base
from backend.models import User, Product, Brand, Dispensary, Price, Review

target_metadata = Base.metadata

# Add all models
sqlalchemy_url = config.get_main_option("sqlalchemy.url")
```

Update `backend/alembic.ini`:
```
sqlalchemy.url = driver://user:password@localhost/dbname
# Will be overridden by .env DATABASE_URL at runtime
```

### 3. Create ScraperFlags Table Model

Add to `backend/models.py`:

```python
class ScraperFlag(Base):
    """Flags for products with low confidence matches requiring manual review"""
    __tablename__ = "scraper_flags"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Original scraped data
    original_name = Column(String, nullable=False)  # As scraped from dispensary
    original_thc = Column(Float, nullable=True)
    original_cbd = Column(Float, nullable=True)
    brand_name = Column(String, nullable=False)
    dispensary_id = Column(String, ForeignKey("dispensaries.id"), nullable=False)

    # Potential match
    matched_product_id = Column(String, ForeignKey("products.id"), nullable=True)
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0

    # Status
    status = Column(String, default="pending")  # pending, approved, rejected, merged
    merge_reason = Column(String, nullable=True)  # Why flagged

    # Admin action
    admin_notes = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)  # Future: admin_id

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dispensary = relationship("Dispensary", back_populates="scraper_flags")
    matched_product = relationship("Product", foreign_keys=[matched_product_id])

    def __repr__(self):
        return f"<ScraperFlag {self.original_name} @ {self.dispensary_id}>"
```

Update Dispensary model to include:
```python
scraper_flags = relationship("ScraperFlag", back_populates="dispensary", cascade="all, delete-orphan")
```

### 4. Create Promotions Table Model

Add to `backend/models.py`:

```python
class Promotion(Base):
    """Stores recurring and one-time promotional offers"""
    __tablename__ = "promotions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Promotion details
    title = Column(String, nullable=False)  # e.g. "Medical Monday 15% off"
    description = Column(String, nullable=True)
    discount_percentage = Column(Float, nullable=True)  # 0-100
    discount_amount = Column(Float, nullable=True)  # Fixed $ amount

    # Scope
    dispensary_id = Column(String, ForeignKey("dispensaries.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)  # NULL = applies to category
    applies_to_category = Column(String, nullable=True)  # "Flower", "Vape", "Edible", etc.

    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(String, nullable=True)  # "daily", "weekly", "monthly"
    recurring_day = Column(String, nullable=True)  # "monday", "friday", etc.

    # Dates
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)  # NULL = no end date

    # Status
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dispensary = relationship("Dispensary")
    product = relationship("Product")

    def __repr__(self):
        return f"<Promotion {self.title} @ {self.dispensary_id}>"
```

### 5. Update Products Table with Normalization Fields

Update Product model in `backend/models.py`:

```python
class Product(Base):
    # ... existing fields ...

    # Normalization tracking
    master_product_id = Column(String, ForeignKey("products.id"), nullable=True)  # Links duplicates to master
    normalization_confidence = Column(Float, default=1.0)  # 0.0-1.0 confidence score
    is_master = Column(Boolean, default=True)  # True if this is canonical entry

    # Add this to existing relationships:
    master_product = relationship("Product", remote_side=[id], foreign_keys=[master_product_id])
    duplicate_products = relationship("Product", backref="duplicated_from", remote_side=[master_product_id])
```

### 6. Create Database Indexes for Performance

Create `backend/alembic/versions/001_initial_schema.py`:

```python
"""Initial schema with indexes"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Create indexes on frequently searched columns
    op.create_index('ix_products_name', 'products', ['name'])
    op.create_index('ix_products_brand_id', 'products', ['brand_id'])
    op.create_index('ix_prices_product_id', 'prices', ['product_id'])
    op.create_index('ix_prices_dispensary_id', 'prices', ['dispensary_id'])
    op.create_index('ix_reviews_product_id', 'reviews', ['product_id'])
    op.create_index('ix_reviews_user_id', 'reviews', ['user_id'])
    op.create_index('ix_scraper_flags_status', 'scraper_flags', ['status'])
    op.create_index('ix_promotions_dispensary_id', 'promotions', ['dispensary_id'])

def downgrade():
    op.drop_index('ix_promotions_dispensary_id')
    op.drop_index('ix_scraper_flags_status')
    op.drop_index('ix_reviews_user_id')
    op.drop_index('ix_reviews_product_id')
    op.drop_index('ix_prices_dispensary_id')
    op.drop_index('ix_prices_product_id')
    op.drop_index('ix_products_brand_id')
    op.drop_index('ix_products_name')
```

### 7. Generate Migration from Models

```bash
cd backend
alembic revision --autogenerate -m "Add ScraperFlags and Promotions tables"
# Review generated migration file in alembic/versions/
```

### 8. Apply Migration to Database

```bash
cd backend
alembic upgrade head
# Should create all tables with proper relationships
```

Verify with database client:
```sql
\dt  -- List all tables
SELECT * FROM information_schema.tables WHERE table_schema='public';
```

### 9. Update Prisma Schema Reference

Update `backend/prisma/schema.prisma` to include new tables:

```prisma
model ScraperFlag {
  id                  String      @id @default(uuid())
  originalName        String
  originalThc         Float?
  originalCbd         Float?
  brandName           String
  dispensaryId        String
  matchedProductId    String?
  confidenceScore     Float
  status              String      @default("pending")
  mergeReason         String?
  adminNotes          String?
  resolvedAt          DateTime?
  resolvedBy          String?
  createdAt           DateTime    @default(now())
  updatedAt           DateTime    @updatedAt

  dispensary          Dispensary  @relation(fields: [dispensaryId], references: [id])
  matchedProduct      Product?    @relation(fields: [matchedProductId], references: [id])
}

model Promotion {
  id                  String      @id @default(uuid())
  title               String
  description         String?
  discountPercentage  Float?
  discountAmount      Float?
  dispensaryId        String
  productId           String?
  appliesToCategory   String?
  isRecurring         Boolean     @default(false)
  recurringPattern    String?
  recurringDay        String?
  startDate           DateTime
  endDate             DateTime?
  isActive            Boolean     @default(true)
  createdAt           DateTime    @default(now())
  updatedAt           DateTime    @updatedAt

  dispensary          Dispensary  @relation(fields: [dispensaryId], references: [id])
  product             Product?    @relation(fields: [productId], references: [id])
}
```

### 10. Document Rollback Procedure

Create `docs/database_rollback.md`:

```markdown
# Database Rollback Guide

## Rollback to Previous Migration

```bash
cd backend
alembic downgrade -1  # Rollback one migration
alembic downgrade base  # Rollback to initial schema
```

## Recreate Database from Scratch

```bash
# Drop all tables
psql -U postgres -d cannabis_aggregator -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Apply all migrations
cd backend
alembic upgrade head
```

## Backup Before Migration

```bash
pg_dump -U postgres cannabis_aggregator > backup_$(date +%Y%m%d_%H%M%S).sql
```
```

## Success Criteria

- [ ] Alembic initialized and configured
- [ ] ScraperFlags table created with proper fields
- [ ] Promotions table created with recurrence support
- [ ] Products table updated with normalization fields
- [ ] All indexes created for query performance
- [ ] Migration applied successfully to database
- [ ] Prisma schema updated
- [ ] Rollback procedures documented
- [ ] Database schema verified with \dt or equivalent
- [ ] No migration errors in logs

## Notes

- Do NOT modify the migrations after applying them to production
- Always test migrations on a copy of production data first
- Keep migration files for audit trail
- Alembic tracks migration history automatically

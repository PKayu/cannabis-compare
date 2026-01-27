"""
Seed script to populate test data for API testing.
Run with: python seed_test_data.py
"""
import sys
sys.path.insert(0, '.')

from database import SessionLocal, engine
from models import Base, User, Dispensary, Brand, Product, Price, Review, ScraperFlag, Promotion
from datetime import datetime, timedelta
import uuid

def seed_data():
    """Populate database with test data"""
    db = SessionLocal()

    try:
        # Check if data already exists
        existing_dispensaries = db.query(Dispensary).count()
        if existing_dispensaries > 0:
            print(f"Database already has {existing_dispensaries} dispensaries. Skipping seed.")
            print("To reseed, delete existing data first.")
            return

        print("Seeding test data...")

        # === Create Dispensaries ===
        dispensaries = [
            Dispensary(
                id="disp-001",
                name="WholesomeCo",
                website="https://wholesomeco.com",
                location="123 Main St, Salt Lake City, UT",
                hours="Mon-Sat 9am-9pm, Sun 10am-6pm",
                phone="(801) 555-0101",
                latitude=40.7608,
                longitude=-111.8910
            ),
            Dispensary(
                id="disp-002",
                name="Dragonfly Wellness",
                website="https://dragonflywellness.com",
                location="456 State St, Salt Lake City, UT",
                hours="Mon-Sun 10am-8pm",
                phone="(801) 555-0202",
                latitude=40.7589,
                longitude=-111.8912
            ),
            Dispensary(
                id="disp-003",
                name="Beehive Farmacy",
                website="https://beehivefarmacy.com",
                location="789 Temple St, Salt Lake City, UT",
                hours="Mon-Fri 9am-7pm, Sat 10am-5pm",
                phone="(801) 555-0303",
                latitude=40.7614,
                longitude=-111.8880
            )
        ]
        for d in dispensaries:
            db.add(d)
        print(f"  Created {len(dispensaries)} dispensaries")

        # === Create Brands ===
        brands = [
            Brand(id="brand-001", name="Tryke"),
            Brand(id="brand-002", name="Zion Cultivar"),
            Brand(id="brand-003", name="Standard Wellness"),
            Brand(id="brand-004", name="Curaleaf"),
        ]
        for b in brands:
            db.add(b)
        print(f"  Created {len(brands)} brands")

        # === Create Products ===
        products = [
            Product(
                id="prod-001",
                name="Blue Dream",
                product_type="flower",
                thc_percentage=22.5,
                cbd_percentage=0.1,
                brand_id="brand-001",
                is_master=True,
                normalization_confidence=1.0
            ),
            Product(
                id="prod-002",
                name="Gorilla Glue #4",
                product_type="flower",
                thc_percentage=28.0,
                cbd_percentage=0.2,
                brand_id="brand-002",
                is_master=True,
                normalization_confidence=1.0
            ),
            Product(
                id="prod-003",
                name="Wedding Cake",
                product_type="flower",
                thc_percentage=25.0,
                cbd_percentage=0.3,
                brand_id="brand-001",
                is_master=True,
                normalization_confidence=1.0
            ),
            Product(
                id="prod-004",
                name="OG Kush Vape Cart",
                product_type="vaporizer",
                thc_percentage=85.0,
                cbd_percentage=0.5,
                brand_id="brand-003",
                is_master=True,
                normalization_confidence=1.0
            ),
            Product(
                id="prod-005",
                name="CBD Relief Tincture",
                product_type="tincture",
                thc_percentage=5.0,
                cbd_percentage=20.0,
                brand_id="brand-004",
                is_master=True,
                normalization_confidence=1.0
            ),
            # A duplicate product (non-master) for testing merge
            Product(
                id="prod-006",
                name="Blue Dream (Alternate)",
                product_type="flower",
                thc_percentage=21.0,
                cbd_percentage=0.1,
                brand_id="brand-001",
                is_master=False,
                master_product_id="prod-001",
                normalization_confidence=0.85
            ),
        ]
        for p in products:
            db.add(p)
        print(f"  Created {len(products)} products")

        # === Create Prices (with intentional outliers for testing) ===
        prices = [
            # Blue Dream at all 3 dispensaries (with one outlier)
            Price(id="price-001", product_id="prod-001", dispensary_id="disp-001", amount=45.00, in_stock=True),
            Price(id="price-002", product_id="prod-001", dispensary_id="disp-002", amount=48.00, in_stock=True),
            Price(id="price-003", product_id="prod-001", dispensary_id="disp-003", amount=120.00, in_stock=True),  # OUTLIER

            # Gorilla Glue at 2 dispensaries
            Price(id="price-004", product_id="prod-002", dispensary_id="disp-001", amount=55.00, in_stock=True),
            Price(id="price-005", product_id="prod-002", dispensary_id="disp-002", amount=52.00, in_stock=False),

            # Wedding Cake with historical price change
            Price(
                id="price-006",
                product_id="prod-003",
                dispensary_id="disp-001",
                amount=50.00,
                in_stock=True,
                previous_price=55.00,
                price_change_percentage=-9.09,
                price_change_date=datetime.utcnow() - timedelta(days=2)
            ),
            Price(id="price-007", product_id="prod-003", dispensary_id="disp-003", amount=52.00, in_stock=True),

            # OG Kush Vape at all dispensaries (with outlier)
            Price(id="price-008", product_id="prod-004", dispensary_id="disp-001", amount=35.00, in_stock=True),
            Price(id="price-009", product_id="prod-004", dispensary_id="disp-002", amount=38.00, in_stock=True),
            Price(id="price-010", product_id="prod-004", dispensary_id="disp-003", amount=5.00, in_stock=True),  # OUTLIER (too cheap)

            # CBD Tincture
            Price(id="price-011", product_id="prod-005", dispensary_id="disp-001", amount=65.00, in_stock=True),
            Price(id="price-012", product_id="prod-005", dispensary_id="disp-002", amount=62.00, in_stock=True),
            Price(id="price-013", product_id="prod-005", dispensary_id="disp-003", amount=68.00, in_stock=False),
        ]
        for p in prices:
            db.add(p)
        print(f"  Created {len(prices)} prices")

        # === Create Users ===
        users = [
            User(id="user-001", email="testuser@example.com", username="testuser"),
            User(id="user-002", email="reviewer@example.com", username="reviewer"),
        ]
        for u in users:
            db.add(u)
        print(f"  Created {len(users)} users")

        # === Create Reviews ===
        reviews = [
            Review(
                id="review-001",
                user_id="user-001",
                product_id="prod-001",
                rating=5,
                effects_rating=5,
                taste_rating=4,
                value_rating=4,
                comment="Great strain for relaxation! Smooth smoke.",
                upvotes=12
            ),
            Review(
                id="review-002",
                user_id="user-002",
                product_id="prod-001",
                rating=4,
                effects_rating=4,
                taste_rating=5,
                value_rating=3,
                comment="Love the taste, but a bit pricey.",
                upvotes=5
            ),
            Review(
                id="review-003",
                user_id="user-001",
                product_id="prod-002",
                rating=5,
                effects_rating=5,
                taste_rating=4,
                value_rating=5,
                comment="Potent! Great value for the THC content.",
                upvotes=20
            ),
        ]
        for r in reviews:
            db.add(r)
        print(f"  Created {len(reviews)} reviews")

        # === Create ScraperFlags (for admin queue testing) ===
        flags = [
            ScraperFlag(
                id="flag-001",
                original_name="Blu Dream",  # Misspelling
                original_thc=21.5,
                original_cbd=0.1,
                brand_name="Tryke",
                dispensary_id="disp-002",
                matched_product_id="prod-001",
                confidence_score=0.75,
                status="pending",
                merge_reason="Fuzzy match - possible misspelling"
            ),
            ScraperFlag(
                id="flag-002",
                original_name="GG4",  # Abbreviation
                original_thc=27.0,
                original_cbd=0.2,
                brand_name="Zion Cultivar",
                dispensary_id="disp-001",
                matched_product_id="prod-002",
                confidence_score=0.68,
                status="pending",
                merge_reason="Abbreviation detected - GG4 vs Gorilla Glue #4"
            ),
            ScraperFlag(
                id="flag-003",
                original_name="Wedding Kake",  # Misspelling
                original_thc=24.0,
                original_cbd=0.3,
                brand_name="Tryke",
                dispensary_id="disp-003",
                matched_product_id="prod-003",
                confidence_score=0.82,
                status="pending",
                merge_reason="Fuzzy match - possible misspelling"
            ),
            ScraperFlag(
                id="flag-004",
                original_name="Unknown Strain XYZ",
                original_thc=19.0,
                original_cbd=0.5,
                brand_name="New Brand",
                dispensary_id="disp-001",
                matched_product_id=None,
                confidence_score=0.25,
                status="pending",
                merge_reason="No match found - may be new product"
            ),
            # One already approved flag
            ScraperFlag(
                id="flag-005",
                original_name="Blue Dreem",
                original_thc=22.0,
                original_cbd=0.1,
                brand_name="Tryke",
                dispensary_id="disp-001",
                matched_product_id="prod-001",
                confidence_score=0.88,
                status="approved",
                merge_reason="Misspelling",
                admin_notes="Confirmed as Blue Dream variant",
                resolved_at=datetime.utcnow() - timedelta(days=1),
                resolved_by="admin-user-id"
            ),
        ]
        for f in flags:
            db.add(f)
        print(f"  Created {len(flags)} scraper flags")

        # === Create Promotions ===
        promotions = [
            Promotion(
                id="promo-001",
                title="Medical Monday - 15% Off",
                description="Show your medical card for 15% off all flower products",
                discount_percentage=15.0,
                dispensary_id="disp-001",
                applies_to_category="flower",
                is_recurring=True,
                recurring_pattern="weekly",
                recurring_day="monday",
                start_date=datetime.utcnow() - timedelta(days=30),
                is_active=True
            ),
            Promotion(
                id="promo-002",
                title="New Patient Special",
                description="First-time patients get $10 off any purchase over $50",
                discount_amount=10.0,
                dispensary_id="disp-002",
                is_recurring=False,
                start_date=datetime.utcnow() - timedelta(days=7),
                end_date=datetime.utcnow() + timedelta(days=23),
                is_active=True
            ),
            Promotion(
                id="promo-003",
                title="Vape Friday",
                description="20% off all vape cartridges every Friday",
                discount_percentage=20.0,
                dispensary_id="disp-003",
                applies_to_category="vaporizer",
                is_recurring=True,
                recurring_pattern="weekly",
                recurring_day="friday",
                start_date=datetime.utcnow() - timedelta(days=60),
                is_active=True
            ),
        ]
        for p in promotions:
            db.add(p)
        print(f"  Created {len(promotions)} promotions")

        # Commit all changes
        db.commit()
        print("\n✓ Test data seeded successfully!")

        # Print summary
        print("\n=== Test Data Summary ===")
        print(f"  Dispensaries: {len(dispensaries)}")
        print(f"  Brands: {len(brands)}")
        print(f"  Products: {len(products)} (1 duplicate for merge testing)")
        print(f"  Prices: {len(prices)} (2 intentional outliers)")
        print(f"  Users: {len(users)}")
        print(f"  Reviews: {len(reviews)}")
        print(f"  ScraperFlags: {len(flags)} ({sum(1 for f in flags if f.status == 'pending')} pending)")
        print(f"  Promotions: {len(promotions)}")

        print("\n=== Key Test IDs ===")
        print("  Flag IDs (pending): flag-001, flag-002, flag-003, flag-004")
        print("  Flag ID (approved): flag-005")
        print("  Product IDs: prod-001 through prod-006")
        print("  Dispensary IDs: disp-001, disp-002, disp-003")
        print("  Outlier Prices: price-003 ($120 vs ~$46 avg), price-010 ($5 vs ~$36 avg)")

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        raise
    finally:
        db.close()


def clear_data():
    """Clear all test data (use with caution!)"""
    db = SessionLocal()
    try:
        # Delete in order of dependencies
        db.query(Review).delete()
        db.query(Promotion).delete()
        db.query(ScraperFlag).delete()
        db.query(Price).delete()
        db.query(Product).delete()
        db.query(Brand).delete()
        db.query(Dispensary).delete()
        db.query(User).delete()
        db.commit()
        print("All test data cleared.")
    except Exception as e:
        db.rollback()
        print(f"Error clearing data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed or clear test data")
    parser.add_argument("--clear", action="store_true", help="Clear all data instead of seeding")
    args = parser.parse_args()

    if args.clear:
        confirm = input("Are you sure you want to delete ALL data? (yes/no): ")
        if confirm.lower() == "yes":
            clear_data()
    else:
        seed_data()

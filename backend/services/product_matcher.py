from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Product, Brand
from services.scrapers.base_scraper import ScrapedProduct
import logging

logger = logging.getLogger(__name__)

class ProductMatcher:
    """
    Service to match scraped products with existing database entries.
    Handles deduplication and new product creation.
    """
    def __init__(self, db: Session):
        self.db = db

    def match_or_create(self, scraped: ScrapedProduct) -> Product:
        """
        Find existing product or create a new one.
        """
        # 1. Find or Create Brand
        brand = self._get_or_create_brand(scraped.brand)

        # 2. Try to find existing product (Exact Match)
        # We match on Name + Brand for now.
        # TODO: Add fuzzy matching for slight name variations
        product = self.db.query(Product).filter(
            func.lower(Product.name) == scraped.name.lower(),
            Product.brand_id == brand.id
        ).first()

        if product:
            return product

        # 3. Create new product if not found
        logger.info(f"Creating new product: {scraped.name} ({brand.name})")
        new_product = Product(
            name=scraped.name,
            brand_id=brand.id,
            product_type=scraped.category, # Maps to 'product_type' in DB
            thc_percentage=scraped.thc_percentage,
            cbd_percentage=scraped.cbd_percentage,
            normalization_confidence=1.0 # Auto-created
        )
        self.db.add(new_product)
        self.db.flush() # Get ID without committing transaction
        return new_product

    def _get_or_create_brand(self, brand_name: str) -> Brand:
        """Get existing brand or create new one"""
        if not brand_name:
            brand_name = "Unknown Brand"
            
        brand = self.db.query(Brand).filter(
            func.lower(Brand.name) == brand_name.lower()
        ).first()

        if not brand:
            brand = Brand(name=brand_name)
            self.db.add(brand)
            self.db.flush()
            
        return brand
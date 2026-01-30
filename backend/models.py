"""
SQLAlchemy models for database tables
Based on the Prisma schema from the PRD v1.2

Tables:
- User: User accounts for authentication
- Dispensary: Utah pharmacy details
- Brand: Cannabis cultivators/brands
- Product: Master product entries (strains, vapes, etc.)
- Price: Junction table linking products to dispensaries with pricing
- Review: User reviews with intention tags
- ScraperFlag: Products requiring manual normalization review
- Promotion: Recurring and one-time promotional offers
- ScraperRun: Log of every scraper execution for monitoring
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import uuid

class User(Base):
    """User model for authentication and review tracking"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class Dispensary(Base):
    """Dispensary (pharmacy) model"""
    __tablename__ = "dispensaries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    website = Column(String, nullable=True)
    location = Column(String, nullable=True)
    hours = Column(String, nullable=True)  # Operating hours
    phone = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)  # For map integration
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prices = relationship("Price", back_populates="dispensary", cascade="all, delete-orphan")
    scraper_flags = relationship("ScraperFlag", back_populates="dispensary", cascade="all, delete-orphan")
    promotions = relationship("Promotion", back_populates="dispensary", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Dispensary {self.name}>"


class Brand(Base):
    """Brand (cultivator) model"""
    __tablename__ = "brands"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    products = relationship("Product", back_populates="brand", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Brand {self.name}>"


class Product(Base):
    """Product model for strains and cannabis products (Master Product entries)"""
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)  # e.g., "Gorilla Glue #4"
    product_type = Column(String, nullable=False)  # e.g., "Flower", "Vape", "Edible"
    thc_percentage = Column(Float, nullable=True)  # THC content
    cbd_percentage = Column(Float, nullable=True)  # CBD content
    brand_id = Column(String, ForeignKey("brands.id"), nullable=False)

    # Normalization tracking (PRD section 4.1)
    master_product_id = Column(String, ForeignKey("products.id"), nullable=True)  # Links duplicates to master
    normalization_confidence = Column(Float, default=1.0)  # 0.0-1.0 confidence score
    is_master = Column(Boolean, default=True)  # True if this is canonical entry

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    brand = relationship("Brand", back_populates="products")
    prices = relationship("Price", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    promotions = relationship("Promotion", back_populates="product")

    # Self-referential relationship for product normalization
    master_product = relationship("Product", remote_side=[id], foreign_keys=[master_product_id], backref="duplicate_products")

    def __repr__(self):
        return f"<Product {self.name}>"


class Price(Base):
    """Price model linking products to dispensaries with pricing"""
    __tablename__ = "prices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    amount = Column(Float, nullable=False)  # Current price in USD
    in_stock = Column(Boolean, default=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    dispensary_id = Column(String, ForeignKey("dispensaries.id"), nullable=False)

    # Price history tracking
    previous_price = Column(Float, nullable=True)
    price_change_date = Column(DateTime, nullable=True)
    price_change_percentage = Column(Float, nullable=True)  # % change since last update

    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint: one price per product per dispensary
    __table_args__ = (UniqueConstraint('product_id', 'dispensary_id', name='uix_product_dispensary'),)

    # Relationships
    product = relationship("Product", back_populates="prices")
    dispensary = relationship("Dispensary", back_populates="prices")

    def update_price(self, new_price: float):
        """Update price and track history"""
        if self.amount != new_price:
            self.previous_price = self.amount
            self.price_change_percentage = ((new_price - self.amount) / self.amount) * 100 if self.amount else 0
            self.price_change_date = datetime.utcnow()
            self.amount = new_price

    def __repr__(self):
        return f"<Price ${self.amount} at {self.dispensary_id}>"


class Review(Base):
    """Review model for user-submitted product reviews"""
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rating = Column(Integer, nullable=False)  # 1-5 stars
    effects_rating = Column(Integer, nullable=True)  # 1-5 for effects
    taste_rating = Column(Integer, nullable=True)  # 1-5 for taste
    value_rating = Column(Integer, nullable=True)  # 1-5 for value
    comment = Column(Text, nullable=True)
    upvotes = Column(Integer, default=0)

    # Dual-track intention system (Workflow 09)
    intention_type = Column(String, nullable=True)  # "medical" or "mood"
    intention_tag = Column(String, nullable=True)  # e.g., "pain", "socializing"

    # Batch tracking (optional)
    batch_number = Column(String, nullable=True)
    cultivation_date = Column(DateTime, nullable=True)

    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")

    def __repr__(self):
        return f"<Review {self.rating}★ for {self.product_id}>"


class ScraperFlag(Base):
    """
    Flags for products with low confidence matches requiring manual admin review.

    Confidence thresholds (PRD section 4.1):
    - >90%: Auto-merge to existing product
    - 60-90%: Flagged for admin review (stored here)
    - <60%: Create new product entry
    """
    __tablename__ = "scraper_flags"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Original scraped data
    original_name = Column(String, nullable=False)  # Product name as scraped from dispensary
    original_thc = Column(Float, nullable=True)
    original_cbd = Column(Float, nullable=True)
    brand_name = Column(String, nullable=False)
    dispensary_id = Column(String, ForeignKey("dispensaries.id"), nullable=False)

    # Potential match
    matched_product_id = Column(String, ForeignKey("products.id"), nullable=True)
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0

    # Status workflow
    status = Column(String, default="pending", index=True)  # pending, approved, rejected, merged
    merge_reason = Column(String, nullable=True)  # Why flagged for review

    # Admin action
    admin_notes = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String, nullable=True)  # Future: admin user_id

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dispensary = relationship("Dispensary", back_populates="scraper_flags")
    matched_product = relationship("Product", foreign_keys=[matched_product_id])

    def __repr__(self):
        return f"<ScraperFlag {self.original_name} ({self.confidence_score:.0%}) @ {self.status}>"


class Promotion(Base):
    """
    Stores recurring and one-time promotional offers (PRD section 4.2).

    Supports:
    - One-time promotions with start/end dates
    - Recurring deals (e.g., "Medical Mondays", "Friday Vape Sales")
    - Category-wide or product-specific discounts
    """
    __tablename__ = "promotions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Promotion details
    title = Column(String, nullable=False)  # e.g., "Medical Monday 15% off"
    description = Column(Text, nullable=True)
    discount_percentage = Column(Float, nullable=True)  # 0-100 (e.g., 15 = 15% off)
    discount_amount = Column(Float, nullable=True)  # Fixed $ amount off

    # Scope
    dispensary_id = Column(String, ForeignKey("dispensaries.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=True)  # NULL = applies to category or all
    applies_to_category = Column(String, nullable=True)  # "Flower", "Vape", "Edible", etc.

    # Recurrence (PRD: "Medical Mondays", "Friday Vape Sales")
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(String, nullable=True)  # "daily", "weekly", "monthly"
    recurring_day = Column(String, nullable=True)  # "monday", "friday", etc.

    # Validity period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)  # NULL = no end date (ongoing)

    # Status
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    dispensary = relationship("Dispensary", back_populates="promotions")
    product = relationship("Product", back_populates="promotions")

    def __repr__(self):
        return f"<Promotion '{self.title}' @ {self.dispensary_id}>"

    def is_currently_active(self) -> bool:
        """Check if promotion is currently valid"""
        now = datetime.utcnow()
        if not self.is_active:
            return False
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True


class Watchlist(Base):
    """User's watched products for price and stock alerts"""
    __tablename__ = "watchlists"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)

    # Alert preferences
    alert_on_stock = Column(Boolean, default=True)  # Notify when back in stock
    alert_on_price_drop = Column(Boolean, default=True)  # Notify on price decrease
    price_drop_threshold = Column(Float, nullable=True, default=10.0)  # % threshold (e.g., 10 = 10% drop)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint: one watchlist entry per user per product
    __table_args__ = (UniqueConstraint('user_id', 'product_id', name='uix_user_product'),)

    # Relationships
    user = relationship("User")
    product = relationship("Product")

    def __repr__(self):
        return f"<Watchlist user={self.user_id} product={self.product_id}>"


class PriceAlert(Base):
    """Log of price alerts sent to users"""
    __tablename__ = "price_alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"), nullable=False, index=True)
    dispensary_id = Column(String, ForeignKey("dispensaries.id"), nullable=False, index=True)

    alert_type = Column(String, nullable=False, index=True)  # "stock_available" or "price_drop"
    previous_price = Column(Float, nullable=True)
    new_price = Column(Float, nullable=True)
    percent_change = Column(Float, nullable=True)

    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
    email_sent = Column(Boolean, default=False)

    # Relationships
    user = relationship("User")
    product = relationship("Product")
    dispensary = relationship("Dispensary")

    def __repr__(self):
        return f"<PriceAlert {self.alert_type} for user={self.user_id} product={self.product_id}>"


class NotificationPreference(Base):
    """User notification settings"""
    __tablename__ = "notification_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Email preferences
    email_stock_alerts = Column(Boolean, default=True)
    email_price_drops = Column(Boolean, default=True)
    email_frequency = Column(String, default="immediately")  # "immediately", "daily", or "weekly"

    # In-app preferences (placeholder for future)
    app_notifications = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<NotificationPreference user={self.user_id} frequency={self.email_frequency}>"


class ScraperRun(Base):
    """Log of every scraper execution for monitoring and diagnostics."""
    __tablename__ = "scraper_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Scraper identity
    scraper_id = Column(String, nullable=False, index=True)
    scraper_name = Column(String, nullable=False)
    dispensary_id = Column(String, ForeignKey("dispensaries.id"), nullable=True, index=True)

    # Execution details
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Results
    status = Column(String, nullable=False, default="running", index=True)  # running, success, error, warning
    products_found = Column(Integer, default=0)
    products_processed = Column(Integer, default=0)
    flags_created = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_type = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)

    # Metadata
    triggered_by = Column(String, nullable=True)  # "scheduler", "manual", or admin user id

    # Relationships
    dispensary = relationship("Dispensary")

    def complete(self, status: str, products_found: int = 0, products_processed: int = 0,
                 flags_created: int = 0, error_message: str = None, error_type: str = None):
        """Mark run as completed with results."""
        self.status = status
        self.completed_at = datetime.utcnow()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.products_found = products_found
        self.products_processed = products_processed
        self.flags_created = flags_created
        self.error_message = error_message
        self.error_type = error_type

    def __repr__(self):
        return f"<ScraperRun {self.scraper_id} {self.status} at {self.started_at}>"

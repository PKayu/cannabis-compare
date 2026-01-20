"""
SQLAlchemy models for database tables
Based on the Prisma schema from the PRD
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
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
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prices = relationship("Price", back_populates="dispensary", cascade="all, delete-orphan")

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
    """Product model for strains and cannabis products"""
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)  # e.g., "Gorilla Glue #4"
    product_type = Column(String, nullable=False)  # e.g., "Flower", "Vape", "Edible"
    thc_percentage = Column(Float, nullable=True)  # THC content
    cbd_percentage = Column(Float, nullable=True)  # CBD content
    brand_id = Column(String, ForeignKey("brands.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    brand = relationship("Brand", back_populates="products")
    prices = relationship("Price", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product {self.name}>"


class Price(Base):
    """Price model linking products to dispensaries with pricing"""
    __tablename__ = "prices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    amount = Column(Float, nullable=False)  # Price in USD
    in_stock = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    dispensary_id = Column(String, ForeignKey("dispensaries.id"), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="prices")
    dispensary = relationship("Dispensary", back_populates="prices")

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
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")

    def __repr__(self):
        return f"<Review {self.rating}★ for {self.product_id}>"

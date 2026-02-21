"""
Test suite for products endpoints
Tests for /api/products/{id}, /api/products/{id}/prices, /api/products/{id}/related, /api/products/{id}/pricing-history
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
from models import Product, Brand, Price, Dispensary, Promotion


@pytest.mark.integration
class TestProductEndpoints:
    """Tests for /api/products endpoints"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        """Setup test data for product tests"""
        self.db = db_session

        # Create test brand
        self.brand = Brand(name="WholesomeCo")
        self.db.add(self.brand)
        self.db.flush()

        # Create test dispensaries
        self.dispensary1 = Dispensary(
            name="Wholesome Co.",
            location="Salt Lake City, UT",
            website="https://wholesome.co"
        )
        self.dispensary2 = Dispensary(
            name="Beehive Farmacy",
            location="Salt Lake City, UT",
            website="https://beehivefarmacy.com"
        )
        self.db.add_all([self.dispensary1, self.dispensary2])
        self.db.flush()

        # Create test product
        self.product = Product(
            name="Gorilla Glue #4",
            product_type="Flower",
            thc_percentage=24.5,
            cbd_percentage=0.1,
            brand_id=self.brand.id,
            is_master=True
        )
        self.db.add(self.product)
        self.db.flush()

        # Create prices
        self.price1 = Price(
            amount=45.00,
            in_stock=True,
            product_id=self.product.id,
            dispensary_id=self.dispensary1.id
        )
        self.price2 = Price(
            amount=50.00,
            in_stock=True,
            product_id=self.product.id,
            dispensary_id=self.dispensary2.id
        )
        self.db.add_all([self.price1, self.price2])
        self.db.commit()

    def test_get_product_details(self, client):
        """Test GET /api/products/{id} returns product info"""
        response = client.get(f"/api/products/{self.product.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == str(self.product.id)
        assert data["name"] == "Gorilla Glue #4"
        assert data["brand"] == "WholesomeCo"
        assert data["product_type"] == "Flower"
        assert data["thc_percentage"] == 24.5
        assert data["cbd_percentage"] == 0.1
        assert data["is_master"] is True
        assert "created_at" in data
        assert "updated_at" in data

    def test_get_product_not_found(self, client):
        """Test GET /api/products/{id} returns 404 for non-existent product"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/products/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_get_product_price_comparison(self, client):
        """Test GET /api/products/{id}/prices returns price comparison grouped by weight"""
        response = client.get(f"/api/products/{self.product.id}/prices")

        assert response.status_code == status.HTTP_200_OK
        weight_groups = response.json()

        # API returns a list of weight groups; test data has no weight so one group
        assert len(weight_groups) >= 1

        # Each weight group has variant metadata and a nested prices list
        group = weight_groups[0]
        assert "variant_id" in group
        assert "prices" in group
        assert len(group["prices"]) == 2  # Two dispensaries in test setup

        # Check individual price structure inside the group
        price = group["prices"][0]
        assert "dispensary_id" in price
        assert "dispensary_name" in price
        assert "dispensary_location" in price
        assert "msrp" in price
        assert "in_stock" in price
        assert "last_updated" in price

    def test_get_product_price_comparison_not_found(self, client):
        """Test GET /api/products/{id}/prices returns 404 for non-existent product"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/products/{fake_id}/prices")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_product_price_comparison_with_promotion(self, client, db_session):
        """Test price comparison includes active promotions"""
        # Create active promotion
        promotion = Promotion(
            title="Monday Sale",
            description="20% off all products",
            discount_percentage=20.0,
            is_active=True,
            start_date=datetime.now(timezone.utc) - timedelta(days=1),
            end_date=datetime.now(timezone.utc) + timedelta(days=1),
            dispensary_id=self.dispensary1.id
        )
        db_session.add(promotion)
        db_session.commit()

        response = client.get(f"/api/products/{self.product.id}/prices")

        assert response.status_code == status.HTTP_200_OK
        weight_groups = response.json()

        # Flatten all prices across weight groups to find the one with a promotion
        all_prices = [p for wg in weight_groups for p in wg["prices"]]
        promo_price = next((p for p in all_prices if p["promotion"] is not None), None)
        assert promo_price is not None
        assert promo_price["promotion"]["title"] == "Monday Sale"
        assert promo_price["deal_price"] is not None
        assert promo_price["deal_price"] < promo_price["msrp"]
        assert promo_price["savings"] > 0

    def test_get_product_price_comparison_sorting(self, client):
        """Test price comparison is sorted by price (lowest first)"""
        response = client.get(f"/api/products/{self.product.id}/prices")

        assert response.status_code == status.HTTP_200_OK
        prices = response.json()

        # Check sorted by deal_price or msrp
        if len(prices) > 1:
            for i in range(len(prices) - 1):
                price1 = prices[i]["deal_price"] if prices[i]["deal_price"] else prices[i]["msrp"]
                price2 = prices[i + 1]["deal_price"] if prices[i + 1]["deal_price"] else prices[i + 1]["msrp"]
                assert price1 <= price2

    def test_get_related_products(self, client, db_session):
        """Test GET /api/products/{id}/related returns similar products"""
        # Create related products
        related1 = Product(
            name="Blue Dream",
            product_type="Flower",
            thc_percentage=21.0,
            cbd_percentage=0.5,
            brand_id=self.brand.id,  # Same brand
            is_master=True
        )
        related2 = Product(
            name="OG Kush",
            product_type="Edible",  # Different type
            thc_percentage=10.0,
            cbd_percentage=0.0,
            brand_id=self.brand.id,
            is_master=True
        )
        db_session.add_all([related1, related2])
        db_session.flush()

        # Add prices for related products
        db_session.add(Price(
            amount=40.00,
            in_stock=True,
            product_id=related1.id,
            dispensary_id=self.dispensary1.id
        ))
        db_session.add(Price(
            amount=35.00,
            in_stock=True,
            product_id=related2.id,
            dispensary_id=self.dispensary1.id
        ))
        db_session.commit()

        response = client.get(f"/api/products/{self.product.id}/related")

        assert response.status_code == status.HTTP_200_OK
        related = response.json()

        assert len(related) > 0
        assert all("id" in r for r in related)
        assert all("name" in r for r in related)
        assert all("brand" in r for r in related)
        assert all("min_price" in r for r in related)
        assert all("max_price" in r for r in related)

    def test_get_related_products_not_found(self, client):
        """Test GET /api/products/{id}/related returns 404 for non-existent product"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/products/{fake_id}/related")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_related_products_limit(self, client, db_session):
        """Test GET /api/products/{id}/related respects limit parameter"""
        # Create multiple related products
        for i in range(10):
            product = Product(
                name=f"Product {i}",
                product_type="Flower",
                thc_percentage=20.0,
                cbd_percentage=0.1,
                brand_id=self.brand.id,
                is_master=True
            )
            db_session.add(product)
        db_session.commit()

        response = client.get(f"/api/products/{self.product.id}/related?limit=5")

        assert response.status_code == status.HTTP_200_OK
        related = response.json()

        assert len(related) <= 5

    def test_get_pricing_history(self, client, db_session):
        """Test GET /api/products/{id}/pricing-history returns price history"""
        # Add price change history
        self.price1.previous_price = 50.00
        self.price1.price_change_date = datetime.now(timezone.utc) - timedelta(days=5)
        self.price1.price_change_percentage = -10.0
        db_session.commit()

        response = client.get(f"/api/products/{self.product.id}/pricing-history?days=30")

        assert response.status_code == status.HTTP_200_OK
        history = response.json()

        assert isinstance(history, list)

    def test_get_pricing_history_not_found(self, client):
        """Test GET /api/products/{id}/pricing-history returns 404 for non-existent product"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/products/{fake_id}/pricing-history")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_pricing_history_days_parameter(self, client):
        """Test GET /api/products/{id}/pricing-history respects days parameter"""
        response = client.get(f"/api/products/{self.product.id}/pricing-history?days=7")

        assert response.status_code == status.HTTP_200_OK
        history = response.json()

        assert isinstance(history, list)

    def test_get_pricing_history_invalid_days(self, client):
        """Test GET /api/products/{id}/pricing-history validates days parameter"""
        # Test with days > 365 (should fail validation)
        response = client.get(f"/api/products/{self.product.id}/pricing-history?days=400")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_product_with_out_of_stock_prices(self, client, db_session):
        """Test product details work even when all prices are out of stock"""
        # Mark all prices as out of stock
        self.price1.in_stock = False
        self.price2.in_stock = False
        db_session.commit()

        response = client.get(f"/api/products/{self.product.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(self.product.id)

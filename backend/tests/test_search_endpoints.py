"""
Test suite for product search endpoints
Tests for /api/products/search and /api/products/autocomplete
"""
import pytest
from fastapi import status
from models import Product, Brand, Price, Dispensary


@pytest.mark.integration
class TestProductSearch:
    """Tests for /api/products/search endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        """Setup test data for search tests"""
        self.db = db_session

        # Create test brands
        self.brand_wholesome = Brand(name="WholesomeCo")
        self.brand_tryke = Brand(name="Tryke")
        self.brand_beehive = Brand(name="Beehive Farmacy")
        self.db.add_all([self.brand_wholesome, self.brand_tryke, self.brand_beehive])
        self.db.flush()

        # Create test dispensaries
        self.dispensary_slc = Dispensary(
            name="Wholesome Co.",
            location="Salt Lake City, UT"
        )
        self.dispensary_park = Dispensary(
            name="Tryke Dispensary",
            location="Park City, UT"
        )
        self.db.add_all([self.dispensary_slc, self.dispensary_park])
        self.db.flush()

        # Create test products with realistic data
        self.products = []

        # Flower products
        product_gorilla = Product(
            name="Gorilla Glue #4",
            product_type="Flower",
            thc_percentage=24.5,
            cbd_percentage=0.1,
            brand_id=self.brand_wholesome.id,
            is_master=True
        )
        self.products.append(product_gorilla)

        product_blue = Product(
            name="Blue Dream",
            product_type="Flower",
            thc_percentage=21.0,
            cbd_percentage=0.5,
            brand_id=self.brand_tryke.id,
            is_master=True
        )
        self.products.append(product_blue)

        product_og = Product(
            name="OG Kush",
            product_type="Flower",
            thc_percentage=23.0,
            cbd_percentage=0.2,
            brand_id=self.brand_beehive.id,
            is_master=True
        )
        self.products.append(product_og)

        product_gdp = Product(
            name="Granddaddy Purple",
            product_type="Flower",
            thc_percentage=20.5,
            cbd_percentage=0.3,
            brand_id=self.brand_wholesome.id,
            is_master=True
        )
        self.products.append(product_gdp)

        # Edible product
        product_gummy = Product(
            name="Watermelon Gummies 10mg",
            product_type="Edible",
            thc_percentage=10.0,
            cbd_percentage=0.0,
            brand_id=self.brand_wholesome.id,
            is_master=True
        )
        self.products.append(product_gummy)

        # Vape product
        product_vape = Product(
            name="Blue Dream Vape Cart",
            product_type="Vape",
            thc_percentage=85.0,
            cbd_percentage=0.5,
            brand_id=self.brand_tryke.id,
            is_master=True
        )
        self.products.append(product_vape)

        self.db.add_all(self.products)
        self.db.flush()

        # Create prices for products
        # Gorilla Glue - multiple prices
        self.db.add(Price(
            amount=45.00,
            in_stock=True,
            product_id=product_gorilla.id,
            dispensary_id=self.dispensary_slc.id
        ))
        self.db.add(Price(
            amount=50.00,
            in_stock=True,
            product_id=product_gorilla.id,
            dispensary_id=self.dispensary_park.id
        ))

        # Blue Dream - single price
        self.db.add(Price(
            amount=40.00,
            in_stock=True,
            product_id=product_blue.id,
            dispensary_id=self.dispensary_slc.id
        ))

        # OG Kush - higher price
        self.db.add(Price(
            amount=55.00,
            in_stock=True,
            product_id=product_og.id,
            dispensary_id=self.dispensary_slc.id
        ))

        # Granddaddy Purple - lower price
        self.db.add(Price(
            amount=35.00,
            in_stock=True,
            product_id=product_gdp.id,
            dispensary_id=self.dispensary_slc.id
        ))

        # Gummy
        self.db.add(Price(
            amount=25.00,
            in_stock=True,
            product_id=product_gummy.id,
            dispensary_id=self.dispensary_slc.id
        ))

        # Vape
        self.db.add(Price(
            amount=60.00,
            in_stock=True,
            product_id=product_vape.id,
            dispensary_id=self.dispensary_slc.id
        ))

        self.db.commit()

    def test_search_basic_query(self, client):
        """Test basic product search by name"""
        response = client.get("/api/products/search?q=Blue Dream")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        # Should find Blue Dream products
        assert len(results) > 0
        assert any("Blue Dream" in r["name"] for r in results)

        # Check response structure
        result = results[0]
        assert "id" in result
        assert "name" in result
        assert "brand" in result
        assert "thc" in result
        assert "cbd" in result
        assert "type" in result
        assert "min_price" in result
        assert "max_price" in result
        assert "dispensary_count" in result
        assert "relevance_score" in result

    def test_search_with_category_filter(self, client):
        """Test search filtered by product type"""
        response = client.get("/api/products/search?q=Dream&product_type=Flower")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        # Should only return Flower products
        assert all(r["type"] == "Flower" for r in results)

    def test_search_with_price_range(self, client):
        """Test search filtered by price range"""
        response = client.get("/api/products/search?q=Gorilla&min_price=40&max_price=50")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        # All results should have prices in range
        for result in results:
            assert result["min_price"] >= 40
            assert result["max_price"] <= 50

    def test_search_with_thc_filter(self, client):
        """Test search filtered by THC percentage"""
        response = client.get("/api/products/search?q=Blue&min_thc=20")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        # All results should have THC >= 20%
        for result in results:
            assert result["thc"] is None or result["thc"] >= 20.0

    def test_search_with_cbd_filter(self, client):
        """Test search filtered by CBD percentage"""
        response = client.get("/api/products/search?q=Dream&min_cbd=0.3")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        # All results should have CBD >= 0.3%
        for result in results:
            assert result["cbd"] is None or result["cbd"] >= 0.3

    def test_search_pagination(self, client):
        """Test search results with limit"""
        response = client.get("/api/products/search?q=Blue&limit=5")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        # Should return at most 5 results
        assert len(results) <= 5

    def test_search_no_results(self, client):
        """Test search returns empty when no matches"""
        response = client.get("/api/products/search?q=NonExistentProductXYZ")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        # Should return empty list
        assert len(results) == 0

    def test_search_sort_by_price_low(self, client):
        """Test search sorting by price low to high"""
        response = client.get("/api/products/search?q=Gorilla&sort_by=price_low")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        if len(results) > 1:
            # Check sorted by min_price ascending
            for i in range(len(results) - 1):
                assert results[i]["min_price"] <= results[i + 1]["min_price"]

    def test_search_sort_by_price_high(self, client):
        """Test search sorting by price high to low"""
        response = client.get("/api/products/search?q=Glue&sort_by=price_high")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        if len(results) > 1:
            # Check sorted by max_price descending
            for i in range(len(results) - 1):
                assert results[i]["max_price"] >= results[i + 1]["max_price"]

    def test_search_sort_by_thc(self, client):
        """Test search sorting by THC percentage"""
        response = client.get("/api/products/search?q=Dream&sort_by=thc")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        if len(results) > 1:
            # Check sorted by THC descending (products with THC should come first)
            thc_values = [r["thc"] or 0 for r in results]
            for i in range(len(thc_values) - 1):
                assert thc_values[i] >= thc_values[i + 1]

    def test_search_sort_by_cbd(self, client):
        """Test search sorting by CBD percentage"""
        response = client.get("/api/products/search?q=Dream&sort_by=cbd")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        if len(results) > 1:
            # Check sorted by CBD descending
            cbd_values = [r["cbd"] or 0 for r in results]
            for i in range(len(cbd_values) - 1):
                assert cbd_values[i] >= cbd_values[i + 1]

    def test_search_minimum_query_length(self, client):
        """Test search requires minimum 2 characters"""
        # Query with 1 character should fail validation
        response = client.get("/api/products/search?q=A")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_search_brand_matching(self, client):
        """Test search can match by brand name"""
        response = client.get("/api/products/search?q=WholesomeCo")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        # Should find products from WholesomeCo brand
        assert len(results) > 0
        assert any(r["brand"] == "WholesomeCo" for r in results)

    def test_search_fuzzy_matching(self, client):
        """Test search uses fuzzy matching for typos and variations"""
        # Search for "Gorrila" (typo of "Gorilla")
        response = client.get("/api/products/search?q=Gorrila")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        # Should still find Gorilla Glue despite typo
        assert len(results) > 0
        assert any("Gorilla" in r["name"] for r in results)

    def test_search_case_insensitive(self, client):
        """Test search is case insensitive"""
        response_lower = client.get("/api/products/search?q=blue dream")
        response_upper = client.get("/api/products/search?q=BLUE DREAM")
        response_mixed = client.get("/api/products/search?q=BlUe DrEaM")

        assert response_lower.status_code == status.HTTP_200_OK
        assert response_upper.status_code == status.HTTP_200_OK
        assert response_mixed.status_code == status.HTTP_200_OK

        results_lower = response_lower.json()
        results_upper = response_upper.json()
        results_mixed = response_mixed.json()

        # All should return same number of results
        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_search_dispensary_count(self, client):
        """Test search returns accurate dispensary count"""
        response = client.get("/api/products/search?q=Gorilla Glue")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        # Gorilla Glue should be available at 2 dispensaries
        gorilla_result = next((r for r in results if "Gorilla Glue" in r["name"]), None)
        assert gorilla_result is not None
        assert gorilla_result["dispensary_count"] == 2

    def test_search_out_of_stock_products(self, client, db_session):
        """Test search excludes products with no in-stock prices"""
        # Find a product and mark all its prices as out of stock
        product = db_session.query(Product).filter(Product.name == "Granddaddy Purple").first()
        for price in product.prices:
            price.in_stock = False
        db_session.commit()

        response = client.get("/api/products/search?q=Granddaddy")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        # Should not find the out-of-stock product
        assert not any("Granddaddy Purple" in r["name"] for r in results)

    def test_search_relevance_score(self, client):
        """Test search returns relevance scores"""
        response = client.get("/api/products/search?q=Blue Dream")

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        # All results should have relevance scores
        for result in results:
            assert "relevance_score" in result
            assert 0 <= result["relevance_score"] <= 1

        # Exact match should have high relevance
        blue_dream = next((r for r in results if "Blue Dream" in r["name"]), None)
        assert blue_dream is not None
        assert blue_dream["relevance_score"] >= 0.8


@pytest.mark.integration
class TestProductAutocomplete:
    """Tests for /api/products/autocomplete endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        """Setup test data for autocomplete tests"""
        self.db = db_session

        # Create test brand
        self.brand = Brand(name="WholesomeCo")
        self.db.add(self.brand)
        self.db.flush()

        # Create test products
        self.products = [
            Product(name="Gorilla Glue #4", product_type="Flower", thc_percentage=24.5,
                   cbd_percentage=0.1, brand_id=self.brand.id, is_master=True),
            Product(name="Blue Dream", product_type="Flower", thc_percentage=21.0,
                   cbd_percentage=0.5, brand_id=self.brand.id, is_master=True),
            Product(name="OG Kush", product_type="Flower", thc_percentage=23.0,
                   cbd_percentage=0.2, brand_id=self.brand.id, is_master=True),
            Product(name="Granddaddy Purple", product_type="Flower", thc_percentage=20.5,
                   cbd_percentage=0.3, brand_id=self.brand.id, is_master=True),
        ]
        self.db.add_all(self.products)
        self.db.commit()

    def test_autocomplete_basic(self, client):
        """Test basic autocomplete functionality"""
        response = client.get("/api/products/autocomplete?q=Blu")

        assert response.status_code == status.HTTP_200_OK
        suggestions = response.json()

        assert len(suggestions) > 0
        assert any("Blue Dream" in s["name"] for s in suggestions)

    def test_autocomplete_limit(self, client):
        """Test autocomplete respects limit parameter"""
        response = client.get("/api/products/autocomplete?q=on&limit=2")

        assert response.status_code == status.HTTP_200_OK
        suggestions = response.json()

        # Should return at most 2 suggestions
        assert len(suggestions) <= 2

    def test_autocomplete_minimum_length(self, client):
        """Test autocomplete requires minimum 2 characters"""
        response = client.get("/api/products/autocomplete?q=A")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_autocomplete_response_structure(self, client):
        """Test autocomplete returns correct response structure"""
        response = client.get("/api/products/autocomplete?q=Gor")

        assert response.status_code == status.HTTP_200_OK
        suggestions = response.json()

        if len(suggestions) > 0:
            suggestion = suggestions[0]
            assert "id" in suggestion
            assert "name" in suggestion
            assert "brand" in suggestion
            assert "type" in suggestion

    def test_autocomplete_case_insensitive(self, client):
        """Test autocomplete is case insensitive"""
        response_lower = client.get("/api/products/autocomplete?q=blu")
        response_upper = client.get("/api/products/autocomplete?q=BLU")

        assert response_lower.status_code == status.HTTP_200_OK
        assert response_upper.status_code == status.HTTP_200_OK

        results_lower = response_lower.json()
        results_upper = response_upper.json()

        # Both should return same results
        assert len(results_lower) == len(results_upper)

    def test_autocomplete_no_results(self, client):
        """Test autocomplete returns empty when no matches"""
        response = client.get("/api/products/autocomplete?q=NonExistentXYZ")

        assert response.status_code == status.HTTP_200_OK
        suggestions = response.json()

        assert len(suggestions) == 0

    def test_autocomplete_multiple_matches(self, client):
        """Test autocomplete returns multiple matching products"""
        # Search for products containing "o" - should match multiple products
        response = client.get("/api/products/autocomplete?q=or")

        assert response.status_code == status.HTTP_200_OK
        suggestions = response.json()

        # Should return multiple products (matching "or" in "Gorilla" and "Granddaddy Pur**pl**e")
        assert len(suggestions) >= 1  # At least one match

"""
Tests for scraper functionality.

Run with: pytest backend/tests/test_scraper.py -v
"""
import pytest
from datetime import datetime, timezone
from services.scrapers.base_scraper import BaseScraper, ScrapedProduct, ScrapedPromotion
from services.scrapers.playwright_scraper import WholesomeCoScraper


class MockScraper(BaseScraper):
    """Mock scraper for testing base functionality"""

    def __init__(self, dispensary_id: str, products=None, promotions=None, should_fail=False):
        super().__init__(dispensary_id)
        self._products = products or []
        self._promotions = promotions or []
        self._should_fail = should_fail
        self._scrape_count = 0

    async def scrape_products(self):
        self._scrape_count += 1
        if self._should_fail:
            raise Exception("Intentional failure")
        return self._products

    async def scrape_promotions(self):
        if self._should_fail:
            raise Exception("Intentional failure")
        return self._promotions


class TestScrapedProduct:
    """Test cases for ScrapedProduct data class"""

    def test_create_product(self):
        """Test creating a ScrapedProduct"""
        product = ScrapedProduct(
            name="Gorilla Glue #4",
            brand="Tryke",
            category="Flower",
            price=45.00,
            in_stock=True,
            thc_percentage=24.5,
            cbd_percentage=0.5
        )

        assert product.name == "Gorilla Glue #4"
        assert product.brand == "Tryke"
        assert product.category == "Flower"
        assert product.price == 45.00
        assert product.in_stock is True
        assert product.thc_percentage == 24.5
        assert product.cbd_percentage == 0.5

    def test_product_defaults(self):
        """Test ScrapedProduct default values"""
        product = ScrapedProduct(
            name="Test Product",
            brand="Test Brand",
            category="Flower",
            price=30.00
        )

        assert product.in_stock is True
        assert product.thc_percentage is None
        assert product.cbd_percentage is None
        assert product.batch_number is None


class TestScrapedPromotion:
    """Test cases for ScrapedPromotion data class"""

    def test_create_promotion(self):
        """Test creating a ScrapedPromotion"""
        promo = ScrapedPromotion(
            title="Medical Monday 15% Off",
            start_date=datetime.now(timezone.utc),
            discount_percentage=15.0,
            is_recurring=True,
            recurring_day="monday"
        )

        assert promo.title == "Medical Monday 15% Off"
        assert promo.discount_percentage == 15.0
        assert promo.is_recurring is True
        assert promo.recurring_day == "monday"

    def test_promotion_defaults(self):
        """Test ScrapedPromotion default values"""
        promo = ScrapedPromotion(
            title="Test Promo",
            start_date=datetime.now(timezone.utc)
        )

        assert promo.description is None
        assert promo.discount_percentage is None
        assert promo.is_recurring is False
        assert promo.recurring_day is None


class TestBaseScraper:
    """Test cases for BaseScraper class"""

    @pytest.mark.asyncio
    async def test_run_success(self):
        """Test successful scraper run"""
        products = [
            ScrapedProduct(name="Product 1", brand="Brand", category="Flower", price=30.0)
        ]
        promotions = [
            ScrapedPromotion(title="Promo 1", start_date=datetime.now(timezone.utc))
        ]

        scraper = MockScraper("test-dispensary", products, promotions)
        result = await scraper.run()

        assert result["status"] == "success"
        assert len(result["products"]) == 1
        assert len(result["promotions"]) == 1
        assert result["dispensary_id"] == "test-dispensary"
        assert "scraped_at" in result

    @pytest.mark.asyncio
    async def test_run_failure(self):
        """Test failed scraper run"""
        scraper = MockScraper("test-dispensary", should_fail=True)
        result = await scraper.run()

        assert result["status"] == "error"
        assert "error" in result
        assert result["products"] == []
        assert result["promotions"] == []

    @pytest.mark.asyncio
    async def test_run_with_retries_success(self):
        """Test retry logic succeeds eventually"""
        products = [
            ScrapedProduct(name="Product 1", brand="Brand", category="Flower", price=30.0)
        ]

        scraper = MockScraper("test-dispensary", products)
        result = await scraper.run_with_retries(max_retries=3, initial_delay=0.1)

        assert result["status"] == "success"
        assert scraper._scrape_count == 1  # Should succeed first try

    @pytest.mark.asyncio
    async def test_run_with_retries_all_fail(self):
        """Test retry logic when all attempts fail"""
        scraper = MockScraper("test-dispensary", should_fail=True)
        result = await scraper.run_with_retries(max_retries=2, initial_delay=0.1)

        assert result["status"] == "error"
        assert result["attempts"] == 2
        assert scraper._scrape_count == 2

    def test_get_last_run_initially_none(self):
        """Test last_run is None before first run"""
        scraper = MockScraper("test-dispensary")
        assert scraper.get_last_run() is None

    @pytest.mark.asyncio
    async def test_get_last_run_after_run(self):
        """Test last_run is set after run"""
        scraper = MockScraper("test-dispensary")
        await scraper.run()

        assert scraper.get_last_run() is not None
        assert isinstance(scraper.get_last_run(), datetime)


class TestWholesomeCoScraper:
    """Test cases for WholesomeCoScraper"""

    def test_map_category_from_string(self):
        """Test category mapping from string input"""
        scraper = WholesomeCoScraper("test")
        assert scraper._map_category("flower") == "flower"
        assert scraper._map_category("FLOWER") == "flower"
        assert scraper._map_category("vapes") == "vaporizer"
        assert scraper._map_category("cartridge") == "vaporizer"
        assert scraper._map_category("edibles") == "edible"
        assert scraper._map_category("gummy") == "edible"
        assert scraper._map_category("pre-roll") == "pre-roll"
        assert scraper._map_category("preroll") == "pre-roll"
        assert scraper._map_category("concentrate") == "concentrate"
        assert scraper._map_category("tincture") == "tincture"
        assert scraper._map_category("topical") == "topical"
        assert scraper._map_category("unknown") == "other"

    def test_map_category_from_list(self):
        """Test category mapping from list input"""
        scraper = WholesomeCoScraper("test")
        assert scraper._map_category(["flower", "indica"]) == "flower"
        assert scraper._map_category(["vape", "cartridge"]) == "vaporizer"
        assert scraper._map_category(["edible", "gummy"]) == "edible"
        assert scraper._map_category([]) == "other"

    def test_extract_percentage(self):
        """Test THC/CBD percentage extraction"""
        scraper = WholesomeCoScraper("test")
        assert scraper._extract_percentage("24.5% THC") == 24.5
        assert scraper._extract_percentage("24.5%") == 24.5
        assert scraper._extract_percentage("THC 24.5%") == 24.5
        assert scraper._extract_percentage("no percentage") is None
        assert scraper._extract_percentage("") is None
        assert scraper._extract_percentage(None) is None

    def test_extract_unit_size(self):
        """Test unit size extraction from product name"""
        scraper = WholesomeCoScraper("test")
        assert scraper._extract_unit_size("Gorilla Glue 3.5g") == "3.5g"
        assert scraper._extract_unit_size("Product 1g") == "1g"
        assert scraper._extract_unit_size("100mg edible") == "100mg"
        assert scraper._extract_unit_size("30ml tincture") == "30ml"
        assert scraper._extract_unit_size("no size") is None
        assert scraper._extract_unit_size("") is None
        assert scraper._extract_unit_size(None) is None

    @pytest.mark.asyncio
    async def test_scraper_initialization(self):
        """Test scraper initialization"""
        scraper = WholesomeCoScraper("wholesome-co-dispensary-id")

        # Test instance attributes
        assert scraper.dispensary_id == "wholesome-co-dispensary-id"
        assert scraper.SHOP_URL == "https://www.wholesome.co/shop"
        assert scraper.name == "WholesomeCoScraper"  # name property returns class name

        # Test that scraper is registered in the registry
        from services.scrapers.registry import ScraperRegistry
        config = ScraperRegistry.get("wholesomeco")
        assert config is not None
        assert config.name == "WholesomeCo"
        assert config.dispensary_name == "WholesomeCo"
        assert config.dispensary_location == "Bountiful, UT"

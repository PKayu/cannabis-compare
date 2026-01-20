"""
Tests for scraper functionality.

Run with: pytest backend/tests/test_scraper.py -v
"""
import pytest
from datetime import datetime
from services.scrapers.base_scraper import BaseScraper, ScrapedProduct, ScrapedPromotion
from services.scrapers.wholesome_co_scraper import WholesomeCoScraper


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
            start_date=datetime.utcnow(),
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
            start_date=datetime.utcnow()
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
            ScrapedPromotion(title="Promo 1", start_date=datetime.utcnow())
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

    def test_normalize_category(self):
        """Test category normalization"""
        assert WholesomeCoScraper._normalize_category("flower") == "Flower"
        assert WholesomeCoScraper._normalize_category("FLOWER") == "Flower"
        assert WholesomeCoScraper._normalize_category("vapes") == "Vape"
        assert WholesomeCoScraper._normalize_category("cartridge") == "Vape"
        assert WholesomeCoScraper._normalize_category("edibles") == "Edible"
        assert WholesomeCoScraper._normalize_category("gummy") == "Edible"
        assert WholesomeCoScraper._normalize_category("unknown") == "Other"

    def test_parse_price(self):
        """Test price parsing"""
        assert WholesomeCoScraper._parse_price("$45.00") == 45.00
        assert WholesomeCoScraper._parse_price("45") == 45.00
        assert WholesomeCoScraper._parse_price("$99.99") == 99.99
        assert WholesomeCoScraper._parse_price("") == 0.0
        assert WholesomeCoScraper._parse_price("invalid") == 0.0

    def test_parse_percentage(self):
        """Test percentage parsing"""
        assert WholesomeCoScraper._parse_percentage("24.5%") == 24.5
        assert WholesomeCoScraper._parse_percentage("24.5") == 24.5
        assert WholesomeCoScraper._parse_percentage(24.5) == 24.5
        assert WholesomeCoScraper._parse_percentage(None) is None
        assert WholesomeCoScraper._parse_percentage("") is None

    def test_check_recurring(self):
        """Test recurring promotion detection"""
        from bs4 import BeautifulSoup

        # Recurring Monday promotion
        html = '<div class="promo">Every Monday get 15% off!</div>'
        soup = BeautifulSoup(html, "html.parser")
        elem = soup.find("div")

        scraper = WholesomeCoScraper("test")
        is_recurring, day = scraper._check_recurring(elem)

        assert is_recurring is True
        assert day == "monday"

    def test_check_recurring_not_recurring(self):
        """Test non-recurring promotion detection"""
        from bs4 import BeautifulSoup

        html = '<div class="promo">One time sale!</div>'
        soup = BeautifulSoup(html, "html.parser")
        elem = soup.find("div")

        scraper = WholesomeCoScraper("test")
        is_recurring, day = scraper._check_recurring(elem)

        assert is_recurring is False
        assert day is None

    def test_extract_discount_percentage(self):
        """Test discount percentage extraction"""
        from bs4 import BeautifulSoup

        html = '<div class="promo">Get 15% off all flowers!</div>'
        soup = BeautifulSoup(html, "html.parser")
        elem = soup.find("div")

        scraper = WholesomeCoScraper("test")
        discount = scraper._extract_discount_percentage(elem)

        assert discount == 15.0

    @pytest.mark.asyncio
    async def test_scraper_initialization(self):
        """Test scraper initialization"""
        scraper = WholesomeCoScraper("wholesome-co-dispensary-id")

        assert scraper.dispensary_id == "wholesome-co-dispensary-id"
        assert scraper.name == "WholesomeCoScraper"
        assert scraper.BASE_URL == "https://www.wholesomeco.com"

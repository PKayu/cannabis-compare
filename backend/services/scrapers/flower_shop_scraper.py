"""
The Flower Shop Scraper — iHeartJane / dmerch Platform

The Flower Shop operates two Utah locations:
  - Logan (North Logan, 2150 N Main, Suite 1, North Logan, UT 84341) — iHeartJane store ID 5150
  - Ogden (South Ogden, 3775 S Wall Ave, South Ogden, UT 84405)     — iHeartJane store ID 5151

Both locations embed iHeartJane's "frameless boost" menu on their website. The public REST
API at api.iheartjane.com is gated (HTTP 403 for server-to-server calls), but the menu
product data is served via a separate merchandising API at dmerch.iheartjane.com using POST
requests with a publicly embedded JDM API key.

Scraping strategy:
  1. Use Playwright to navigate to each category page:
       https://theflowershopusa.com/{location}/menu/{kind}
  2. Intercept the POST response from dmerch.iheartjane.com/v2/multi, which returns all
     products for that category (placement="menu_inline_table").
  3. Parse product attributes from the nested search_attributes dict.

Product data structure (inside each item's search_attributes):
  name              — product name
  brand             — brand name (string)
  kind              — category: flower / vape / edible / extract / tincture / topical
  percent_thc       — THC % (float or None)
  bucket_price      — primary price for the listed weight
  available_weights — list of weight options (e.g. ["gram"], ["eighth ounce"])
  price_gram        — price per gram (if applicable)
  price_eighth_ounce / price_half_ounce / etc — weight-specific prices
  url_slug          — used to construct the product URL

URL construction:
  https://theflowershopusa.com/{location}/products/{url_slug}

Weight mapping (iHeartJane label → standard weight string):
  "gram"          → "1g"
  "half gram"     → "0.5g"
  "two gram"      → "2g"
  "eighth ounce"  → "3.5g"
  "quarter ounce" → "7g"
  "half ounce"    → "14g"
  "ounce"         → "28g"
  "each"          → "each"
"""

import logging
from typing import List, Optional

from playwright.async_api import async_playwright

from .base_scraper import BaseScraper, ScrapedProduct, ScrapedPromotion
from .registry import register_scraper

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Categories to scrape — matches iHeartJane kind values for this store
_KINDS = ["flower", "vape", "edible", "extract", "tincture", "topical"]

# Maps iHeartJane "kind" to our standard category labels
_CATEGORY_MAP = {
    "flower": "flower",
    "vape": "vape",
    "edible": "edible",
    "extract": "concentrate",
    "concentrate": "concentrate",
    "tincture": "tincture",
    "topical": "topical",
    "gear": "other",
}

# Maps iHeartJane available_weights labels to our standard weight strings
_WEIGHT_MAP = {
    "half gram": "0.5g",
    "gram": "1g",
    "two gram": "2g",
    "eighth ounce": "3.5g",
    "quarter ounce": "7g",
    "half ounce": "14g",
    "ounce": "28g",
    "each": "each",
}

# Maps iHeartJane weight labels to their price field names in search_attributes
_WEIGHT_PRICE_FIELDS = {
    "half gram": "price_half_gram",
    "gram": "price_gram",
    "two gram": "price_two_gram",
    "eighth ounce": "price_eighth_ounce",
    "quarter ounce": "price_quarter_ounce",
    "half ounce": "price_half_ounce",
    "ounce": "price_ounce",
    "each": "price_each",
}

# iHeartJane promotional/non-product items that should be filtered out
_PROMO_KEYWORDS = {"your first app order", "first time order", "app order discount"}


# ---------------------------------------------------------------------------
# Base scraper
# ---------------------------------------------------------------------------

class FlowerShopBaseScraper(BaseScraper):
    """
    Playwright-based scraper for The Flower Shop Utah dispensaries.

    Subclasses provide:
      - store_id        iHeartJane numeric store ID
      - location_slug   URL path segment (e.g. "logan" or "ogden")
      - location_name   Human-readable city name for logging
    """

    store_id: int
    location_slug: str  # "logan" or "ogden"
    location_name: str

    BASE_URL = "https://theflowershopusa.com"

    def __init__(self, dispensary_id: str):
        super().__init__(dispensary_id=dispensary_id)

    async def scrape_products(self) -> List[ScrapedProduct]:
        """
        Scrape all products by iterating over each iHeartJane kind/category.

        All category pages are navigated within a single Playwright page so that
        the browser session (cookies, device fingerprint) is preserved across
        requests — this ensures the dmerch.iheartjane.com/v2/multi API returns
        the full product list (83–119 per category) rather than the reduced
        first-page count that a cold browser session returns.
        """
        all_products: List[ScrapedProduct] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    )
                )
                page = await context.new_page()

                # Shared dict: current_kind → list of raw product dicts captured
                captured: dict = {}
                current_kind: list = [None]  # mutable cell for closure

                async def handle_response(response):
                    if "dmerch.iheartjane.com/v2/multi" not in response.url:
                        return
                    try:
                        data = await response.json()
                        for pl in data.get("placements", []):
                            # Only capture the per-category table — skip featured/top rows
                            if (
                                pl.get("placement") == "menu_inline_table"
                                and pl.get("products")
                                and current_kind[0]
                            ):
                                kind = current_kind[0]
                                captured.setdefault(kind, []).extend(pl["products"])
                    except Exception as exc:
                        logger.debug(
                            f"[{self.location_name}] Could not parse multi response: {exc}"
                        )

                page.on("response", handle_response)

                for kind in _KINDS:
                    current_kind[0] = kind
                    url = f"{self.BASE_URL}/{self.location_slug}/menu/{kind}"
                    try:
                        await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                    except Exception:
                        pass  # Timeout is fine — we just need the API response

                    await page.wait_for_timeout(5000)

                    kind_raw = captured.get(kind, [])
                    kind_products: List[ScrapedProduct] = []
                    for raw_item in kind_raw:
                        try:
                            parsed = self._parse_product(raw_item, kind)
                            kind_products.extend(parsed)
                        except Exception as exc:
                            logger.warning(
                                f"[{self.location_name}] Failed to parse product: {exc}",
                                exc_info=True,
                            )
                            continue

                    all_products.extend(kind_products)
                    logger.info(
                        f"[{self.location_name}] {kind}: {len(kind_products)} products"
                    )

                await page.close()

            finally:
                await browser.close()

        logger.info(
            f"[{self.location_name}] Total scraped: {len(all_products)} products"
        )
        return all_products

    def _parse_product(self, raw_item: dict, kind: str) -> List[ScrapedProduct]:
        """
        Parse all weight/price variants of a single product from dmerch search_attributes.

        iHeartJane products can be sold at multiple weights (e.g. 1g, 3.5g, 7g) each
        with a distinct price. The original implementation only captured the first
        available_weight; this version iterates all weights and returns one
        ScrapedProduct per weight option so the full price ladder is recorded.

        Args:
            raw_item: One element from the placements[*].products list.
            kind: The iHeartJane kind string for this category batch.

        Returns:
            List of ScrapedProducts (empty if data is incomplete or price is missing).
        """
        sa = raw_item.get("search_attributes", {})

        name = (sa.get("name") or "").strip()
        if not name:
            return []

        # Filter out promotional/non-product items from iHeartJane
        if name.lower() in _PROMO_KEYWORDS:
            return []

        brand = (sa.get("brand") or "").strip() or None
        category = _CATEGORY_MAP.get(sa.get("kind") or kind, "other")

        # THC percentage — guard against values >100 (mislabelled mg totals)
        thc_raw = sa.get("percent_thc")
        thc_pct: Optional[float] = None
        thc_content: Optional[str] = None
        if thc_raw is not None:
            try:
                v = float(thc_raw)
                if 0 <= v <= 100:
                    thc_pct = v
                    thc_content = f"{v:g}%"
            except (ValueError, TypeError):
                pass

        # Build product URL
        url_slug = sa.get("url_slug") or sa.get("searchable_slug") or ""
        product_url: Optional[str] = None
        if url_slug:
            product_url = (
                f"{self.BASE_URL}/{self.location_slug}/products/{url_slug}"
            )

        # Iterate all available weight options — each yields a separate price point.
        available_weights = sa.get("available_weights") or []
        products: List[ScrapedProduct] = []

        for weight_label in available_weights:
            weight_str = _WEIGHT_MAP.get(weight_label, weight_label) if weight_label else None

            # Prefer weight-specific price field, fall back to bucket_price
            price: float = 0.0
            if weight_label and weight_label in _WEIGHT_PRICE_FIELDS:
                field_name = _WEIGHT_PRICE_FIELDS[weight_label]
                price_raw = sa.get(field_name)
                if price_raw is not None:
                    try:
                        price = float(price_raw)
                    except (ValueError, TypeError):
                        pass

            if price == 0.0:
                bucket = sa.get("bucket_price")
                if bucket is not None:
                    try:
                        price = float(bucket)
                    except (ValueError, TypeError):
                        pass

            if price <= 0:
                continue  # Skip weight options with no usable price

            products.append(ScrapedProduct(
                name=name,
                brand=brand,
                category=category,
                thc_percentage=thc_pct,
                thc_content=thc_content,
                price=price,
                in_stock=True,
                weight=weight_str,
                url=product_url,
                raw_data=sa,
            ))

        # Fall back to bucket_price with no weight if available_weights is empty
        if not products:
            bucket = sa.get("bucket_price")
            if bucket is not None:
                try:
                    price = float(bucket)
                    if price > 0:
                        # Default to "each" for edibles/tinctures/topicals (unit-dosed products)
                        fallback_weight = (
                            "each"
                            if category in ("edible", "tincture", "topical")
                            else None
                        )
                        products.append(ScrapedProduct(
                            name=name,
                            brand=brand,
                            category=category,
                            thc_percentage=thc_pct,
                            thc_content=thc_content,
                            price=price,
                            in_stock=True,
                            weight=fallback_weight,
                            url=product_url,
                            raw_data=sa,
                        ))
                except (ValueError, TypeError):
                    pass

        return products

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        """Promotions not currently implemented for The Flower Shop."""
        return []


# ---------------------------------------------------------------------------
# Logan location
# ---------------------------------------------------------------------------

@register_scraper(
    id="flower-shop-logan",
    name="The Flower Shop (Logan)",
    dispensary_name="The Flower Shop Logan",
    dispensary_location="North Logan, UT",
    schedule_minutes=120,
    description=(
        "Playwright scraper for The Flower Shop Logan, UT "
        "(iHeartJane frameless embed; store_id=5150)"
    ),
)
class FlowerShopLoganScraper(FlowerShopBaseScraper):
    """The Flower Shop — North Logan, Utah (2150 N Main, Suite 1)."""

    store_id = 5150
    location_slug = "logan"
    location_name = "The Flower Shop Logan"

    def __init__(self, dispensary_id: str = "flower-shop-logan"):
        super().__init__(dispensary_id=dispensary_id)


# ---------------------------------------------------------------------------
# Ogden location
# ---------------------------------------------------------------------------

@register_scraper(
    id="flower-shop-ogden",
    name="The Flower Shop (Ogden)",
    dispensary_name="The Flower Shop Ogden",
    dispensary_location="South Ogden, UT",
    schedule_minutes=120,
    description=(
        "Playwright scraper for The Flower Shop Ogden, UT "
        "(iHeartJane frameless embed; store_id=5151)"
    ),
)
class FlowerShopOgdenScraper(FlowerShopBaseScraper):
    """The Flower Shop — South Ogden, Utah (3775 S Wall Ave)."""

    store_id = 5151
    location_slug = "ogden"
    location_name = "The Flower Shop Ogden"

    def __init__(self, dispensary_id: str = "flower-shop-ogden"):
        super().__init__(dispensary_id=dispensary_id)

"""
Curaleaf Park City Scraper — SweedPOS Platform

Curaleaf Park City (1351 Kearns Blvd STE 110-B, Park City, UT 84060) operates
a custom Next.js storefront at:
  https://ut.curaleaf.com/shop/utah/curaleaf-ut-wellness-park

Unlike the other Curaleaf Utah locations (Lehi, Provo, Springville) which use
the ut.curaleaf.com/stores/ path with Dutchie, Park City uses a different URL
pattern (/shop/utah/) and is backed by SweedPOS.

The storefront calls SweedPOS's proxy API:
  https://web-ui-curaleaf.sweedpos.com/_api/proxy/Products/GetProductList

The API requires a store session established via browser cookies (specifically
last_store and confirmed21OrOlder). We use Playwright to:
1. Navigate to the age gate and confirm age (sets required cookies)
2. Navigate to each category page, which triggers GetProductList API calls
3. Intercept those API responses via page.on("response", ...) and parse products
4. Click "Show more" buttons to load all pages (24 products per page)

Category IDs (from GetProductCategoryList, store 165):
  1854 - Flower
  1863 - Vape
  1861 - Concentrates
  1855 - Edibles
  1857 - Beverage
  1858 - Oral (capsules / tinctures)
  1856 - Topical
  1859 - Accessories (hardware)
"""
import logging
import re
from typing import List, Dict, Optional, Any

from .base_scraper import BaseScraper, ScrapedProduct, ScrapedPromotion
from .registry import register_scraper

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category config: (category_id, url_slug, standard_category)
# ---------------------------------------------------------------------------
_CATEGORIES = [
    (1854, "flower-1854",         "flower"),
    (1863, "vape-1863",           "vape"),
    (1861, "concentrates-1861",   "concentrate"),
    (1855, "edibles-1855",        "edible"),
    (1857, "beverage-1857",       "edible"),      # beverages are edibles
    (1858, "oral-1858",           "tincture"),    # capsules/tinctures
    (1856, "topical-1856",        "topical"),
    (1859, "accessories-1859",    "hardware"),
]

_STORE_URL = "https://ut.curaleaf.com/shop/utah/curaleaf-ut-wellness-park"
_BASE_PRODUCT_URL = _STORE_URL + "/menu"
_SWEEDPOS_API_MARKER = "GetProductList"

# Static file extensions to skip in response listener
_STATIC_EXTS = (
    ".js", ".css", ".png", ".jpg", ".jpeg", ".gif",
    ".svg", ".ico", ".woff", ".woff2", ".ttf", ".map",
)

# ---------------------------------------------------------------------------
# Category name -> standard name fallback map
# ---------------------------------------------------------------------------
_CATEGORY_MAP: Dict[str, str] = {
    "flower":       "flower",
    "vape":         "vape",
    "vaporizer":    "vape",
    "cartridge":    "vape",
    "concentrates": "concentrate",
    "concentrate":  "concentrate",
    "extract":      "concentrate",
    "edibles":      "edible",
    "edible":       "edible",
    "beverage":     "edible",
    "beverages":    "edible",
    "oral":         "tincture",
    "tincture":     "tincture",
    "tinctures":    "tincture",
    "capsules":     "tincture",
    "topical":      "topical",
    "topicals":     "topical",
    "accessories":  "hardware",
    "hardware":     "hardware",
    "pre-roll":     "pre-roll",
    "pre-rolls":    "pre-roll",
    "preroll":      "pre-roll",
}

_WEIGHT_FROM_NAME_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(g|oz|mg|ml)\b", re.IGNORECASE
)


def _map_category(raw_name: Optional[str], fallback: str = "other") -> str:
    if not raw_name:
        return fallback
    return _CATEGORY_MAP.get(raw_name.strip().lower(), fallback)


def _parse_weight(variant: Dict[str, Any], product_name: str) -> Optional[str]:
    """Extract weight from variant unitSize or fall back to product name parsing."""
    unit_size = variant.get("unitSize")
    if unit_size:
        val = unit_size.get("value")
        abbr = (unit_size.get("unitAbbr") or "g").lower()
        if val is not None:
            return f"{val}{abbr}"
    # Try parsing from variant name (e.g., "3.5g | 251208HA")
    vname = variant.get("name", "")
    m = _WEIGHT_FROM_NAME_RE.search(vname) or _WEIGHT_FROM_NAME_RE.search(product_name)
    if m:
        return f"{m.group(1)}{m.group(2).lower()}"
    return None


def _parse_thc(
    lab_tests: Optional[Dict[str, Any]]
) -> tuple[Optional[float], Optional[str]]:
    """Return (thc_percentage, thc_content_string) from labTests dict."""
    if not lab_tests:
        return None, None
    thc = lab_tests.get("thc")
    if not thc:
        display = lab_tests.get("displayThc")
        if display:
            return None, str(display)
        return None, None
    values = thc.get("value") or []
    unit = (thc.get("unitAbbr") or "").lower()
    if not values:
        return None, None
    val = values[0] if isinstance(values, list) else values
    try:
        pct = float(val)
    except (TypeError, ValueError):
        return None, None
    # Guard against mislabelled mg-as-% values (>100)
    if unit == "%" and pct <= 100:
        return round(pct, 2), f"{pct}%"
    if unit == "mg":
        return None, f"{pct} mg"
    return None, None


def _parse_cbd(
    lab_tests: Optional[Dict[str, Any]]
) -> tuple[Optional[float], Optional[str]]:
    """Return (cbd_percentage, cbd_content_string) from labTests dict."""
    if not lab_tests:
        return None, None
    cbd = lab_tests.get("cbd")
    if not cbd:
        return None, None
    values = cbd.get("value") or []
    unit = (cbd.get("unitAbbr") or "").lower()
    if not values:
        return None, None
    val = values[0] if isinstance(values, list) else values
    try:
        pct = float(val)
    except (TypeError, ValueError):
        return None, None
    if unit == "%" and pct <= 100:
        return round(pct, 2), f"{pct}%"
    if unit == "mg":
        return None, f"{pct} mg"
    return None, None


@register_scraper(
    id="curaleaf-park-city",
    name="Curaleaf Utah - Park City",
    dispensary_name="Curaleaf Park City",
    dispensary_location="Park City, UT",
    schedule_minutes=120,
    description=(
        "Playwright scraper for Curaleaf Park City (SweedPOS platform). "
        "Menu at https://ut.curaleaf.com/shop/utah/curaleaf-ut-wellness-park"
    ),
)
class CuraleafParkCityScraper(BaseScraper):
    """
    Scraper for Curaleaf Park City — SweedPOS-backed storefront.

    Unlike Lehi/Provo/Springville (which use the /stores/ path with Dutchie),
    Park City uses /shop/utah/ and is powered by SweedPOS.  We use Playwright
    to navigate each category page and intercept the GetProductList API calls
    via page.on("response", ...).
    """

    def __init__(self, dispensary_id: str = "curaleaf-park-city"):
        super().__init__(dispensary_id=dispensary_id)

    async def _dismiss_age_gate(self, page) -> None:
        """
        Dismiss the Curaleaf age gate (full-page redirect pattern).

        The age gate redirects every URL to /age-gate?returnurl=... and renders
        an 'I'm over 18' button client-side.  We navigate directly to the gate,
        wait for full hydration, then click the button.
        """
        from urllib.parse import quote

        age_gate_url = (
            f"https://ut.curaleaf.com/age-gate"
            f"?returnurl={quote(_STORE_URL, safe='')}"
        )
        logger.info("Dismissing age gate: %s", age_gate_url)
        await page.goto(age_gate_url, wait_until="networkidle", timeout=30_000)
        await page.wait_for_timeout(2_000)

        for selector in [
            'button:has-text("I\'m over 18")',
            'button:has-text("I am over 18")',
            'button:has-text("Yes")',
            'button:has-text("Enter")',
        ]:
            try:
                btn = await page.wait_for_selector(selector, timeout=5_000)
                if btn and await btn.is_visible():
                    await btn.click()
                    await page.wait_for_timeout(2_000)
                    if "age-gate" not in page.url:
                        logger.info("Age gate dismissed — now on: %s", page.url)
                        return
            except Exception:
                continue

        logger.warning("Could not dismiss age gate; scraping may fail.")

    async def _scroll_to_load_all(self, page, max_scrolls: int = 30) -> None:
        """Scroll the page repeatedly to trigger scroll-based lazy loading."""
        prev_height = 0
        for _ in range(max_scrolls):
            height = await page.evaluate("() => document.body.scrollHeight")
            if height == prev_height:
                break
            prev_height = height
            await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1_500)

    def _parse_product(
        self, raw: Dict[str, Any], standard_cat: str
    ) -> List[ScrapedProduct]:
        """
        Convert one SweedPOS product record into one ScrapedProduct per variant.

        Each variant has its own price, weight, and lab tests.
        """
        name = (raw.get("name") or "").strip()
        if not name:
            return []

        brand_obj = raw.get("brand") or {}
        brand = (brand_obj.get("name") or "").strip() or None

        # Category from raw data (fallback to the standard_cat passed in)
        cat_obj = raw.get("category") or {}
        category = _map_category(cat_obj.get("name"), fallback=standard_cat)

        variants = raw.get("variants") or []
        if not variants:
            return []

        results: List[ScrapedProduct] = []

        for variant in variants:
            try:
                price = variant.get("price")
                promo_price = variant.get("promoPrice")
                if price is None:
                    continue
                try:
                    price_val = float(promo_price if promo_price else price)
                except (TypeError, ValueError):
                    continue
                if price_val <= 0:
                    continue

                weight = _parse_weight(variant, name)

                lab_tests = variant.get("labTests")
                thc_pct, thc_content = _parse_thc(lab_tests)
                cbd_pct, cbd_content = _parse_cbd(lab_tests)

                avail_qty = variant.get("availableQty") or 0
                in_stock = avail_qty > 0

                # Build product URL from product name slug + variant id
                product_id = raw.get("id")
                variant_id = variant.get("id")
                if product_id and variant_id:
                    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
                    cat_id = cat_obj.get("id", "")
                    product_url = f"{_BASE_PRODUCT_URL}/{cat_id}/{slug}-{variant_id}"
                else:
                    product_url = _BASE_PRODUCT_URL

                results.append(
                    ScrapedProduct(
                        name=name,
                        brand=brand,
                        category=category,
                        price=price_val,
                        weight=weight,
                        thc_percentage=thc_pct,
                        cbd_percentage=cbd_pct,
                        thc_content=thc_content,
                        cbd_content=cbd_content,
                        in_stock=in_stock,
                        url=product_url,
                        raw_data={
                            **raw,
                            "_variant_id": variant_id,
                            "_variant_name": (variant.get("name") or "").strip(),
                        },
                    )
                )
            except Exception as exc:
                logger.debug("Error parsing variant in %s: %s", name, exc)
                continue

        return results

    async def _fetch_all_category_pages(
        self,
        page,
        cat_slug: str,
        standard_cat: str,
    ) -> List[ScrapedProduct]:
        """
        Fetch all paginated pages for one SweedPOS category.

        SweedPOS uses ?page=N URL parameters for pagination (24 items per page).
        We navigate to each page in sequence until we have retrieved all items,
        using the Playwright response listener to capture API responses.

        Returns a deduplicated list of ScrapedProduct objects.
        """
        captured_for_cat: Dict[int, Any] = {}  # page_num -> API response data

        async def handle_response(response) -> None:
            """Temporary response listener for this category's pages."""
            if _SWEEDPOS_API_MARKER not in response.url:
                return
            if response.status == 200:
                try:
                    data = await response.json()
                    page_num = data.get("page", 1)
                    captured_for_cat[page_num] = data
                    logger.debug(
                        "Captured page %d: %d items (total=%d)",
                        page_num,
                        len(data.get("list") or []),
                        data.get("total", 0),
                    )
                except Exception as exc:
                    logger.debug("JSON parse error for %s: %s", response.url[:80], exc)

        page.on("response", handle_response)
        try:
            # Page 1
            base_url = f"{_STORE_URL}/menu/{cat_slug}"
            try:
                await page.goto(
                    base_url + "?page=1",
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )
            except Exception as exc:
                logger.warning("Navigation failed for %s: %s", base_url, exc)
                return []

            await page.wait_for_timeout(3_000)

            if 1 not in captured_for_cat:
                logger.warning("No API response for %s page 1", cat_slug)
                return []

            total = captured_for_cat[1].get("total") or 0
            page_size = captured_for_cat[1].get("pageSize") or 24
            total_pages = max(1, -(-total // page_size))  # ceiling division

            logger.info(
                "Category %s: total=%d items across %d page(s)",
                cat_slug, total, total_pages
            )

            # Fetch remaining pages
            for page_num in range(2, total_pages + 1):
                if page_num in captured_for_cat:
                    continue
                try:
                    await page.goto(
                        f"{base_url}?page={page_num}",
                        wait_until="domcontentloaded",
                        timeout=30_000,
                    )
                    await page.wait_for_timeout(2_000)
                except Exception as exc:
                    logger.warning(
                        "Navigation failed for %s page %d: %s",
                        cat_slug, page_num, exc
                    )

        finally:
            page.remove_listener("response", handle_response)

        # Parse products from all captured pages
        products: List[ScrapedProduct] = []
        seen_variant_ids: set = set()

        for page_num in sorted(captured_for_cat.keys()):
            data = captured_for_cat[page_num]
            for raw in (data.get("list") or []):
                try:
                    for scraped in self._parse_product(raw, standard_cat):
                        vid = scraped.raw_data.get("_variant_id")
                        if vid and vid in seen_variant_ids:
                            continue
                        if vid:
                            seen_variant_ids.add(vid)
                        products.append(scraped)
                except Exception as exc:
                    logger.debug("Error parsing product %s: %s", raw.get("id"), exc)

        logger.info(
            "Category %s: parsed %d variant products from %d/%d pages",
            cat_slug, len(products), len(captured_for_cat), total_pages
        )
        return products

    async def scrape_products(self) -> List[ScrapedProduct]:
        """
        Scrape all products from Curaleaf Park City (SweedPOS storefront).

        Strategy:
        1. Open browser, dismiss age gate (sets confirmed21OrOlder + last_store cookies).
        2. For each category, iterate through all pages using ?page=N URL parameters.
        3. Capture SweedPOS GetProductList API responses via page.on("response", ...).
        4. Parse products from captured responses.

        SweedPOS returns 24 products per page with a total count; we compute the
        page count from total/pageSize and fetch each page in sequence.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright is required: pip install playwright && "
                "playwright install chromium"
            )

        all_products: List[ScrapedProduct] = []

        logger.info("Starting Curaleaf Park City scrape (%s)", _STORE_URL)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()
            page.set_default_timeout(60_000)

            try:
                # Step 1: Dismiss age gate (sets confirmed21OrOlder + last_store cookies)
                await self._dismiss_age_gate(page)

                # Step 2: Scrape each category with pagination
                for cat_id, cat_slug, standard_cat in _CATEGORIES:
                    logger.info(
                        "Scraping category %s (%s, id=%d)",
                        cat_slug, standard_cat, cat_id
                    )
                    try:
                        category_products = await self._fetch_all_category_pages(
                            page, cat_slug, standard_cat
                        )
                        all_products.extend(category_products)
                    except Exception as exc:
                        logger.warning(
                            "Error scraping category %s: %s", cat_slug, exc
                        )
                        continue

            except Exception as exc:
                logger.error(
                    "Fatal error scraping Curaleaf Park City: %s", exc, exc_info=True
                )
                raise
            finally:
                await browser.close()

        logger.info(
            "Curaleaf Park City: scraped %d products total", len(all_products)
        )
        return all_products

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        """Promotions not currently implemented for Curaleaf Park City."""
        return []

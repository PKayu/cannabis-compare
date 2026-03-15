"""
Beehive Farmacy Scraper — Dutchie Platform

Both the Salt Lake City and Brigham City locations use Dutchie's white-label
Next.js storefront (brigham-city.beehivefarmacy.com / shop.beehivefarmacy.com).

Products are loaded entirely client-side via Dutchie's internal API.  We use
Playwright to load the page and extract products via three complementary
strategies (tried in order):

  1. JS fetch interception — patches window.fetch before page load so every
     fetch response is stored in window.__dutchieCaptures.
  2. Playwright response listener — page.on("response") captures any JSON
     response from any domain (not just api.dutchie.com).
  3. DOM extraction fallback — page.evaluate() walks the rendered DOM using
     multiple selector strategies to extract product card text.

Key identifiers (from window.reactEnv embedded in each store's HTML):
  Brigham City  retailerId=d77367be-fce5-40fe-8355-19e813df168e
  Salt Lake City retailerId=65750558-290d-4db4-908b-ad20124bf2ab

Architecture:
  BeehiveFarmacyBaseScraper  — all scraping + parsing logic; store_url is the
                                only thing subclasses override
  BeehiveFarmacyBrighamScraper  — Brigham City (registered as "beehive-brigham-city")
  BeehiveFarmacySLCScraper      — Salt Lake City  (registered as "beehive-slc")
"""
import logging
import re
from typing import List, Any, Dict, Optional

from .base_scraper import BaseScraper, ScrapedProduct, ScrapedPromotion
from .registry import register_scraper

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dutchie → standard category mapping
# ---------------------------------------------------------------------------
_CATEGORY_MAP: Dict[str, str] = {
    "flower": "flower",
    "pre-rolls": "pre-roll",
    "pre-roll": "pre-roll",
    "pre_roll": "pre-roll",
    "preroll": "pre-roll",
    "pre rolls": "pre-roll",
    "vaporizers": "vape",
    "vaporizer": "vape",
    "vape": "vape",
    "cartridge": "vape",
    "cartridges": "vape",
    "edibles": "edible",
    "edible": "edible",
    "concentrates": "concentrate",
    "concentrate": "concentrate",
    "extract": "concentrate",
    "extracts": "concentrate",
    "tinctures": "tincture",
    "tincture": "tincture",
    "topicals": "topical",
    "topical": "topical",
    "accessories": "hardware",
    "hardware": "hardware",
    "gear": "hardware",
}

# JS injected before page load — patches window.fetch to capture all responses
_FETCH_INTERCEPT_SCRIPT = """
window.__dutchieCaptures = [];
(function() {
    var _orig = window.fetch;
    window.fetch = function(resource, init) {
        return _orig.apply(this, arguments).then(function(resp) {
            var clone = resp.clone();
            var url = typeof resource === 'string' ? resource :
                      (resource && resource.url ? resource.url : String(resource));
            clone.json().then(function(data) {
                window.__dutchieCaptures.push({url: url, data: data, status: resp.status});
            }).catch(function() {});
            return resp;
        });
    };
})();
"""

# JS run after page loads — extracts products from the rendered DOM.
# Tries Dutchie-specific selectors first, then falls back to price-text heuristics.
_DOM_EXTRACT_SCRIPT = """
() => {
    var results = {
        products: [],
        diagnostics: { title: document.title, selectorCounts: {}, usedSelector: null }
    };

    // Selector candidates for Dutchie product cards (most specific first)
    var cardSelectors = [
        '[data-testid="product-card"]',
        '[data-testid="menu-product-card"]',
        '[data-testid*="product-card"]',
        '[data-testid*="productCard"]',
        '[class*="product-card"]',
        '[class*="ProductCard"]',
        '[class*="menu-product-card"]',
        '[class*="MenuProductCard"]',
        '[class*="product-item"]',
        '[class*="ProductItem"]',
        '[class*="productItem"]',
    ];

    var cards = [];
    for (var i = 0; i < cardSelectors.length; i++) {
        var sel = cardSelectors[i];
        var found = document.querySelectorAll(sel);
        results.diagnostics.selectorCounts[sel] = found.length;
        if (found.length > 0 && cards.length === 0) {
            cards = Array.from(found);
            results.diagnostics.usedSelector = sel;
        }
    }

    // Fallback: find any element containing a price pattern with children
    if (cards.length === 0) {
        results.diagnostics.usedSelector = 'price-heuristic';
        var allEls = document.querySelectorAll('div, li, article');
        var priceRe = /\\$\\d+(\\.\\d{2})?/;
        for (var j = 0; j < allEls.length && cards.length < 300; j++) {
            var el = allEls[j];
            if (priceRe.test(el.textContent) && el.children.length >= 2 && el.children.length <= 15) {
                cards.push(el);
            }
        }
        results.diagnostics.selectorCounts['price-heuristic'] = cards.length;
    }

    results.diagnostics.cardsFound = cards.length;

    // Extract data from each card
    var seen = {};
    for (var k = 0; k < Math.min(cards.length, 500); k++) {
        var card = cards[k];
        try {
            var text = (card.textContent || '').replace(/\\s+/g, ' ').trim();
            if (!text || text.length < 10) continue;

            // Must have a price
            var priceMatch = text.match(/\\$(\\d+(?:\\.\\d{1,2})?)/);
            if (!priceMatch) continue;

            // Dedup by text prefix (first 80 chars)
            var key = text.substring(0, 80);
            if (seen[key]) continue;
            seen[key] = true;

            // Product URL from first anchor pointing to a product page
            var linkEl = card.querySelector('a[href*="product"]') || card.querySelector('a[href]');
            var url = null;
            if (linkEl && linkEl.href) {
                url = linkEl.href;
                if (!url.startsWith('http')) {
                    try { url = new URL(url, window.location.origin).href; } catch(e) {}
                }
            }

            // Sub-elements — try Dutchie data-testid sub-selectors
            var nameEl = card.querySelector('[data-testid*="name"], [data-testid*="title"], h1, h2, h3, h4');
            var brandEl = card.querySelector('[data-testid*="brand"]');
            var priceEl = card.querySelector('[data-testid*="price"], [data-testid*="Price"]');
            var weightEl = card.querySelector('[data-testid*="weight"], [data-testid*="size"]');

            results.products.push({
                fullText: text.substring(0, 500),
                url: url,
                price: priceMatch[1],
                nameText: nameEl ? (nameEl.textContent || '').trim() : null,
                brandText: brandEl ? (brandEl.textContent || '').trim() : null,
                priceText: priceEl ? (priceEl.textContent || '').trim() : null,
                weightText: weightEl ? (weightEl.textContent || '').trim() : null,
            });
        } catch(e) {}
    }

    return results;
}
"""


class BeehiveFarmacyBaseScraper(BaseScraper):
    """
    Scraper base for Beehive Farmacy Dutchie storefronts.

    Subclasses set `store_url` and register themselves with @register_scraper.
    """

    store_url: str = ""  # Overridden by each location subclass

    # Standard Dutchie embedded-menu categories — subclasses can use these
    # in _get_urls_to_scrape() to iterate over category pages.
    DUTCHIE_CATEGORIES: List[str] = [
        "flower",
        "pre-rolls",
        "vaporizers",
        "edibles",
        "concentrates",
        "tinctures",
        "topicals",
        "accessories",
    ]

    def __init__(self, dispensary_id: str):
        super().__init__(dispensary_id=dispensary_id)

    def _get_urls_to_scrape(self) -> List[str]:
        """Return the list of URLs to scrape.

        Default: single store URL.  Subclasses can override to return
        per-category URLs for Dutchie embedded menus that don't load all
        products on a single page.
        """
        return [self.store_url]

    async def scrape_products(self) -> List[ScrapedProduct]:
        """
        Scrape all products from a Beehive Farmacy Dutchie storefront.

        Strategy (three layers, in order):
        1. JS fetch interception — patches window.fetch via addInitScript so
           every API response is stored in window.__dutchieCaptures.  This
           works even if Playwright's response listener misses calls.
        2. Playwright response listener — captures any JSON response from any
           domain.  Logging all non-static URLs helps diagnose domain changes.
        3. DOM extraction fallback — if neither network approach yields
           products, page.evaluate() walks the rendered DOM using Dutchie-
           specific data-testid selectors + price-text heuristics.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise ImportError(
                "Playwright is required: pip install playwright && "
                "playwright install chromium"
            )

        urls_to_scrape = self._get_urls_to_scrape()

        # Accumulates captures from Playwright response listener and JS fetch patch
        network_captured: List[Dict[str, Any]] = []
        js_captured: List[Dict[str, Any]] = []
        dom_result: Optional[Dict[str, Any]] = None

        logger.info(
            f"Scraping Dutchie store ({self.store_url}) — "
            f"{len(urls_to_scrape)} URL(s) to visit"
        )

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

            # --- Layer 1: patch window.fetch before any JS runs ---------------
            await page.add_init_script(_FETCH_INTERCEPT_SCRIPT)

            # --- Layer 2: Playwright response listener (any JSON) -------------
            _static_exts = (
                ".js", ".css", ".png", ".jpg", ".jpeg", ".gif",
                ".svg", ".ico", ".woff", ".woff2", ".ttf", ".map",
            )

            async def handle_response(response) -> None:
                url = response.url
                if any(url.split("?")[0].endswith(ext) for ext in _static_exts):
                    return
                if response.status != 200:
                    return
                ct = response.headers.get("content-type", "")
                if "json" not in ct:
                    return
                try:
                    data = await response.json()
                    network_captured.append({"url": url, "data": data})
                    logger.info(f"Network JSON: {url[:150]}")
                except Exception as exc:
                    logger.debug(f"Could not parse JSON from {url}: {exc}")

            page.on("response", handle_response)

            try:
                age_gate_dismissed = False

                for url_idx, scrape_url in enumerate(urls_to_scrape):
                    logger.info(
                        f"Navigating to URL {url_idx + 1}/{len(urls_to_scrape)}: "
                        f"{scrape_url}"
                    )

                    # Clear JS captures before each navigation to avoid
                    # double-counting responses from a previous page.
                    if url_idx > 0:
                        await page.evaluate(
                            "() => { window.__dutchieCaptures = []; }"
                        )

                    try:
                        await page.goto(
                            scrape_url,
                            wait_until="domcontentloaded",
                            timeout=60_000,
                        )
                    except Exception as nav_exc:
                        logger.warning(
                            f"Failed to navigate to {scrape_url}: {nav_exc} "
                            "— skipping"
                        )
                        continue

                    await page.wait_for_timeout(3_000)

                    # Dismiss age gate only on the first successful page load;
                    # Dutchie persists the verification in the browser context.
                    if not age_gate_dismissed:
                        await self._dismiss_age_gate(page)
                        age_gate_dismissed = True

                    # Wait until JS fetch interception has captured at least one
                    # response OR fall through after 15s.
                    try:
                        await page.wait_for_function(
                            "() => window.__dutchieCaptures && "
                            "window.__dutchieCaptures.length > 0",
                            timeout=15_000,
                        )
                        logger.info("JS captures arrived — proceeding to scroll")
                    except Exception:
                        logger.warning(
                            "No JS captures within 15s; proceeding anyway "
                            "(may rely on network listener or DOM fallback)"
                        )

                    await self._scroll_to_load_all(page)
                    await page.wait_for_timeout(2_000)

                    # --- Read JS-captured fetch responses for this URL --------
                    js_raw = await page.evaluate(
                        "() => window.__dutchieCaptures || []"
                    )
                    logger.info(
                        f"URL {url_idx + 1}: JS fetch interception captured "
                        f"{len(js_raw)} responses"
                    )
                    js_captured.extend(
                        {"url": item.get("url", ""), "data": item.get("data", {})}
                        for item in (js_raw or [])
                    )

                # --- DOM fallback if no API responses found -------------------
                all_captured = js_captured + network_captured
                logger.info(
                    f"Combined captures: {len(js_captured)} JS + "
                    f"{len(network_captured)} network = {len(all_captured)} total"
                )

                if not all_captured:
                    logger.info(
                        "No API responses — running DOM extraction fallback"
                    )
                    dom_result = await page.evaluate(_DOM_EXTRACT_SCRIPT)
                    logger.info(
                        f"DOM extraction: selector={dom_result.get('diagnostics', {}).get('usedSelector')}, "
                        f"cards={dom_result.get('diagnostics', {}).get('cardsFound', 0)}, "
                        f"products={len(dom_result.get('products', []))}"
                    )
                    logger.debug(
                        f"DOM selector counts: "
                        f"{dom_result.get('diagnostics', {}).get('selectorCounts', {})}"
                    )

            except Exception as e:
                logger.error(
                    f"Error loading Dutchie page: {e}", exc_info=True
                )
                raise
            finally:
                await browser.close()

        # -----------------------------------------------------------------------
        # Parse results
        # -----------------------------------------------------------------------
        all_captured = js_captured + network_captured

        if all_captured:
            logger.info(f"Parsing {len(all_captured)} captured API responses")
            all_products: List[ScrapedProduct] = []
            for item in all_captured:
                parsed = self._parse_dutchie_response(item["data"])
                if parsed:
                    logger.debug(
                        f"  {len(parsed)} products from {item['url'][:100]}"
                    )
                all_products.extend(parsed)

        elif dom_result is not None:
            logger.info("Parsing DOM extraction results")
            all_products = self._parse_dom_products(dom_result.get("products", []))

        else:
            logger.warning("No data captured from any source")
            all_products = []

        # Deduplicate by (name, price)
        seen: set = set()
        unique: List[ScrapedProduct] = []
        for product in all_products:
            key = (product.name.lower().strip(), product.price)
            if key not in seen:
                seen.add(key)
                unique.append(product)

        logger.info(
            f"Scraped {len(unique)} unique products from Dutchie store "
            f"({self.store_url})"
        )
        return unique

    # -----------------------------------------------------------------------
    # Age gate & scroll helpers
    # -----------------------------------------------------------------------

    async def _dismiss_age_gate(self, page: Any) -> None:
        """Click through Dutchie's age verification modal if present."""
        logger.info("Checking for age gate...")

        selectors = [
            'button:has-text("I\'m 21+")',
            'button:has-text("I am 21+")',
            'button:has-text("Yes, I\'m 21 or older")',
            'button:has-text("Yes, I am 21 or older")',
            'button:has-text("Yes, I\'m of legal age")',
            'button:has-text("I\'m of legal age")',
            'button:has-text("Confirm")',
            'button:has-text("Enter")',
            '[data-testid="age-gate-confirm"]',
            '[data-testid*="age"] button',
            '[data-testid*="verify"] button',
        ]

        for selector in selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=2_000)
                if button:
                    logger.info(f"Dismissing age gate: {selector}")
                    await button.click()
                    await page.wait_for_timeout(3_000)
                    return
            except Exception:
                continue

        logger.info("No age gate found (or already dismissed)")

    async def _scroll_to_load_all(self, page: Any) -> None:
        """Scroll until page height stabilises (lazy-load trigger)."""
        logger.info("Scrolling to load all products...")

        prev_height = 0
        stable_rounds = 0

        for attempt in range(20):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2_000)

            height = await page.evaluate("document.body.scrollHeight")
            logger.debug(f"Scroll {attempt + 1}: height={height}px")

            if height == prev_height:
                stable_rounds += 1
                if stable_rounds >= 2:
                    logger.info(f"Page stabilized at {height}px")
                    break
            else:
                stable_rounds = 0

            prev_height = height

        logger.info("Finished scrolling")

    # -----------------------------------------------------------------------
    # Dutchie JSON parsing (used when network/JS interception succeeds)
    # -----------------------------------------------------------------------

    def _parse_dutchie_response(self, data: Any) -> List[ScrapedProduct]:
        """
        Parse a captured Dutchie JSON payload into ScrapedProducts.

        Tries multiple known response shapes:
          GraphQL: {"data": {"filteredProducts": {"products": [...]}}}
          GraphQL: {"data": {"menu": {"products": [...]}}}
          REST v1: {"products": [...]}
          REST v2: {"items": [...]} / {"results": [...]}
        """
        raw_list: List[Any] = []

        if not isinstance(data, dict):
            return []

        # GraphQL envelope
        if "data" in data and isinstance(data["data"], dict):
            gql = data["data"]
            for outer in ("filteredProducts", "menu", "products", "menuProducts"):
                if outer in gql:
                    inner = gql[outer]
                    if isinstance(inner, list):
                        raw_list = inner
                    elif isinstance(inner, dict):
                        raw_list = (
                            inner.get("products")
                            or inner.get("items")
                            or inner.get("results")
                            or []
                        )
                    if raw_list:
                        break

        # Flat REST shapes
        if not raw_list:
            for key in ("products", "items", "results", "data"):
                candidate = data.get(key)
                if isinstance(candidate, list) and candidate:
                    raw_list = candidate
                    break

        if not raw_list:
            return []

        # Log structure of first item to aid debugging if parsing fails
        if raw_list:
            sample = raw_list[0]
            if isinstance(sample, dict):
                logger.debug(
                    f"Product schema sample keys: {list(sample.keys())[:15]}"
                )

        products: List[ScrapedProduct] = []
        for item in raw_list:
            try:
                products.extend(self._parse_dutchie_product(item))
            except Exception as exc:
                logger.warning(
                    f"Failed to parse Dutchie product: {exc}", exc_info=True
                )
        return products

    def _parse_dutchie_product(self, item: Any) -> List[ScrapedProduct]:
        """
        Convert a single Dutchie product dict → one ScrapedProduct per weight option.

        Handles three known schemas:
          Actual Dutchie API:  Name/Prices/Options/THCContent/CBDContent/cName/Status
          Dutchie v2 GraphQL:  name/variants[]{priceMed,option}/potencyThc/potencyCbd
          Legacy REST:         name/prices[]{price,unit,unitQuantity}
        Returns an empty list (never None) so callers can safely use extend().
        """
        if not isinstance(item, dict):
            return []

        # --- Name ------------------------------------------------------------
        name = item.get("name") or item.get("Name")
        if not name or not str(name).strip():
            return []
        name = str(name).strip()

        # --- Brand -----------------------------------------------------------
        brand_name_flat = item.get("brandName") or ""
        brand_raw = item.get("brand") or item.get("Brand")
        if isinstance(brand_name_flat, str) and brand_name_flat.strip():
            brand: str = brand_name_flat.strip()
        elif isinstance(brand_raw, dict):
            brand = brand_raw.get("name") or brand_raw.get("Name") or "Unknown"
        elif isinstance(brand_raw, str) and brand_raw.strip():
            brand = brand_raw.strip()
        else:
            brand = "Unknown"

        # --- Category --------------------------------------------------------
        raw_cat = (
            item.get("category")
            or item.get("Category")
            or item.get("type")
            or item.get("productType")
            or "other"
        )
        category = _CATEGORY_MAP.get(str(raw_cat).lower().strip(), "other")

        # --- Potency ---------------------------------------------------------
        thc_pct: Optional[float] = None
        thc_content: Optional[str] = None
        cbd_pct: Optional[float] = None
        cbd_content: Optional[str] = None

        for potency_raw, is_thc in (
            # Actual Dutchie API uses THCContent/CBDContent (capital).
            # Older GraphQL uses potencyThc/potencyCbd.
            (
                item.get("THCContent") or item.get("potencyThc") or item.get("thcContent"),
                True,
            ),
            (
                item.get("CBDContent") or item.get("potencyCbd") or item.get("cbdContent"),
                False,
            ),
        ):
            if not isinstance(potency_raw, dict):
                continue

            unit_str = str(potency_raw.get("unit", "")).upper()
            formatted = potency_raw.get("formatted") or potency_raw.get("value", "")
            is_pct = unit_str == "PERCENTAGE" or "%" in str(formatted)

            # Extract numeric value from range list, percentage key, or value key
            rng = potency_raw.get("range")
            raw_val = None
            if rng and isinstance(rng, list):
                # Skip None entries: e.g. range=[None]
                numeric = [x for x in rng if x is not None]
                if numeric:
                    raw_val = numeric[0]
            if raw_val is None:
                raw_val = potency_raw.get("percentage") or potency_raw.get("value")
            if raw_val is None and formatted:
                m = re.search(r"(\d+\.?\d*)", str(formatted))
                if m:
                    raw_val = m.group(1)

            if raw_val is not None:
                try:
                    v = float(raw_val)
                    # Guard: Dutchie occasionally returns mg totals (e.g. 118 mg
                    # for a 10-pack edible) with unit="PERCENTAGE" — a data error.
                    # Any value >100 cannot be a valid percentage.
                    if is_pct and v <= 100:
                        display = f"{v}%"
                        if is_thc:
                            thc_pct = v
                            thc_content = display
                        else:
                            cbd_pct = v
                            cbd_content = display
                    else:
                        # mg (or out-of-range "percentage" — store as mg content)
                        mg_display = f"{v} mg"
                        if is_thc:
                            thc_content = mg_display
                        else:
                            cbd_content = mg_display
                except (ValueError, TypeError):
                    pass

        # --- Stock status (actual Dutchie API) --------------------------------
        status = item.get("Status") or item.get("status") or "Active"
        is_below = item.get("isBelowThreshold", False)
        global_in_stock: bool = (str(status).lower() == "active") and not bool(is_below)

        # --- URL slug ---------------------------------------------------------
        # Actual Dutchie API uses cName (e.g. "og18") as the product slug
        slug = (
            item.get("cName")
            or item.get("slug")
            or item.get("id")
            or item.get("Id")
        )
        product_url: Optional[str] = (
            f"{self.store_url}/product/{slug}" if slug else None
        )

        products: List[ScrapedProduct] = []

        # --- Schema 1: Dutchie v2 variants (priceMed/option) -----------------
        variants_raw = item.get("variants") or item.get("Variants") or []
        if variants_raw and isinstance(variants_raw, list):
            for fv in variants_raw:
                if not isinstance(fv, dict):
                    continue
                price: Optional[float] = None
                # Utah is medical-only → prefer priceMed
                for pk in ("priceMed", "priceRec", "price", "Price", "amount"):
                    v = fv.get(pk)
                    if v is not None:
                        try:
                            price = float(v)
                        except (ValueError, TypeError):
                            pass
                        if price is not None:
                            break
                if price is None:
                    continue

                opt = str(fv.get("option") or "").strip()
                if opt:
                    weight: Optional[str] = opt
                else:
                    unit = str(fv.get("unit") or fv.get("unitQuantityType") or "").lower()
                    qty = fv.get("unitQuantity") or fv.get("quantity") or ""
                    if qty and unit:
                        if "gram" in unit:
                            unit = "g"
                        elif "oz" in unit or "ounce" in unit:
                            unit = "oz"
                        elif "mg" in unit or "milligram" in unit:
                            unit = "mg"
                        elif "ml" in unit or "milliliter" in unit:
                            unit = "ml"
                        weight = f"{qty}{unit}"
                    else:
                        weight = None

                var_in_stock = bool(fv.get("inStock", fv.get("in_stock", global_in_stock)))
                products.append(ScrapedProduct(
                    name=name, brand=brand, category=category, price=price,
                    weight=weight, thc_percentage=thc_pct, cbd_percentage=cbd_pct,
                    thc_content=thc_content, cbd_content=cbd_content,
                    in_stock=var_in_stock, url=product_url, raw_data=item,
                ))
            return products  # Done if we had variants

        # --- Schema 2: actual Dutchie API — parallel Options + Prices arrays -
        # e.g. Options=["1/8oz","1/4oz"], medicalPrices=[45,85], Prices=[45,85]
        options = item.get("Options") or item.get("options") or []
        # Utah is medical-only → prefer medicalPrices
        prices_list = (
            item.get("medicalPrices")
            or item.get("Prices")
            or item.get("prices")
            or []
        )

        if options and isinstance(options, list) and prices_list and isinstance(prices_list, list):
            for i, option in enumerate(options):
                raw_price = prices_list[i] if i < len(prices_list) else None
                if raw_price is None:
                    continue
                price = None
                if isinstance(raw_price, (int, float)):
                    price = float(raw_price)
                elif isinstance(raw_price, dict):
                    for pk in ("price", "Price", "amount"):
                        if pk in raw_price:
                            try:
                                price = float(raw_price[pk])
                                break
                            except (ValueError, TypeError):
                                pass
                if price is None:
                    continue
                products.append(ScrapedProduct(
                    name=name, brand=brand, category=category, price=price,
                    weight=str(option).strip() if option else None,
                    thc_percentage=thc_pct, cbd_percentage=cbd_pct,
                    thc_content=thc_content, cbd_content=cbd_content,
                    in_stock=global_in_stock, url=product_url, raw_data=item,
                ))
            if products:
                return products

        # --- Schema 3: legacy prices list (list of dicts) --------------------
        prices_raw = item.get("prices") or item.get("Prices") or []
        if prices_raw and isinstance(prices_raw, list) and isinstance(prices_raw[0], dict):
            for fp in prices_raw:
                price = None
                for pk in ("price", "Price", "amount", "Amount"):
                    if pk in fp:
                        try:
                            price = float(fp[pk])
                        except (ValueError, TypeError):
                            pass
                        if price is not None:
                            break
                if price is None:
                    continue
                unit = str(fp.get("unit") or fp.get("Unit") or "").lower()
                qty = fp.get("unitQuantity") or fp.get("quantity") or ""
                weight = None
                if qty and unit:
                    if "gram" in unit:
                        unit = "g"
                    elif "oz" in unit or "ounce" in unit:
                        unit = "oz"
                    elif "mg" in unit or "milligram" in unit:
                        unit = "mg"
                    elif "ml" in unit or "milliliter" in unit:
                        unit = "ml"
                    weight = f"{qty}{unit}"
                fp_in_stock = bool(fp.get("inStock", fp.get("in_stock", global_in_stock)))
                products.append(ScrapedProduct(
                    name=name, brand=brand, category=category, price=price,
                    weight=weight, thc_percentage=thc_pct, cbd_percentage=cbd_pct,
                    thc_content=thc_content, cbd_content=cbd_content,
                    in_stock=fp_in_stock, url=product_url, raw_data=item,
                ))
            if products:
                return products

        # --- Schema 4: flat price field (last resort) ------------------------
        price = None
        for pk in ("price", "Price", "amount", "priceMed", "priceRec"):
            raw = item.get(pk)
            if raw is not None:
                try:
                    price = float(raw)
                    break
                except (ValueError, TypeError):
                    pass
        if price is not None:
            weight_raw = item.get("weight") or item.get("Weight")
            products.append(ScrapedProduct(
                name=name, brand=brand, category=category, price=price,
                weight=str(weight_raw) if weight_raw else None,
                thc_percentage=thc_pct, cbd_percentage=cbd_pct,
                thc_content=thc_content, cbd_content=cbd_content,
                in_stock=global_in_stock, url=product_url, raw_data=item,
            ))

        return products

    # -----------------------------------------------------------------------
    # DOM extraction parsing (used when API interception yields nothing)
    # -----------------------------------------------------------------------

    def _parse_dom_products(
        self, dom_items: List[Dict[str, Any]]
    ) -> List[ScrapedProduct]:
        """
        Convert raw DOM extraction dicts → ScrapedProducts.

        Each dict has: fullText, url, price, nameText, brandText, weightText.
        We parse fields from fullText using regex where sub-element text is absent.
        """
        products: List[ScrapedProduct] = []

        for item in dom_items:
            try:
                product = self._parse_dom_item(item)
                if product is not None:
                    products.append(product)
            except Exception as exc:
                logger.warning(f"DOM product parse error: {exc}")

        return products

    def _parse_dom_item(self, item: Dict[str, Any]) -> Optional[ScrapedProduct]:
        """Parse a single DOM extraction dict → ScrapedProduct."""
        text = item.get("fullText", "")
        if not text:
            return None

        # Price
        price_str = item.get("price")
        if not price_str:
            m = re.search(r"\$(\d+(?:\.\d{1,2})?)", text)
            price_str = m.group(1) if m else None
        if not price_str:
            return None
        try:
            price = float(price_str)
        except (ValueError, TypeError):
            return None

        # Name — prefer explicit nameText, else first non-empty line
        name = (item.get("nameText") or "").strip()
        if not name:
            lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
            name = lines[0] if lines else text[:60].strip()
        if not name:
            return None

        # Brand
        brand = (item.get("brandText") or "").strip() or "Unknown"

        # Category — infer from keywords in the product text
        category = "other"
        text_lower = text.lower()
        for kw, cat in (
            ("flower", "flower"),
            ("pre-roll", "pre-roll"),
            ("pre roll", "pre-roll"),
            ("vaporizer", "vape"),
            ("cartridge", "vape"),
            ("vape", "vape"),
            ("edible", "edible"),
            ("gummy", "edible"),
            ("chocolate", "edible"),
            ("concentrate", "concentrate"),
            ("wax", "concentrate"),
            ("shatter", "concentrate"),
            ("live resin", "concentrate"),
            ("rosin", "concentrate"),
            ("tincture", "tincture"),
            ("topical", "topical"),
            ("lotion", "topical"),
            ("patch", "topical"),
            ("accessory", "hardware"),
            ("accessories", "hardware"),
            ("hardware", "hardware"),
            ("pipe", "hardware"),
        ):
            if kw in text_lower:
                category = cat
                break

        # Weight
        weight_text = (item.get("weightText") or "").strip()
        if weight_text:
            weight: Optional[str] = weight_text
        else:
            # Look for weight patterns in full text — skip potency numbers
            # Pattern: number + unit (g, mg, ml, oz) NOT preceded by THC/CBD
            wm = re.search(
                r"(?<!THC[:\s]{0,3})(?<!CBD[:\s]{0,3})"
                r"\b(\d+(?:\.\d+)?)\s*(g|mg|ml|oz)\b",
                text,
                re.IGNORECASE,
            )
            weight = (wm.group(1) + wm.group(2).lower()) if wm else None

        # THC
        thc_pct: Optional[float] = None
        thc_content: Optional[str] = None
        thc_m = re.search(r"THC[:\s]*(\d+(?:\.\d+)?)\s*(%)", text, re.IGNORECASE)
        thc_mg_m = re.search(r"THC[:\s]*(\d+(?:\.\d+)?)\s*mg", text, re.IGNORECASE)
        if thc_m:
            thc_content = f"{thc_m.group(1)}%"
            try:
                thc_pct = float(thc_m.group(1))
            except (ValueError, TypeError):
                pass
        elif thc_mg_m:
            thc_content = f"{thc_mg_m.group(1)} mg"

        # CBD
        cbd_pct: Optional[float] = None
        cbd_content: Optional[str] = None
        cbd_m = re.search(r"CBD[:\s]*(\d+(?:\.\d+)?)\s*(%)", text, re.IGNORECASE)
        cbd_mg_m = re.search(r"CBD[:\s]*(\d+(?:\.\d+)?)\s*mg", text, re.IGNORECASE)
        if cbd_m:
            cbd_content = f"{cbd_m.group(1)}%"
            try:
                cbd_pct = float(cbd_m.group(1))
            except (ValueError, TypeError):
                pass
        elif cbd_mg_m:
            cbd_content = f"{cbd_mg_m.group(1)} mg"

        # In stock — absent from DOM usually means visible = in stock
        in_stock = True
        if re.search(r"\bout of stock\b|\bsold out\b|\bunavailable\b", text, re.IGNORECASE):
            in_stock = False

        product_url = item.get("url") or None

        return ScrapedProduct(
            name=name,
            brand=brand,
            category=category,
            price=price,
            weight=str(weight) if weight else None,
            thc_percentage=thc_pct,
            cbd_percentage=cbd_pct,
            thc_content=thc_content,
            cbd_content=cbd_content,
            in_stock=in_stock,
            url=product_url,
            raw_data=item,
        )

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        """Promotions not currently implemented for Beehive Farmacy."""
        return []


# ---------------------------------------------------------------------------
# Location-specific scrapers
# ---------------------------------------------------------------------------

@register_scraper(
    id="beehive-brigham-city",
    name="Beehive Farmacy (Brigham City)",
    dispensary_name="Beehive Farmacy Brigham City",
    dispensary_location="Brigham City, UT",
    schedule_minutes=120,
    description="Playwright scraper for Beehive Farmacy Brigham City (Dutchie platform)"
)
class BeehiveFarmacyBrighamScraper(BeehiveFarmacyBaseScraper):
    """
    Beehive Farmacy — Brigham City location.

    Dutchie retailerId: d77367be-fce5-40fe-8355-19e813df168e
    """

    store_url = (
        "https://brigham-city.beehivefarmacy.com"
        "/stores/beehive-farmacy-brigham-city"
    )

    def __init__(self, dispensary_id: str = "beehive-brigham-city"):
        super().__init__(dispensary_id=dispensary_id)


@register_scraper(
    id="beehive-slc",
    name="Beehive Farmacy (Salt Lake City)",
    dispensary_name="Beehive Farmacy Salt Lake City",
    dispensary_location="Salt Lake City, UT",
    schedule_minutes=120,
    description="Playwright scraper for Beehive Farmacy SLC (Dutchie platform)"
)
class BeehiveFarmacySLCScraper(BeehiveFarmacyBaseScraper):
    """
    Beehive Farmacy — Salt Lake City location.

    Dutchie retailerId: 65750558-290d-4db4-908b-ad20124bf2ab
    """

    store_url = "https://shop.beehivefarmacy.com/stores/beehives-farmacy"

    def __init__(self, dispensary_id: str = "beehive-slc"):
        super().__init__(dispensary_id=dispensary_id)

"""
Dragonfly Wellness Price Scraper — Custom AppSync GraphQL Platform

Dragonfly Wellness Price (20 E Main St, Price, UT 84501) operates a custom
Next.js storefront (price.dragonflywellness.com) backed by AWS AppSync GraphQL.
This is distinct from the SLC location which uses Dutchie.

The public API key is embedded in the storefront JavaScript and the GraphQL
endpoint is openly accessible. Products are queried via the listProducts query.

API details discovered via Playwright network interception on 2026-03-17:
  Endpoint: https://zywowa2refffhmcafkqk3zixfe.appsync-api.us-west-2.amazonaws.com/graphql
  API Key:  da2-yrholeei3zgbjbahwclkqs7o5q (public, embedded in storefront JS)

Category mapping:
  Flower              -> flower
  Cartpens            -> vape    (cartridge/pen devices)
  Infused Edible      -> edible
  Concentrates        -> concentrate
  Infused Non-edible  -> topical / tincture (best-effort by subcategory)
  Unmedicated         -> hardware

Product weight is provided for Flower as "1g", "3.5g", etc. For other
categories the weight field is often null; we fall back to parsing it from
the product name.

THC percentage is extracted from potencyStrings, e.g. "Total THC*: 23.1%".
Guard against values >100 (Dragonfly stores mg values for edibles with "%"
sometimes absent — we only set thc_percentage when the parsed value is <=100).
"""
import logging
import re
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

import aiohttp

from .base_scraper import BaseScraper, ScrapedProduct, ScrapedPromotion
from .registry import register_scraper

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AppSync GraphQL constants
# ---------------------------------------------------------------------------

_APPSYNC_ENDPOINT = (
    "https://zywowa2refffhmcafkqk3zixfe.appsync-api.us-west-2.amazonaws.com/graphql"
)
_APPSYNC_API_KEY = "da2-yrholeei3zgbjbahwclkqs7o5q"

# Same query the storefront uses.  We ask for all fields relevant to pricing.
_LIST_PRODUCTS_QUERY = """
query ListProducts($filter: ModelProductFilterInput, $limit: Int, $nextToken: String) {
  listProducts(filter: $filter, limit: $limit, nextToken: $nextToken) {
    items {
      id
      name
      category
      subcategory
      price
      discount
      description
      imageURL
      availableOnline
      quantity
      potencyStrings
      brandName
      strain
      weight
      urlName
      __typename
    }
    nextToken
    __typename
  }
}
"""

# Base URL for product detail pages
_STORE_BASE_URL = "https://price.dragonflywellness.com"

# ---------------------------------------------------------------------------
# Category mapping
# ---------------------------------------------------------------------------

_CATEGORY_MAP: Dict[str, str] = {
    "flower": "flower",
    "cartpens": "vape",
    "cartpen": "vape",
    "vape": "vape",
    "vaporizer": "vape",
    "cartridge": "vape",
    "infused edible": "edible",
    "edible": "edible",
    "edibles": "edible",
    "concentrates": "concentrate",
    "concentrate": "concentrate",
    "extract": "concentrate",
    "infused non-edible": "topical",
    "topical": "topical",
    "tincture": "tincture",
    "tinctures": "tincture",
    "unmedicated": "hardware",
    "accessories": "hardware",
    "hardware": "hardware",
    "pre-roll": "pre-roll",
    "pre-rolls": "pre-roll",
    "preroll": "pre-roll",
}


def _map_category(raw: Optional[str]) -> str:
    """Map a raw Dragonfly category string to our standard category name."""
    if not raw:
        return "other"
    key = raw.strip().lower()
    return _CATEGORY_MAP.get(key, "other")


# ---------------------------------------------------------------------------
# THC extraction helpers
# ---------------------------------------------------------------------------

_THC_PATTERN = re.compile(
    r"Total\s+THC[^:]*:\s*([\d.]+)\s*(%|mg)", re.IGNORECASE
)
_THC_SIMPLE_PATTERN = re.compile(
    r"(?:THC|Delta\s*9\s*THC)[^:]*:\s*([\d.]+)\s*(%|mg)", re.IGNORECASE
)
_WEIGHT_FROM_NAME_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(g|oz|mg|ml)\b", re.IGNORECASE
)


def _parse_thc(potency_strings: Optional[List[str]]) -> Optional[float]:
    """
    Extract a numeric THC percentage from the potencyStrings list.

    Returns None if no valid percentage is found or the value exceeds 100
    (which indicates the source is mg, not a percentage).
    """
    if not potency_strings:
        return None

    for s in potency_strings:
        m = _THC_PATTERN.search(s)
        if not m:
            m = _THC_SIMPLE_PATTERN.search(s)
        if m:
            try:
                value = float(m.group(1))
                unit = m.group(2).lower()
                if unit == "%" and value <= 100:
                    return round(value, 2)
            except ValueError:
                pass
    return None


def _parse_thc_content(potency_strings: Optional[List[str]]) -> Optional[str]:
    """Return the raw 'Total THC*: XX%' string for display, if present."""
    if not potency_strings:
        return None
    for s in potency_strings:
        clean = s.strip()
        if "Total THC" in clean or "total thc" in clean.lower():
            return clean
    # Fall back to the first entry that looks like a THC value
    for s in potency_strings:
        if re.search(r"thc", s, re.IGNORECASE):
            return s.strip()
    return None


def _extract_weight_from_name(name: str) -> Optional[str]:
    """Parse a weight hint such as '3.5g' or '500mg' from a product name."""
    m = _WEIGHT_FROM_NAME_PATTERN.search(name)
    if m:
        return m.group(0).replace(" ", "").lower()
    return None


# ---------------------------------------------------------------------------
# Scraper implementation
# ---------------------------------------------------------------------------

@register_scraper(
    id="dragonfly-price",
    name="Dragonfly Wellness (Price)",
    dispensary_name="Dragonfly Wellness Price",
    dispensary_location="Price, UT",
    schedule_minutes=120,
    description=(
        "Scraper for Dragonfly Wellness Price, UT location via AppSync GraphQL API "
        "(price.dragonflywellness.com)"
    )
)
class DragonFlyWellnessPriceScraper(BaseScraper):
    """
    Dragonfly Wellness — Price, UT location.

    Uses AWS AppSync GraphQL directly (not Dutchie).
    API key is public and embedded in the storefront.
    """

    def __init__(self, dispensary_id: str = "dragonfly-price"):
        super().__init__(dispensary_id=dispensary_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_products_page(
        self,
        session: aiohttp.ClientSession,
        next_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch one page of products from the AppSync GraphQL API."""
        # Filter: price > 0 AND updated within last 6 months
        six_months_ago = (
            datetime.now(timezone.utc) - timedelta(days=183)
        ).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        now_str = (
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        )

        variables: Dict[str, Any] = {
            "limit": 500,
            "nextToken": next_token,
            "filter": {
                "price": {"gt": 0},
                "updatedAt": {"between": [six_months_ago, now_str]},
            },
        }

        payload = {
            "query": _LIST_PRODUCTS_QUERY,
            "variables": variables,
        }

        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "x-api-key": _APPSYNC_API_KEY,
            "x-amz-user-agent": "aws-amplify/6.16.2 api/1 framework/2",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }

        async with session.post(
            _APPSYNC_ENDPOINT, json=payload, headers=headers
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    # Non-product items that appear in the Dragonfly catalog — service fees,
    # donations, and utility items that are not cannabis or hardware products.
    _NON_PRODUCT_PATTERNS = re.compile(
        r"(?i)^(rounding\s+donation|dept\s+of\s+health\s+transaction\s+fee"
        r"|herbal\s+viewer|df\s+herbal\s+viewer)$"
    )

    def _parse_product(self, item: Dict[str, Any]) -> Optional[ScrapedProduct]:
        """Convert a raw AppSync product item into a ScrapedProduct."""
        try:
            name = (item.get("name") or "").strip()
            if not name:
                return None

            # Skip non-product service items (donations, fees, etc.)
            if self._NON_PRODUCT_PATTERNS.match(name):
                logger.debug("Skipping non-product item: %s", name)
                return None

            price_raw = item.get("price")
            try:
                price = float(price_raw) if price_raw is not None else 0.0
            except (TypeError, ValueError):
                price = 0.0

            if price <= 0:
                return None

            # Skip placeholder prices — $0.01 items are "call for price" placeholders
            # (e.g. MiniNail accessories listed at $0.01 on the storefront)
            if price < 0.50:
                return None

            raw_category = item.get("category", "")
            category = _map_category(raw_category)

            # Weight: provided for flower; parse from name for others
            weight = item.get("weight") or _extract_weight_from_name(name)

            # Brand — use brandName if present
            brand_raw = item.get("brandName")
            brand = (brand_raw or "").strip() or "Dragonfly Wellness"

            # Potency
            potency_strings = item.get("potencyStrings") or []
            thc_pct = _parse_thc(potency_strings)
            thc_content = _parse_thc_content(potency_strings)

            # Availability: product must be marked availableOnline and have stock
            available_online = bool(item.get("availableOnline", True))
            quantity = item.get("quantity") or 0
            in_stock = available_online and quantity > 0

            # Product URL
            url_name = item.get("urlName") or ""
            if url_name:
                product_url = f"{_STORE_BASE_URL}/products/{url_name}"
            else:
                product_url = _STORE_BASE_URL + "/products"

            return ScrapedProduct(
                name=name,
                brand=brand,
                category=category,
                price=price,
                in_stock=in_stock,
                thc_percentage=thc_pct,
                thc_content=thc_content,
                weight=weight,
                url=product_url,
                raw_data=item,
            )
        except Exception as exc:
            logger.warning("Error parsing product %s: %s", item.get("id"), exc)
            return None

    # ------------------------------------------------------------------
    # BaseScraper interface
    # ------------------------------------------------------------------

    async def scrape_products(self) -> List[ScrapedProduct]:
        """
        Fetch all products from the Dragonfly Wellness Price AppSync API.

        Handles pagination via nextToken.
        """
        products: List[ScrapedProduct] = []
        next_token: Optional[str] = None
        page = 0

        try:
            async with aiohttp.ClientSession() as session:
                while True:
                    page += 1
                    logger.info(
                        "Fetching Dragonfly Wellness Price products page %d "
                        "(nextToken=%s)",
                        page,
                        next_token,
                    )

                    data = await self._fetch_products_page(session, next_token)
                    errors = data.get("errors")
                    if errors:
                        logger.error(
                            "GraphQL errors on page %d: %s", page, errors
                        )
                        break

                    list_result = (
                        data.get("data", {}).get("listProducts") or {}
                    )
                    items = list_result.get("items") or []

                    for item in items:
                        try:
                            product = self._parse_product(item)
                            if product is not None:
                                products.append(product)
                        except Exception as exc:
                            logger.warning(
                                "Skipping product due to error: %s", exc
                            )
                            continue

                    next_token = list_result.get("nextToken")
                    logger.info(
                        "Page %d: parsed %d products (cumulative %d), "
                        "nextToken=%s",
                        page,
                        len(items),
                        len(products),
                        "present" if next_token else "None",
                    )

                    if not next_token:
                        break

        except aiohttp.ClientError as exc:
            logger.error(
                "HTTP error fetching Dragonfly Wellness Price products: %s",
                exc,
            )
        except Exception as exc:
            logger.exception(
                "Unexpected error scraping Dragonfly Wellness Price: %s", exc
            )

        logger.info(
            "Dragonfly Wellness Price: scraped %d products total", len(products)
        )
        return products

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        """Promotions not currently implemented for Dragonfly Wellness Price."""
        return []

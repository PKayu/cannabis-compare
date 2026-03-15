"""
Dragonfly Wellness Scraper — Dutchie Platform

Dragonfly Wellness operates two Utah locations:
  - Salt Lake City (711 S State St) — Utah's first licensed cannabis pharmacy (opened March 2020)
  - Price, UT (20 E Main St) — eastern Utah location

Both locations use the Dutchie storefront directly (no white-label subdomain).
Scraping logic is inherited from BeehiveFarmacyBaseScraper which implements
the three-layer Dutchie strategy: JS fetch interception → network listener → DOM fallback.

Dutchie slugs:
  SLC   — dragonfly-wellness
  Price — dragonfly-wellness-price
"""

from typing import List

from .base_scraper import ScrapedPromotion
from .beehive_farmacy_scraper import BeehiveFarmacyBaseScraper
from .registry import register_scraper

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Location-specific scrapers
# ---------------------------------------------------------------------------

@register_scraper(
    id="dragonfly-slc",
    name="Dragonfly Wellness (Salt Lake City)",
    dispensary_name="Dragonfly Wellness Salt Lake City",
    dispensary_location="Salt Lake City, UT",
    schedule_minutes=120,
    description="Playwright scraper for Dragonfly Wellness SLC (Dutchie platform)"
)
class DragonFlyWellnessSLCScraper(BeehiveFarmacyBaseScraper):
    """
    Dragonfly Wellness — Salt Lake City location.

    Utah's first licensed medical cannabis pharmacy.
    Dutchie slug: dragonfly-wellness
    """

    store_url = "https://dutchie.com/stores/dragonfly-wellness"

    def __init__(self, dispensary_id: str = "dragonfly-slc"):
        super().__init__(dispensary_id=dispensary_id)

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        """Promotions not currently implemented for Dragonfly Wellness."""
        return []


# ---------------------------------------------------------------------------
# Price, UT location — DISABLED pending URL investigation
# ---------------------------------------------------------------------------
# Dragonfly Price (20 E Main St, Price, UT) uses Dutchie slug: dragonfly-wellness-price
# Attempted URLs:
#   https://dutchie.com/stores/dragonfly-wellness-price       → 500px info page, 0 products
#   https://dutchie.com/dispensary/dragonfly-wellness-price   → age gate dismisses but page goes blank
#   https://dutchie.com/dispensaries/dragonfly-wellness-price/menu → same blank result
# Root cause: [data-testid*="age"] button selector appears to trigger an action that
# unloads the page on the /dispensary/ path. Investigate manually before enabling.
#
# @register_scraper(
#     id="dragonfly-price",
#     name="Dragonfly Wellness (Price)",
#     dispensary_name="Dragonfly Wellness Price",
#     dispensary_location="Price, UT",
#     schedule_minutes=120,
#     description="Playwright scraper for Dragonfly Wellness Price, UT (Dutchie platform)"
# )
# class DragonFlyWellnessPriceScraper(BeehiveFarmacyBaseScraper):
#     store_url = "https://dutchie.com/dispensaries/dragonfly-wellness-price/menu"
#     def __init__(self, dispensary_id: str = "dragonfly-price"):
#         super().__init__(dispensary_id=dispensary_id)
#     async def scrape_promotions(self) -> List[ScrapedPromotion]:
#         return []

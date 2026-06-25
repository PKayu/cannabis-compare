"""
The Forest Utah Scraper — Dutchie Platform

The Forest Murray location switched from iHeartJane to a Dutchie white-label
storefront in June 2026.

Location:
  Murray — 6041 State St, Murray, UT 84107

Platform:
  Dutchie embedded Next.js storefront (same architecture as Beehive Farmacy).
  Dispensary ID: 69cd22a84028784c6f7ecf8a
  GraphQL API:   https://theforestutah.com/api-1/graphql

Scraping strategy (same as beehive_farmacy_scraper.py):
  1. Iterate over per-category URLs:
       https://theforestutah.com/stores/the-forest-murray/products/{category}
  2. Intercept fetch() responses (JS patch + Playwright response listener).
  3. Parse Dutchie JSON payloads via BeehiveFarmacyBaseScraper._parse_dutchie_response().
  4. DOM extraction fallback if no API responses captured.
"""

from typing import List

from .base_scraper import ScrapedPromotion
from .beehive_farmacy_scraper import BeehiveFarmacyBaseScraper
from .registry import register_scraper

import logging

logger = logging.getLogger(__name__)


@register_scraper(
    id="the-forest-murray",
    name="The Forest (Murray)",
    dispensary_name="The Forest Murray",
    dispensary_location="Murray, UT",
    schedule_minutes=120,
    description=(
        "Playwright scraper for The Forest Utah — Murray location "
        "(Dutchie platform; dispensary ID 69cd22a84028784c6f7ecf8a)."
    ),
)
class TheForestMurrayScraper(BeehiveFarmacyBaseScraper):
    """
    The Forest — Murray, Utah (6041 State St, Murray, UT 84107).

    Dutchie white-label storefront at theforestutah.com.
    """

    store_url = "https://theforestutah.com/stores/the-forest-murray"

    def __init__(self, dispensary_id: str = "the-forest-murray"):
        super().__init__(dispensary_id=dispensary_id)

    def _get_urls_to_scrape(self) -> List[str]:
        """Return per-category product URLs (Dutchie doesn't load all on one page)."""
        return [
            f"{self.store_url}/products/{cat}"
            for cat in self.DUTCHIE_CATEGORIES
        ]

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        return []

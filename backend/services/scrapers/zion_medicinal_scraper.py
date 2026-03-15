"""
Zion Medicinal Scraper — Dutchie Embedded Menu Platform

Zion Medicinal (Cedar City, UT) uses Dutchie's embedded-menu platform at
  https://dutchie.com/embedded-menu/bloom-medicinal/

The menu is structured identically to Beehive Farmacy's white-label storefront
(same Dutchie Next.js app), so we extend BeehiveFarmacyBaseScraper directly.
Because the embedded-menu format only loads one category at a time, we override
``_get_urls_to_scrape`` to iterate over all Dutchie category pages.

Key identifiers:
  retailerId  = 4e08e3db-e487-4b8f-b58c-29cf5a5b29b2
  dispensaryId = 60b0455896ed3f00b4e88396
  slug         = bloom-medicinal  (legacy Bloom Medicinal Cedar City branding)
"""
import logging
from typing import List

from .beehive_farmacy_scraper import BeehiveFarmacyBaseScraper
from .base_scraper import ScrapedPromotion
from .registry import register_scraper

logger = logging.getLogger(__name__)


@register_scraper(
    id="zion-medicinal",
    name="Zion Medicinal (Cedar City)",
    dispensary_name="Zion Medicinal",
    dispensary_location="Cedar City, UT",
    schedule_minutes=120,
    description=(
        "Dutchie embedded-menu scraper for Zion Medicinal, Cedar City, UT "
        "(Dutchie slug: bloom-medicinal, retailerId: 4e08e3db-e487-4b8f-b58c-29cf5a5b29b2)"
    ),
)
class ZionMedicinalScraper(BeehiveFarmacyBaseScraper):
    """
    Scraper for Zion Medicinal — Cedar City, Utah (Iron County).

    Reuses the entire Beehive Farmacy Dutchie scraping pipeline.  Overrides
    ``_get_urls_to_scrape`` to iterate over each Dutchie category page,
    because the embedded-menu format only loads one category at a time
    (unlike white-label storefronts that may infinite-scroll all products).
    """

    store_url = "https://dutchie.com/embedded-menu/bloom-medicinal/"

    def __init__(self, dispensary_id: str = "zion-medicinal"):
        super().__init__(dispensary_id=dispensary_id)

    def _get_urls_to_scrape(self) -> List[str]:
        """Return per-category URLs for the Dutchie embedded menu."""
        base = self.store_url.rstrip("/")
        return [f"{base}/products/{cat}" for cat in self.DUTCHIE_CATEGORIES]

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        """Promotions not yet implemented for Zion Medicinal."""
        return []

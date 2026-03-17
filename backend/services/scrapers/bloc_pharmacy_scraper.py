"""
Bloc Pharmacy Scraper — Dutchie White-Label Platform

Bloc Pharmacy operates two Utah locations:
  - South Jordan (10392 South Jordan Gateway, South Jordan, UT 84095)
  - St. George   (1624 S Convention Center Drive, St. George, UT 84790)

Both locations use Dutchie white-label storefronts on custom subdomains:
  South Jordan  — store-south-jordan.blocpharmacy.com
  St. George    — store-st-george.blocpharmacy.com

Scraping logic is inherited from BeehiveFarmacyBaseScraper, which implements
the three-layer Dutchie strategy: JS fetch interception → network listener → DOM fallback.

Dutchie retailer IDs (from window.reactEnv in each storefront's HTML):
  South Jordan  — 5bdc0890-04fc-43a1-be75-5db931731c66
  St. George    — df5a80a7-42b9-48b1-87b6-d425b1667a1b
"""

from typing import List

from .base_scraper import ScrapedPromotion
from .beehive_farmacy_scraper import BeehiveFarmacyBaseScraper
from .registry import register_scraper

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# South Jordan location
# ---------------------------------------------------------------------------

@register_scraper(
    id="bloc-south-jordan",
    name="Bloc Pharmacy (South Jordan)",
    dispensary_name="Bloc Pharmacy South Jordan",
    dispensary_location="South Jordan, UT",
    schedule_minutes=120,
    description=(
        "Playwright scraper for Bloc Pharmacy South Jordan (Dutchie white-label; "
        "retailerId: 5bdc0890-04fc-43a1-be75-5db931731c66)"
    ),
)
class BlocPharmacySouthJordanScraper(BeehiveFarmacyBaseScraper):
    """
    Bloc Pharmacy — South Jordan, Utah.

    Dutchie white-label storefront at store-south-jordan.blocpharmacy.com.
    """

    store_url = "https://store-south-jordan.blocpharmacy.com/stores/bloc-pharmacy-south-jordan"

    def __init__(self, dispensary_id: str = "bloc-south-jordan"):
        super().__init__(dispensary_id=dispensary_id)

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        """Promotions not currently implemented for Bloc Pharmacy South Jordan."""
        return []


# ---------------------------------------------------------------------------
# St. George location
# ---------------------------------------------------------------------------

@register_scraper(
    id="bloc-st-george",
    name="Bloc Pharmacy (St. George)",
    dispensary_name="Bloc Pharmacy St. George",
    dispensary_location="St. George, UT",
    schedule_minutes=120,
    description=(
        "Playwright scraper for Bloc Pharmacy St. George (Dutchie white-label; "
        "retailerId: df5a80a7-42b9-48b1-87b6-d425b1667a1b)"
    ),
)
class BlocPharmacyStGeorgeScraper(BeehiveFarmacyBaseScraper):
    """
    Bloc Pharmacy — St. George, Utah.

    Dutchie white-label storefront at store-st-george.blocpharmacy.com.
    """

    store_url = "https://store-st-george.blocpharmacy.com/stores/bloc-pharmacy-st-george"

    def __init__(self, dispensary_id: str = "bloc-st-george"):
        super().__init__(dispensary_id=dispensary_id)

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        """Promotions not currently implemented for Bloc Pharmacy St. George."""
        return []

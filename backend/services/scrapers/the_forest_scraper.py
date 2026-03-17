"""
The Forest Utah Scraper — iHeartJane / dmerch Platform

The Forest operates two Utah locations (Murray and Springville), both sharing
a single iHeartJane store ID (3196) and a single website (theforestutah.com).
The product catalog is the same for both locations, so one scraper covers both.

Location:
  Murray     — 6041 State St, Murray, UT 84107
  Springville — 484 S 1750 W, Springville, UT

Platform:
  iHeartJane "frameless boost" embed, identical architecture to The Flower Shop.

Scraping strategy (same as flower_shop_scraper.py):
  1. Navigate to each category page:
       https://theforestutah.com/shop/menu/{kind}/
  2. Intercept POST response from dmerch.iheartjane.com/v2/multi
     (placement="menu_inline_table") to get all products for that category.
  3. Parse product attributes from search_attributes dict.

iHeartJane store ID: 3196

Category URL pattern:
  https://theforestutah.com/shop/menu/{kind}/

Product URL pattern:
  https://theforestutah.com/shop/products/{url_slug}
"""

from typing import List

from .base_scraper import ScrapedPromotion
from .flower_shop_scraper import FlowerShopBaseScraper
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
        "Playwright scraper for The Forest Utah (iHeartJane frameless embed; "
        "store_id=3196). Covers the Murray location at 6041 State St."
    ),
)
class TheForestMurrayScraper(FlowerShopBaseScraper):
    """
    The Forest — Murray, Utah (6041 State St, Murray, UT 84107).

    iHeartJane frameless embed at theforestutah.com/shop/menu/{kind}/.
    Both Murray and Springville share store ID 3196; this scraper covers both.
    """

    store_id = 3196
    location_slug = "shop"
    location_name = "The Forest Murray"
    BASE_URL = "https://theforestutah.com"

    def __init__(self, dispensary_id: str = "the-forest-murray"):
        super().__init__(dispensary_id=dispensary_id)

    async def scrape_promotions(self) -> List[ScrapedPromotion]:
        """Promotions not currently implemented for The Forest."""
        return []

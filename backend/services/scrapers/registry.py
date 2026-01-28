"""
Scraper Registry - Central registry for all dispensary scrapers.

Scrapers self-register using the @register_scraper decorator, which stores
metadata about each scraper (name, location, schedule, etc.). This enables:

1. Dynamic scraper discovery - no hardcoded lists
2. Generic API endpoints - /run/{scraper_id} works for any scraper
3. Automatic scheduling - all registered scrapers are scheduled on startup
4. Easy addition of new scrapers - just add decorator and import

Example:
    @register_scraper(
        id="wholesomeco",
        name="WholesomeCo",
        dispensary_name="WholesomeCo",
        dispensary_location="Bountiful, UT",
        schedule_minutes=120
    )
    class WholesomeCoScraper(BaseScraper):
        ...
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING, Type, Dict, Optional, List, Any

if TYPE_CHECKING:
    from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

# Module-level storage (natural singleton)
_scrapers: Dict[str, "ScraperConfig"] = {}
_lock = threading.Lock()


@dataclass(frozen=True)
class ScraperConfig:
    """
    Configuration for a registered scraper.

    Frozen dataclass prevents accidental mutation after registration.
    """
    id: str
    """URL-friendly identifier (e.g., "wholesomeco", "beehive")"""

    name: str
    """Human-readable display name (e.g., "WholesomeCo")"""

    scraper_class: Type["BaseScraper"]
    """The scraper class to instantiate"""

    dispensary_name: str
    """Name of the dispensary in the database"""

    dispensary_location: str
    """Location of the dispensary"""

    schedule_minutes: int = 120
    """How often to run this scraper (default: 2 hours per PRD)"""

    enabled: bool = True
    """Whether this scraper is currently enabled"""

    description: str = ""
    """Optional description of the scraper"""

    def __post_init__(self):
        """Validate scraper configuration after creation."""
        # Validate ID format (alphanumeric, underscore, hyphen)
        if not self.id or not self.id.replace("-", "_").replace("_", "").isalnum():
            raise ValueError(
                f"Invalid scraper ID '{self.id}'. "
                "Must be alphanumeric with underscores or hyphens only."
            )

        # Validate schedule is reasonable
        if self.schedule_minutes < 5:
            raise ValueError(
                f"schedule_minutes must be at least 5, got {self.schedule_minutes}"
            )


class ScraperRegistry:
    """
    Central registry for all dispensary scrapers.

    Thread-safe singleton pattern using module-level dict and lock.
    """

    @classmethod
    def register(cls, config: ScraperConfig) -> None:
        """
        Register a scraper configuration.

        Args:
            config: The scraper configuration to register

        Raises:
            ValueError: If scraper ID is invalid
        """
        with _lock:
            if config.id in _scrapers:
                logger.warning(
                    f"Scraper '{config.id}' already registered. Overwriting."
                )
            _scrapers[config.id] = config
            logger.info(f"Registered scraper: {config.id} ({config.name})")

    @classmethod
    def get(cls, scraper_id: str) -> Optional[ScraperConfig]:
        """
        Get a scraper configuration by ID.

        Args:
            scraper_id: The scraper identifier

        Returns:
            ScraperConfig if found, None otherwise
        """
        return _scrapers.get(scraper_id)

    @classmethod
    def get_all(cls) -> Dict[str, ScraperConfig]:
        """
        Get all registered scrapers.

        Returns a copy to prevent external mutation.

        Returns:
            Dict mapping scraper IDs to their configurations
        """
        with _lock:
            return _scrapers.copy()

    @classmethod
    def get_enabled(cls) -> List[ScraperConfig]:
        """
        Get all enabled scrapers.

        Returns:
            List of enabled scraper configurations
        """
        return [c for c in _scrapers.values() if c.enabled]

    @classmethod
    def is_enabled(cls, scraper_id: str) -> bool:
        """
        Check if a scraper is registered and enabled.

        Args:
            scraper_id: The scraper identifier

        Returns:
            True if scraper exists and is enabled
        """
        config = _scrapers.get(scraper_id)
        return config is not None and config.enabled

    @classmethod
    def clear(cls) -> None:
        """
        Clear all scraper registrations.

        Mainly intended for testing isolation.
        """
        with _lock:
            _scrapers.clear()
            logger.info("Cleared all scraper registrations")


def register_scraper(**kwargs: Any) -> callable:
    """
    Decorator to register a scraper class with its metadata.

    Usage:
        @register_scraper(
            id="wholesomeco",
            name="WholesomeCo",
            dispensary_name="WholesomeCo",
            dispensary_location="Bountiful, UT",
            schedule_minutes=120,
            description="Direct scraping from WholesomeCo website"
        )
        class WholesomeCoScraper(BaseScraper):
            async def scrape_products(self) -> List[ScrapedProduct]:
                ...

    Args:
        **kwargs: ScraperConfig fields (id, name, dispensary_name, etc.)

    Returns:
        Decorator function that registers the class
    """
    def decorator(cls: Type["BaseScraper"]) -> Type["BaseScraper"]:
        config = ScraperConfig(scraper_class=cls, **kwargs)
        ScraperRegistry.register(config)
        return cls
    return decorator

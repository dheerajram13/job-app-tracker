"""
Scraper Factory - Factory Pattern Implementation
Creates appropriate scraper instances based on site name
"""
import logging
from typing import List, Optional
from app.interfaces.job_scraper_interface import IJobScraper
from app.services.scrapers.jobspy_scraper import JobspyScraper
from app.exceptions import SiteNotSupportedError

logger = logging.getLogger(__name__)


class ScraperFactory:
    """
    Factory for creating job scraper instances

    Implements Factory Pattern - encapsulates object creation logic
    Follows Open/Closed Principle - easy to add new scrapers
    """

    def __init__(self):
        """Initialize factory with available scrapers"""
        self._scrapers: List[IJobScraper] = [
            JobspyScraper(),
            # Can add more scrapers here:
            # CustomLinkedInScraper(),
            # CustomIndeedScraper(),
        ]

    def get_scraper(self, site_name: str) -> IJobScraper:
        """
        Get appropriate scraper for a site

        Args:
            site_name: Name of the job site

        Returns:
            Scraper instance that supports the site

        Raises:
            SiteNotSupportedError: If no scraper supports the site
        """
        for scraper in self._scrapers:
            if scraper.supports_site(site_name):
                logger.info(f"Found scraper {scraper.__class__.__name__} for site {site_name}")
                return scraper

        raise SiteNotSupportedError(site_name)

    def get_scrapers_for_sites(self, site_names: List[str]) -> List[tuple[str, IJobScraper]]:
        """
        Get scrapers for multiple sites

        Args:
            site_names: List of site names

        Returns:
            List of tuples (site_name, scraper)
        """
        result = []
        for site_name in site_names:
            try:
                scraper = self.get_scraper(site_name)
                result.append((site_name, scraper))
            except SiteNotSupportedError:
                logger.warning(f"No scraper found for site: {site_name}")
                continue

        return result

    def get_all_supported_sites(self) -> List[str]:
        """
        Get list of all supported site names

        Returns:
            List of supported site names
        """
        supported_sites = set()
        for scraper in self._scrapers:
            if hasattr(scraper, 'SUPPORTED_SITES'):
                supported_sites.update(scraper.SUPPORTED_SITES)

        return sorted(list(supported_sites))

    def register_scraper(self, scraper: IJobScraper) -> None:
        """
        Register a new scraper (for extensibility)

        Args:
            scraper: Scraper instance to register
        """
        self._scrapers.append(scraper)
        logger.info(f"Registered new scraper: {scraper.__class__.__name__}")


# Singleton instance
_scraper_factory_instance: Optional[ScraperFactory] = None


def get_scraper_factory() -> ScraperFactory:
    """
    Get singleton instance of ScraperFactory

    Returns:
        ScraperFactory instance
    """
    global _scraper_factory_instance
    if _scraper_factory_instance is None:
        _scraper_factory_instance = ScraperFactory()
    return _scraper_factory_instance

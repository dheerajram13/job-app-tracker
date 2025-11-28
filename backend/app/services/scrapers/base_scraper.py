"""
Base Scraper Implementation
Provides common functionality for all scrapers
"""
import logging
from typing import List, Dict
from app.interfaces.job_scraper_interface import IJobScraper, JobSearchParams

logger = logging.getLogger(__name__)


class BaseScraper(IJobScraper):
    """
    Abstract base scraper with common functionality

    Implements Template Method pattern for scraping workflow
    """

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/',
        }

    async def search(self, params: JobSearchParams) -> List[Dict]:
        """
        Template method for job search workflow

        Args:
            params: Job search parameters

        Returns:
            List of job dictionaries
        """
        try:
            logger.info(f"Starting search with {self.__class__.__name__}")
            results = await self._execute_search(params)
            logger.info(f"Found {len(results)} jobs with {self.__class__.__name__}")
            return results
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {str(e)}")
            return []

    async def _execute_search(self, params: JobSearchParams) -> List[Dict]:
        """
        Execute the actual search - must be implemented by subclasses

        Args:
            params: Job search parameters

        Returns:
            List of job dictionaries
        """
        raise NotImplementedError("Subclasses must implement _execute_search")

    def supports_site(self, site_name: str) -> bool:
        """
        Check if this scraper supports a specific site

        Args:
            site_name: Name of the job site

        Returns:
            True if supported, False otherwise
        """
        raise NotImplementedError("Subclasses must implement supports_site")

    def _normalize_url(self, url: str, base_url: str) -> str:
        """
        Normalize relative URLs to absolute URLs

        Args:
            url: URL to normalize
            base_url: Base URL for the site

        Returns:
            Absolute URL
        """
        if not url:
            return ""
        if url.startswith('http'):
            return url
        return f"{base_url}{url}"

    def _extract_text_safe(self, element, selector: str = None) -> str:
        """
        Safely extract text from BeautifulSoup element

        Args:
            element: BeautifulSoup element
            selector: CSS selector (if extracting from child element)

        Returns:
            Extracted text or empty string
        """
        try:
            if selector:
                elem = element.select_one(selector)
                return elem.get_text().strip() if elem else ""
            return element.get_text().strip() if element else ""
        except Exception as e:
            logger.debug(f"Error extracting text: {str(e)}")
            return ""

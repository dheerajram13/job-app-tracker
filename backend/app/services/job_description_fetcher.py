"""
Job Description Fetcher
Fetches detailed job descriptions from URLs
"""
import logging
import httpx
from bs4 import BeautifulSoup
from typing import Optional
from app.interfaces.job_scraper_interface import IJobDescriptionFetcher
from app.exceptions import NetworkError

logger = logging.getLogger(__name__)


class JobDescriptionFetcher(IJobDescriptionFetcher):
    """
    Fetches detailed job descriptions from job posting URLs

    Implements Single Responsibility Principle - focused only on fetching descriptions
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize fetcher

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        # Common selectors for job descriptions
        self.description_selectors = [
            ".job-description",
            ".description-content",
            "#job-details",
            ".job-details",
            "[data-test='job-description']",
            "[data-test='description']",
            ".jobsearch-jobDescriptionText",  # Indeed
            ".description__text",  # LinkedIn
            ".jobDescriptionContent",  # Glassdoor
        ]

    async def fetch(self, url: str) -> str:
        """
        Fetch detailed job description from URL

        Args:
            url: Job posting URL

        Returns:
            Job description text

        Raises:
            NetworkError: If fetching fails
        """
        try:
            async with httpx.AsyncClient(
                headers=self.headers,
                timeout=self.timeout,
                follow_redirects=True
            ) as client:
                logger.info(f"Fetching job description from: {url}")
                response = await client.get(url)
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # Try specific selectors first
                description = self._extract_with_selectors(soup)

                # Fallback to generic extraction
                if not description:
                    description = self._extract_generic(soup)

                if not description:
                    logger.warning(f"No description found for URL: {url}")
                    return "Description not available"

                return description

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching {url}: {e.response.status_code}")
            raise NetworkError(f"HTTP {e.response.status_code}: {str(e)}")
        except httpx.RequestError as e:
            logger.error(f"Request error fetching {url}: {str(e)}")
            raise NetworkError(f"Request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")
            raise NetworkError(f"Failed to fetch description: {str(e)}")

    def _extract_with_selectors(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract description using predefined selectors

        Args:
            soup: BeautifulSoup object

        Returns:
            Extracted description or None
        """
        for selector in self.description_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator=' ', strip=True)
                if text and len(text) > 50:  # Ensure it's substantial
                    logger.debug(f"Found description with selector: {selector}")
                    return text

        return None

    def _extract_generic(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Generic fallback extraction method

        Args:
            soup: BeautifulSoup object

        Returns:
            Extracted description or None
        """
        # Try main, article, or body
        containers = [
            soup.select_one("main"),
            soup.select_one("article"),
            soup.select_one("body")
        ]

        for container in containers:
            if not container:
                continue

            # Remove non-content elements
            for element in container.select("nav, header, footer, script, style, aside"):
                element.decompose()

            # Get text
            text = container.get_text(separator=' ', strip=True)

            if text and len(text) > 100:
                logger.debug("Found description using generic extraction")
                return text[:5000]  # Limit length

        return None

    def fetch_batch(self, urls: list[str]) -> dict[str, str]:
        """
        Fetch descriptions for multiple URLs

        Note: This is a synchronous wrapper for batch operations

        Args:
            urls: List of job posting URLs

        Returns:
            Dictionary mapping URLs to descriptions
        """
        import asyncio

        async def _fetch_all():
            results = {}
            for url in urls:
                try:
                    description = await self.fetch(url)
                    results[url] = description
                except Exception as e:
                    logger.error(f"Error fetching {url}: {str(e)}")
                    results[url] = "Error fetching description"
            return results

        return asyncio.run(_fetch_all())

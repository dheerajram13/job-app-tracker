"""
Job Search Service - Orchestrates job scraping operations
Uses Strategy, Factory, and Dependency Injection patterns
"""
import logging
from typing import List, Dict, Optional
from app.interfaces.job_scraper_interface import JobSearchParams
from app.services.scrapers.scraper_factory import ScraperFactory
from app.services.job_result_processor import JobResultProcessor
from app.services.job_description_fetcher import JobDescriptionFetcher
from app.exceptions import JobScraperError

logger = logging.getLogger(__name__)


class JobSearchService:
    """
    Orchestrates job search operations

    Follows SOLID principles:
    - Single Responsibility: Coordinates job search workflow
    - Dependency Inversion: Depends on interfaces, not concrete implementations
    - Open/Closed: Easy to extend with new scrapers via factory

    Design Patterns:
    - Facade: Provides simple interface for complex subsystem
    - Strategy: Uses different scraper strategies via factory
    - Dependency Injection: Accepts dependencies via constructor
    """

    def __init__(
        self,
        scraper_factory: Optional[ScraperFactory] = None,
        result_processor: Optional[JobResultProcessor] = None,
        description_fetcher: Optional[JobDescriptionFetcher] = None
    ):
        """
        Initialize service with dependencies

        Args:
            scraper_factory: Factory for creating scrapers
            result_processor: Processor for job results
            description_fetcher: Fetcher for job descriptions
        """
        self.scraper_factory = scraper_factory or ScraperFactory()
        self.result_processor = result_processor or JobResultProcessor()
        self.description_fetcher = description_fetcher or JobDescriptionFetcher()

    async def search_jobs(self, params: JobSearchParams) -> List[Dict]:
        """
        Search for jobs across multiple sites

        Args:
            params: Job search parameters

        Returns:
            List of job dictionaries

        Raises:
            JobScraperError: If search fails
        """
        try:
            logger.info(
                f"Starting job search: term='{params.search_term}', "
                f"location='{params.location}', sites={params.site_name}"
            )

            # Determine which sites to search
            sites_to_search = self._determine_sites(params.site_name)

            if not sites_to_search:
                logger.warning("No sites specified for search")
                return []

            # Get scrapers for each site
            site_scraper_pairs = self.scraper_factory.get_scrapers_for_sites(sites_to_search)

            if not site_scraper_pairs:
                logger.warning("No scrapers available for specified sites")
                return []

            # Execute searches across all sites
            all_results = []
            for site_name, scraper in site_scraper_pairs:
                try:
                    # Create site-specific params
                    site_params = params.copy(update={'site_name': site_name})

                    # Execute search
                    results = await scraper.search(site_params)
                    all_results.extend(results)

                    logger.info(f"Found {len(results)} jobs from {site_name}")

                except Exception as e:
                    logger.error(f"Error searching {site_name}: {str(e)}")
                    # Continue with other sites even if one fails
                    continue

            # Post-process results
            all_results = self._post_process_results(all_results, params)

            logger.info(f"Total jobs found: {len(all_results)}")
            return all_results

        except Exception as e:
            logger.error(f"Error in job search: {str(e)}")
            raise JobScraperError(f"Job search failed: {str(e)}")

    def _determine_sites(self, site_name) -> List[str]:
        """
        Determine which sites to search

        Args:
            site_name: Site name (string, list, or None)

        Returns:
            List of site names
        """
        if site_name is None:
            # Search all supported sites
            return self.scraper_factory.get_all_supported_sites()

        if isinstance(site_name, str):
            return [site_name.lower()]

        if isinstance(site_name, list):
            return [site.lower() for site in site_name]

        return []

    def _post_process_results(self, results: List[Dict], params: JobSearchParams) -> List[Dict]:
        """
        Post-process job results

        Args:
            results: Raw job results
            params: Search parameters

        Returns:
            Processed and enriched results
        """
        # Remove duplicates
        results = self.result_processor.filter_duplicates(results)

        # Enrich with relevance scores
        results = self.result_processor.enrich_results(results, params.search_term)

        # Sort by date if requested
        if params.sort_order:
            results = self.result_processor.sort_by_date(results, params.sort_order)

        # Limit results
        if params.num_jobs:
            results = results[:params.num_jobs]

        return results

    async def parse_job_url(self, url: str) -> Dict:
        """
        Parse job details from a URL

        Args:
            url: Job posting URL

        Returns:
            Dictionary containing job details
        """
        try:
            description = await self.description_fetcher.fetch(url)

            return {
                "url": url,
                "description": description,
                "success": True
            }

        except Exception as e:
            logger.error(f"Error parsing job URL {url}: {str(e)}")
            return {
                "url": url,
                "description": "Failed to fetch description",
                "success": False,
                "error": str(e)
            }

    def get_supported_sites(self) -> List[str]:
        """
        Get list of all supported job sites

        Returns:
            List of supported site names
        """
        return self.scraper_factory.get_all_supported_sites()

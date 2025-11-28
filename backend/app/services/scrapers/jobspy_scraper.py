"""
Jobspy Scraper Implementation
Uses the jobspy library for scraping multiple job sites
"""
import asyncio
import logging
from typing import List, Dict
from app.interfaces.job_scraper_interface import JobSearchParams
from app.services.scrapers.base_scraper import BaseScraper
from app.exceptions import ScrapingFailedError

logger = logging.getLogger(__name__)


class JobspyScraper(BaseScraper):
    """
    Jobspy-based scraper implementation

    Supports: LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs
    Uses the python-jobspy library for scraping
    """

    SUPPORTED_SITES = ["linkedin", "indeed", "glassdoor", "zip_recruiter", "google"]

    def __init__(self):
        super().__init__()

    def supports_site(self, site_name: str) -> bool:
        """
        Check if this scraper supports a specific site

        Args:
            site_name: Name of the job site

        Returns:
            True if supported, False otherwise
        """
        return site_name.lower() in self.SUPPORTED_SITES

    async def _execute_search(self, params: JobSearchParams) -> List[Dict]:
        """
        Execute job search using jobspy library

        Args:
            params: Job search parameters

        Returns:
            List of job dictionaries
        """
        try:
            from jobspy import scrape_jobs

            # Determine which sites to search
            sites_to_search = self._get_sites_to_search(params.site_name)

            if not sites_to_search:
                logger.warning("No supported sites to search with jobspy")
                return []

            # Prepare jobspy parameters
            jobspy_params = {
                'site_name': sites_to_search,
                'search_term': params.search_term,
                'location': params.location or "Australia",
                'results_wanted': params.num_jobs,
                'hours_old': params.hours_old,
                'country_indeed': params.country_code or 'australia'
            }

            logger.info(f"Searching with jobspy: {jobspy_params}")

            # Run jobspy in a separate thread (it's not async)
            jobspy_results = await asyncio.to_thread(scrape_jobs, **jobspy_params)

            if jobspy_results is None or jobspy_results.empty:
                logger.warning(f"No results from jobspy for sites: {sites_to_search}")
                return []

            # Convert DataFrame to list of dictionaries
            results = []
            for _, row in jobspy_results.iterrows():
                job_data = self._convert_jobspy_row(row, params.search_term)
                results.append(job_data)

            logger.info(f"Jobspy returned {len(results)} jobs")
            return results

        except ImportError:
            logger.error("jobspy library not installed")
            raise ScrapingFailedError("jobspy", "Library not installed")
        except Exception as e:
            logger.error(f"Error in jobspy scraping: {str(e)}")
            raise ScrapingFailedError("jobspy", str(e))

    def _get_sites_to_search(self, site_name) -> List[str]:
        """
        Determine which sites to search based on site_name parameter

        Args:
            site_name: Site name (string, list, or None)

        Returns:
            List of site names to search
        """
        if site_name is None:
            return self.SUPPORTED_SITES

        if isinstance(site_name, str):
            site = site_name.lower()
            return [site] if self.supports_site(site) else []

        if isinstance(site_name, list):
            return [
                site.lower() for site in site_name
                if self.supports_site(site.lower())
            ]

        return []

    def _convert_jobspy_row(self, row, search_term: str) -> Dict:
        """
        Convert jobspy DataFrame row to job dictionary

        Args:
            row: Pandas DataFrame row
            search_term: Search term used

        Returns:
            Job dictionary
        """
        return {
            "title": row.get("title") or "",
            "company": row.get("company") or "Unknown Company",
            "location": row.get("location") or "",
            "date_posted": self._format_date(row.get("date_posted")),
            "url": row.get("job_url") or "",
            "source": row.get("site", "").lower(),
            "search_term": search_term,
            "description": row.get("description") or "",
            "salary_min": row.get("min_amount"),
            "salary_max": row.get("max_amount"),
            "job_type": row.get("job_type"),
        }

    def _format_date(self, date_posted) -> str:
        """
        Format date_posted from jobspy to string

        Args:
            date_posted: Date from jobspy (can be various types)

        Returns:
            Formatted date string
        """
        if date_posted is None:
            return "Recently"

        try:
            # If it's a datetime, convert to string
            if hasattr(date_posted, 'strftime'):
                return date_posted.strftime('%Y-%m-%d')
            return str(date_posted)
        except Exception as e:
            logger.debug(f"Error formatting date: {str(e)}")
            return "Recently"

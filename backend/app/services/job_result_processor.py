"""
Job Result Processor
Handles post-processing of job search results
"""
import logging
from typing import List, Dict
from app.interfaces.job_scraper_interface import IJobResultProcessor

logger = logging.getLogger(__name__)


class JobResultProcessor(IJobResultProcessor):
    """
    Processes and enhances job search results

    Implements Single Responsibility Principle - focused on result processing only
    """

    def sort_by_date(self, results: List[Dict], sort_order: str) -> List[Dict]:
        """
        Sort job results by date

        Args:
            results: List of job dictionaries
            sort_order: 'asc' or 'desc'

        Returns:
            Sorted list of jobs (modifies in place and returns)
        """
        def get_date_value(job: Dict) -> int:
            """Extract numeric value from date string for sorting"""
            date_str = str(job.get('date_posted', '')).lower()

            # Immediate postings
            if any(term in date_str for term in ['just now', 'today', 'hours ago']):
                return 0

            # Yesterday
            if 'yesterday' in date_str:
                return 1

            # Days ago
            if 'days ago' in date_str or 'day ago' in date_str:
                try:
                    days = int(''.join(filter(str.isdigit, date_str)))
                    return days
                except ValueError:
                    return 1000

            # Weeks ago
            if 'week' in date_str:
                try:
                    weeks = int(''.join(filter(str.isdigit, date_str)) or '1')
                    return 7 * weeks
                except ValueError:
                    return 7

            # Months ago
            if 'month' in date_str:
                try:
                    months = int(''.join(filter(str.isdigit, date_str)) or '1')
                    return 30 * months
                except ValueError:
                    return 30

            # Unknown or very old
            return 9999

        # Sort in place
        results.sort(
            key=get_date_value,
            reverse=(sort_order.lower() != 'asc')
        )

        return results

    def filter_duplicates(self, results: List[Dict]) -> List[Dict]:
        """
        Remove duplicate job postings

        Considers jobs duplicate if they have the same URL or
        same title + company combination

        Args:
            results: List of job dictionaries

        Returns:
            Deduplicated list of jobs
        """
        seen_urls = set()
        seen_job_identifiers = set()
        unique_jobs = []

        for job in results:
            url = job.get('url', '').strip()
            title = job.get('title', '').strip().lower()
            company = job.get('company', '').strip().lower()

            # Create unique identifier
            job_identifier = f"{title}|{company}"

            # Check for duplicates
            is_duplicate = False

            if url and url in seen_urls:
                is_duplicate = True
            elif job_identifier in seen_job_identifiers:
                is_duplicate = True

            if not is_duplicate:
                if url:
                    seen_urls.add(url)
                seen_job_identifiers.add(job_identifier)
                unique_jobs.append(job)
            else:
                logger.debug(f"Filtered duplicate job: {title} at {company}")

        duplicates_removed = len(results) - len(unique_jobs)
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate jobs")

        return unique_jobs

    def calculate_relevance(self, job: Dict, search_term: str) -> float:
        """
        Calculate relevance score for a job

        Scoring factors:
        - Title match: 40%
        - Description match: 30%
        - Company match: 10%
        - Recency: 20%

        Args:
            job: Job dictionary
            search_term: Search term used

        Returns:
            Relevance score between 0 and 1
        """
        try:
            score = 0.0
            search_keywords = search_term.lower().split()

            title = job.get('title', '').lower()
            description = job.get('description', '').lower()
            company = job.get('company', '').lower()

            # Title matching (40 points max)
            title_matches = sum(1 for keyword in search_keywords if keyword in title)
            title_score = min(0.4, (title_matches / len(search_keywords)) * 0.4)
            score += title_score

            # Description matching (30 points max)
            if description:
                desc_matches = sum(1 for keyword in search_keywords if keyword in description)
                desc_score = min(0.3, (desc_matches / len(search_keywords)) * 0.3)
                score += desc_score

            # Company matching (10 points max)
            company_matches = sum(1 for keyword in search_keywords if keyword in company)
            company_score = min(0.1, (company_matches / len(search_keywords)) * 0.1)
            score += company_score

            # Recency score (20 points max)
            recency_score = self._calculate_recency_score(job.get('date_posted', ''))
            score += recency_score * 0.2

            return min(1.0, score)

        except Exception as e:
            logger.error(f"Error calculating relevance: {str(e)}")
            return 0.5  # Default score on error

    def _calculate_recency_score(self, date_str: str) -> float:
        """
        Calculate recency score from date string

        Args:
            date_str: Date posted string

        Returns:
            Score between 0 and 1 (1 = most recent)
        """
        date_str_lower = str(date_str).lower()

        if any(term in date_str_lower for term in ['just now', 'today', 'hours ago']):
            return 1.0
        elif 'yesterday' in date_str_lower:
            return 0.9
        elif 'days ago' in date_str_lower or 'day ago' in date_str_lower:
            try:
                days = int(''.join(filter(str.isdigit, date_str_lower)))
                return max(0.5, 1.0 - (days / 30))
            except ValueError:
                return 0.5
        elif 'week' in date_str_lower:
            return 0.4
        elif 'month' in date_str_lower:
            return 0.2
        else:
            return 0.1

    def enrich_results(self, results: List[Dict], search_term: str) -> List[Dict]:
        """
        Enrich job results with additional data

        Adds relevance scores and normalizes data

        Args:
            results: List of job dictionaries
            search_term: Search term used

        Returns:
            Enriched list of jobs
        """
        enriched = []
        for job in results:
            # Calculate relevance
            job['relevance_score'] = self.calculate_relevance(job, search_term)

            # Normalize data
            job['title'] = job.get('title', 'Unknown Title')
            job['company'] = job.get('company', 'Unknown Company')
            job['location'] = job.get('location', 'Unknown Location')
            job['date_posted'] = job.get('date_posted', 'Recently')

            enriched.append(job)

        return enriched

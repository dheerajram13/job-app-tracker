"""
Job Scraper Interface - Contract for job scraping implementations
Follows Interface Segregation Principle (ISP) and Dependency Inversion Principle (DIP)
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pydantic import BaseModel


class JobSearchParams(BaseModel):
    """Job search parameters DTO (Data Transfer Object)"""
    search_term: str
    location: Optional[str] = "Australia"
    num_jobs: Optional[int] = 30
    site_name: Optional[str] = None
    sort_order: Optional[str] = "desc"
    country_code: Optional[str] = "australia"
    fetch_description: Optional[bool] = False
    use_proxies: Optional[bool] = False
    hours_old: Optional[int] = None


class JobData(BaseModel):
    """Job data transfer object"""
    title: str
    company: str
    location: Optional[str] = None
    date_posted: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    search_term: Optional[str] = None
    detailed_description: Optional[str] = None


class IJobScraper(ABC):
    """
    Job Scraper Interface

    Defines the contract for all job scraping implementations.
    Implementations can be: JobspyScraper, LinkedInScraper, IndeedScraper, etc.
    """

    @abstractmethod
    async def search(self, params: JobSearchParams) -> List[Dict]:
        """
        Search for jobs based on search parameters

        Args:
            params: Job search parameters

        Returns:
            List of job dictionaries
        """
        pass

    @abstractmethod
    def supports_site(self, site_name: str) -> bool:
        """
        Check if this scraper supports a specific site

        Args:
            site_name: Name of the job site

        Returns:
            True if supported, False otherwise
        """
        pass


class IJobParser(ABC):
    """
    Job Parser Interface

    Defines the contract for parsing job postings from URLs
    """

    @abstractmethod
    async def parse(self, url: str) -> Dict:
        """
        Parse job details from a URL

        Args:
            url: Job posting URL

        Returns:
            Dictionary containing parsed job data
        """
        pass


class IJobDescriptionFetcher(ABC):
    """
    Job Description Fetcher Interface

    Separated concern for fetching detailed job descriptions
    """

    @abstractmethod
    async def fetch(self, url: str) -> str:
        """
        Fetch detailed job description from URL

        Args:
            url: Job posting URL

        Returns:
            Job description text
        """
        pass


class IJobResultProcessor(ABC):
    """
    Job Result Processor Interface

    Handles post-processing of job search results
    """

    @abstractmethod
    def sort_by_date(self, results: List[Dict], sort_order: str) -> List[Dict]:
        """
        Sort job results by date

        Args:
            results: List of job dictionaries
            sort_order: 'asc' or 'desc'

        Returns:
            Sorted list of jobs
        """
        pass

    @abstractmethod
    def filter_duplicates(self, results: List[Dict]) -> List[Dict]:
        """
        Remove duplicate job postings

        Args:
            results: List of job dictionaries

        Returns:
            Deduplicated list of jobs
        """
        pass

    @abstractmethod
    def calculate_relevance(self, job: Dict, search_term: str) -> float:
        """
        Calculate relevance score for a job

        Args:
            job: Job dictionary
            search_term: Search term used

        Returns:
            Relevance score between 0 and 1
        """
        pass

import os
import asyncio
import random
import json
import logging
import time
from typing import Dict, List, Optional, Union
from pydantic import BaseModel
import httpx
from fastapi import BackgroundTasks
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup
import pandas as pd
from jobspy import scrape_jobs

logger = logging.getLogger(__name__)

class JobSearchParams(BaseModel):
    """Model for job search parameters"""
    search_term: str
    location: Optional[str] = "Australia"
    num_jobs: Optional[int] = 30
    site_name: Optional[Union[str, List[str]]] = None  # Can be a string or a list of strings
    sort_order: Optional[str] = "desc"
    country_code: Optional[str] = "australia"
    fetch_description: Optional[bool] = False  # Whether to fetch detailed job descriptions
    use_proxies: Optional[bool] = False  # Whether to use proxies
    hours_old: Optional[int] = None  # Filter jobs posted within the last X hours (jobspy)

class JobScraperService:
    """Job scraper service with extended site support and jobspy integration"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Proxies configuration (disabled by default)
        self.proxies = []
        
        # Configure site-specific scraping parameters for custom scraping
        self.site_configs = {
            "linkedin": {
                "search_url": "https://www.linkedin.com/jobs/search/?keywords={search_term}&location={location}&start={start}",
                "results_selector": ".jobs-search__results-list li",
                "title_selector": "h3.base-search-card__title",
                "company_selector": "h4.base-search-card__subtitle",
                "location_selector": ".job-search-card__location",
                "link_selector": ".base-card__full-link",
                "date_selector": ".job-search-card__listdate",
                "pages": [0, 25, 50]
            },
            "indeed": {
                "search_url": "https://www.indeed.com/jobs?q={search_term}&l={location}&start={start}",
                "results_selector": ".jobsearch-ResultsList .result",
                "title_selector": ".jobTitle span",
                "company_selector": ".companyName",
                "location_selector": ".companyLocation",
                "link_selector": ".jcs-JobTitle",
                "date_selector": ".date",
                "pages": [0, 10, 20, 30]
            },
            "glassdoor": {
                "search_url": "https://www.glassdoor.com/Job/jobs.htm?sc.keyword={search_term}&locT=C&locId=1147401",
                "results_selector": ".react-job-listing",
                "title_selector": ".job-title",
                "company_selector": ".employer-name",
                "location_selector": ".location",
                "link_selector": ".jobLink",
                "date_selector": ".listing-age",
                "pages": [0, 1, 2]
            },
            "google": {
                "search_url": "https://www.google.com/search?q={search_term}+jobs+in+{location}&ibp=htl;jobs",
                "results_selector": ".iFjolb",
                "title_selector": ".BjJfJf",
                "company_selector": ".vNEEBe",
                "location_selector": ".Qk80Jf",
                "link_selector": "a.pMhGee",
                "date_selector": ".LL4CDc",
                "pages": [0]
            }
        }
        
        # Map jobspy site names to your site_configs
        self.jobspy_site_mapping = {
            "linkedin": "linkedin",
            "indeed": "indeed",
            "glassdoor": "glassdoor",
            "google": "google",
            "zip_recruiter": "zip_recruiter"
        }

    async def search_jobs(self, params: JobSearchParams) -> List[Dict]:
        """Search for jobs based on parameters using jobspy and custom scraping"""
        try:
            logger.info(f"Searching for jobs across sites: {params.site_name}")
            
            # Determine which sites to use jobspy for
            jobspy_sites = []
            custom_sites = []
            
            if isinstance(params.site_name, str):
                site = params.site_name.lower()
                if site in self.jobspy_site_mapping:
                    jobspy_sites.append(site)
                else:
                    custom_sites.append(site)
            elif isinstance(params.site_name, list):
                # Filter to valid site names only
                sites_to_search = [site.lower() for site in params.site_name 
                                  if site.lower() in self.site_configs]
                # If list is empty after filtering, use all sites
                sites_to_search = sites_to_search or list(self.site_configs.keys())
                
                for site in sites_to_search:
                    if site in self.jobspy_site_mapping:
                        jobspy_sites.append(site)
                    else:
                        custom_sites.append(site)
            else:
                # If no sites specified, use all configured sites
                jobspy_sites = [site for site in self.jobspy_site_mapping.keys()]
                custom_sites = [site for site in self.site_configs.keys() 
                              if site not in jobspy_sites]
            
            logger.info(f"Using jobspy for sites: {jobspy_sites}")
            logger.info(f"Using custom scraping for sites: {custom_sites}")
            
            all_results = []
            
            # Search using jobspy
            if jobspy_sites:
                try:
                    from jobspy import scrape_jobs
                    
                    # Convert params to jobspy format
                    jobspy_params = {
                        'search_terms': [params.search_term],
                        'location': params.location or "Australia",  # Default to Australia if not provided
                        'num_jobs': params.num_jobs,
                        'sites': jobspy_sites,
                        'hours_old': params.hours_old,
                        'fetch_description': params.fetch_description
                    }
                    
                    # Run jobspy in a separate thread since it's not async
                    jobspy_results = await asyncio.to_thread(scrape_jobs, **jobspy_params)
                    if jobspy_results is not None and not jobspy_results.empty:
                        for _, row in jobspy_results.iterrows():
                            # Handle None values from jobspy
                            title = row.get("title") or ""
                            company = row.get("company") or "Unknown Company"
                            location = row.get("location") or params.location or ""
                            date_posted = row.get("date_posted") or "Recently"
                            url = row.get("job_url") or ""
                            source = self.jobspy_site_mapping.get(row.get("site", ""), row.get("site", ""))
                            
                            job_data = {
                                "title": title,
                                "company": company,
                                "location": location,
                                "date_posted": date_posted,
                                "url": url,
                                "source": source,
                                "search_term": params.search_term
                            }
                            if params.fetch_description and row.get("description"):
                                job_data["detailed_description"] = row.get("description")
                            all_results.append(job_data)
                        logger.info(f"Found {len(jobspy_results)} jobs using jobspy")
                    else:
                        logger.warning(f"No results returned from jobspy for sites: {jobspy_sites}")
                except Exception as e:
                    logger.error(f"Error using jobspy: {str(e)}")
            
            # Search using custom scraping
            if custom_sites:
                for site in custom_sites:
                    try:
                        site_results = await self._search_site_page(site, params, 0)
                        all_results.extend(site_results)
                    except Exception as e:
                        logger.error(f"Error searching {site}: {str(e)}")
                        continue
            
            # Sort results by date if requested
            if params.sort_order:
                all_results = self._sort_results_by_date(all_results, params.sort_order)
            
            logger.info(f"Total jobs found: {len(all_results)}")
            return all_results
            
        except Exception as e:
            logger.error(f"Error in search_jobs: {str(e)}")
            return []
    
    async def _fetch_job_description(self, url: str) -> str:
        """Fetch detailed job description from a job posting URL"""
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                selectors = [
                    ".job-description",
                    ".description-content",
                    "#job-details",
                    ".job-details",
                    "[data-test='job-description']",
                    "[data-test='description']"
                ]
                
                for selector in selectors:
                    desc_elem = soup.select_one(selector)
                    if desc_elem:
                        return desc_elem.get_text(strip=True)
                
                main_content = soup.select_one("main") or soup.select_one("article") or soup.body
                if main_content:
                    for elem in main_content.select("nav, header, footer, script, style"):
                        elem.decompose()
                    return main_content.get_text(separator=' ', strip=True)
                    
                return "Description not available"
                
        except Exception as e:
            logger.error(f"Error fetching job description from {url}: {str(e)}")
            return "Error fetching description"
    
    def _sort_results_by_date(self, results: List[Dict], sort_order: str):
        """Sort results by date posted"""
        def get_date_value(job):
            date_str = str(job.get('date_posted', '')).lower()
            
            if 'just now' in date_str or 'today' in date_str or 'hours ago' in date_str:
                return 0
            elif 'yesterday' in date_str:
                return 1
            elif 'days ago' in date_str:
                try:
                    days = int(''.join(filter(str.isdigit, date_str)))
                    return days
                except ValueError:
                    return 1000
            elif 'week' in date_str:
                return 7 * (1 if 'a week' in date_str else 
                         int(''.join(filter(str.isdigit, date_str)) or 1))
            elif 'month' in date_str:
                return 30 * (1 if 'a month' in date_str else 
                          int(''.join(filter(str.isdigit, date_str)) or 1))
            else:
                return 9999
        
        results.sort(
            key=get_date_value, 
            reverse=sort_order.lower() != 'asc'
        )
            
    async def _search_site_page(self, site_name: str, params: JobSearchParams, page_start: int) -> List[Dict]:
        """Search a specific page of a job site (custom scraping)"""
        config = self.site_configs[site_name]
        results = []
        
        try:
            url = config["search_url"].format(
                search_term=params.search_term.replace(' ', '+'),
                location=params.location.replace(' ', '+') if params.location else '',
                start=page_start
            )
            
            logger.info(f"Scraping jobs from {site_name} using URL: {url}")
            
            client_options = {
                'headers': self.headers,
                'timeout': 30.0,
                'follow_redirects': True
            }
            
            if params.use_proxies and self.proxies:
                proxy = random.choice(self.proxies)
                if proxy != "localhost":
                    client_options['proxies'] = {
                        'http://': f'http://{proxy}',
                        'https://': f'http://{proxy}'
                    }
            
            async with httpx.AsyncClient(**client_options) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                job_listings = soup.select(config["results_selector"])
                
                logger.info(f"Found {len(job_listings)} job listings on {site_name} page {page_start}")
                
                for job in job_listings:
                    try:
                        title_elem = job.select_one(config["title_selector"])
                        company_elem = job.select_one(config["company_selector"])
                        location_elem = job.select_one(config["location_selector"])
                        link_elem = job.select_one(config["link_selector"])
                        date_elem = job.select_one(config["date_selector"])
                        
                        if not title_elem:
                            continue
                            
                        title = title_elem.get_text().strip()
                        company = company_elem.get_text().strip() if company_elem else "Unknown Company"
                        location = location_elem.get_text().strip() if location_elem else params.location
                        link = link_elem.get('href') if link_elem else ""
                        
                        if link and not link.startswith('http'):
                            if site_name == "linkedin":
                                link = f"https://www.linkedin.com{link}"
                            elif site_name == "indeed":
                                link = f"https://www.indeed.com{link}"
                            elif site_name == "glassdoor":
                                link = f"https://www.glassdoor.com{link}"
                        
                        date_posted = date_elem.get_text().strip() if date_elem else "Recently"
                        
                        job_data = {
                            "title": title,
                            "company": company,
                            "location": location,
                            "date_posted": date_posted,
                            "url": link,
                            "source": site_name,
                            "search_term": params.search_term
                        }
                        
                        results.append(job_data)
                        
                    except Exception as e:
                        logger.error(f"Error processing job listing from {site_name}: {str(e)}")
                        continue
                
                return results
                
        except Exception as e:
            logger.error(f"Error in job search: {str(e)}")
            return []

class JobScraperBackgroundTask:
    """Background task handler for job scraping"""
    def __init__(self):
        self.scraper = JobScraperService()
        self.active_tasks = {}
        self.loop = None

    def start_job_search(self, task_id: str, params: JobSearchParams):
        """Start a job search in the background"""
        try:
            logger.info(f"Starting background job search task: {task_id}")
            self.active_tasks[task_id] = {
                "status": "processing",
                "progress": 0,
                "results": [],
                "task": None
            }
            
            # Create a new task
            task = asyncio.create_task(
                self._run_job_search(task_id, params)
            )
            self.active_tasks[task_id]["task"] = task
            
        except Exception as e:
            logger.error(f"Error starting job search task {task_id}: {str(e)}")
            self.active_tasks[task_id] = {
                "status": "failed",
                "error": str(e),
                "results": []
            }

    async def _run_job_search(self, task_id: str, params: JobSearchParams):
        """Run the actual job search"""
        try:
            results = await self.scraper.search_jobs(params)
            
            self.active_tasks[task_id] = {
                "status": "completed",
                "results": results,
                "count": len(results)
            }
            logger.info(f"Completed job search task: {task_id}, found {len(results)} jobs")
            
        except Exception as e:
            logger.error(f"Error in background job search task {task_id}: {str(e)}")
            self.active_tasks[task_id] = {
                "status": "failed",
                "error": str(e),
                "results": []
            }

    def get_task_status(self, task_id: str) -> Dict:
        """Get the status of a background task"""
        if not task_id:
            return {"status": "not_found"}

        task_id_str = str(task_id)
        if task_id_str not in self.active_tasks:
            return {"status": "not_found"}

        return self.active_tasks[task_id_str]

# Create singleton instances
job_scraper_service = JobScraperService()
job_scraper_background = JobScraperBackgroundTask()
# import os
# import asyncio
# import random
# import json
# import logging
# import time
# from typing import Dict, List, Optional, Union
# from pydantic import BaseModel
# import httpx
# from fastapi import BackgroundTasks
# from fastapi.responses import JSONResponse
# from bs4 import BeautifulSoup

# logger = logging.getLogger(__name__)

# class JobSearchParams(BaseModel):
#     """Model for job search parameters"""
#     search_term: str
#     location: Optional[str] = "Australia"
#     num_jobs: Optional[int] = 30
#     site_name: Optional[Union[str, List[str]]] = None  # Can be a string or a list of strings
#     sort_order: Optional[str] = "desc"
#     country_code: Optional[str] = "au"
#     fetch_description: Optional[bool] = False  # Whether to fetch detailed job descriptions
#     use_proxies: Optional[bool] = False  # Whether to use proxies

# class JobScraperService:
#     """Job scraper service with extended site support"""
    
#     def __init__(self):
#         self.headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
#             'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
#             'Accept-Language': 'en-US,en;q=0.9',
#             'Accept-Encoding': 'gzip, deflate, br',
#             'Connection': 'keep-alive',
#             'Referer': 'https://www.google.com/',
#             'Sec-Fetch-Dest': 'document',
#             'Sec-Fetch-Mode': 'navigate',
#             'Sec-Fetch-Site': 'cross-site',
#             'Sec-Fetch-User': '?1',
#             'Upgrade-Insecure-Requests': '1'
#         }
        
#         # Proxies configuration (disabled by default)
#         self.proxies = []
        
#         # Configure site-specific scraping parameters
#         self.site_configs = {
#             "linkedin": {
#                 "search_url": "https://www.linkedin.com/jobs/search/?keywords={search_term}&location={location}&start={start}",
#                 "results_selector": ".jobs-search__results-list li",
#                 "title_selector": "h3.base-search-card__title",
#                 "company_selector": "h4.base-search-card__subtitle",
#                 "location_selector": ".job-search-card__location",
#                 "link_selector": ".base-card__full-link",
#                 "date_selector": ".job-search-card__listdate",
#                 "pages": [0, 25, 50]
#             },
#             "indeed": {
#                 "search_url": "https://www.indeed.com/jobs?q={search_term}&l={location}&start={start}",
#                 "results_selector": ".jobsearch-ResultsList .result",
#                 "title_selector": ".jobTitle span",
#                 "company_selector": ".companyName",
#                 "location_selector": ".companyLocation",
#                 "link_selector": ".jcs-JobTitle",
#                 "date_selector": ".date",
#                 "pages": [0, 10, 20, 30]
#             },
#             "glassdoor": {
#                 "search_url": "https://www.glassdoor.com/Job/jobs.htm?sc.keyword={search_term}&locT=C&locId=1147401",
#                 "results_selector": ".react-job-listing",
#                 "title_selector": ".job-title",
#                 "company_selector": ".employer-name",
#                 "location_selector": ".location",
#                 "link_selector": ".jobLink",
#                 "date_selector": ".listing-age",
#                 "pages": [0, 1, 2]
#             },
#             "google": {
#                 "search_url": "https://www.google.com/search?q={search_term}+jobs+in+{location}&ibp=htl;jobs",
#                 "results_selector": ".iFjolb",
#                 "title_selector": ".BjJfJf",
#                 "company_selector": ".vNEEBe",
#                 "location_selector": ".Qk80Jf",
#                 "link_selector": "a.pMhGee",
#                 "date_selector": ".LL4CDc",
#                 "pages": [0]  # Google Jobs doesn't have explicit pagination
#             }
#         }

#     async def search_jobs(self, params: JobSearchParams) -> List[Dict]:
#         """Search for jobs based on parameters"""
#         # Process site_name parameter - can be a string, list, or None
#         sites_to_search = []
#         if params.site_name:
#             if isinstance(params.site_name, str):
#                 if params.site_name.lower() != 'all' and params.site_name.lower() in self.site_configs:
#                     sites_to_search = [params.site_name.lower()]
#                 else:
#                     # 'all' or invalid site name, search all sites
#                     sites_to_search = list(self.site_configs.keys())
#             elif isinstance(params.site_name, list):
#                 # Filter to valid site names only
#                 sites_to_search = [site.lower() for site in params.site_name 
#                                   if site.lower() in self.site_configs]
#                 # If list is empty after filtering, use all sites
#                 if not sites_to_search:
#                     sites_to_search = list(self.site_configs.keys())
#         else:
#             # No site_name specified, search all sites
#             sites_to_search = list(self.site_configs.keys())
            
#         logger.info(f"Searching for jobs across sites: {sites_to_search}")
        
#         all_results = []
        
#         # Calculate how many jobs to request per site
#         jobs_per_site = max(10, params.num_jobs // len(sites_to_search))
        
#         # For each site, create tasks to search multiple pages in parallel
#         for site in sites_to_search:
#             # Add random delay to avoid rate limiting
#             await asyncio.sleep(random.uniform(0.5, 2.0))
            
#             site_config = self.site_configs.get(site)
#             if not site_config:
#                 logger.warning(f"Site config for {site} not found, skipping")
#                 continue
                
#             # Create tasks for each pagination page
#             tasks = [
#                 self._search_site_page(site, params, page_start) 
#                 for page_start in site_config["pages"][:2]  # Limit to first 2 pages
#             ]
            
#             try:
#                 # Execute all page searches for this site in parallel
#                 results_per_page = await asyncio.gather(*tasks)
                
#                 # Combine results from all pages
#                 site_results = []
#                 for page_results in results_per_page:
#                     if page_results:  # Check for None or empty list
#                         site_results.extend(page_results)
                    
#                 # Add site results to overall results
#                 all_results.extend(site_results[:jobs_per_site])  # Limit results per site
                
#                 # Fetch detailed descriptions if requested (and not already in results)
#                 if params.fetch_description and site == 'linkedin' and site_results:
#                     try:
#                         # Only fetch for the first few jobs to avoid rate limiting
#                         for job in site_results[:min(5, len(site_results))]:
#                             if job.get('url') and not job.get('detailed_description'):
#                                 # Add delay between requests
#                                 await asyncio.sleep(random.uniform(1.0, 3.0))
#                                 job['detailed_description'] = await self._fetch_job_description(job['url'])
#                     except Exception as e:
#                         logger.error(f"Error fetching job descriptions: {str(e)}")
                
#             except Exception as e:
#                 logger.error(f"Error searching {site}: {str(e)}")
                
#             # Break early if we've found enough jobs
#             if len(all_results) >= params.num_jobs:
#                 break
                
#         # Sort results by date if requested
#         if params.sort_order:
#             self._sort_results_by_date(all_results, params.sort_order)
            
#         # Limit results to requested number
#         return all_results[:params.num_jobs]
    
#     async def _fetch_job_description(self, url: str) -> str:
#         """Fetch detailed job description from a job posting URL"""
#         try:
#             async with httpx.AsyncClient(headers=self.headers, timeout=30.0) as client:
#                 response = await client.get(url)
#                 response.raise_for_status()
                
#                 soup = BeautifulSoup(response.text, 'html.parser')
                
#                 # Look for job description in various common containers
#                 selectors = [
#                     ".job-description",
#                     ".description-content",
#                     "#job-details",
#                     ".job-details",
#                     "[data-test='job-description']",
#                     "[data-test='description']"
#                 ]
                
#                 for selector in selectors:
#                     desc_elem = soup.select_one(selector)
#                     if desc_elem:
#                         return desc_elem.get_text(strip=True)
                
#                 # Fallback to a more generic approach if specific selectors fail
#                 main_content = soup.select_one("main") or soup.select_one("article") or soup.body
#                 if main_content:
#                     # Remove navigational elements
#                     for elem in main_content.select("nav, header, footer, script, style"):
#                         elem.decompose()
                    
#                     # Get text from the remaining content
#                     return main_content.get_text(separator=' ', strip=True)
                    
#                 return "Description not available"
                
#         except Exception as e:
#             logger.error(f"Error fetching job description from {url}: {str(e)}")
#             return "Error fetching description"
    
#     def _sort_results_by_date(self, results: List[Dict], sort_order: str):
#         """Sort results by date posted"""
#         def get_date_value(job):
#             # Try to extract and normalize the date
#             date_str = job.get('date_posted', '').lower()
            
#             # Common patterns like "3 days ago", "Posted yesterday", etc.
#             if 'just now' in date_str or 'today' in date_str or 'hours ago' in date_str:
#                 return 0  # Most recent
#             elif 'yesterday' in date_str:
#                 return 1
#             elif 'days ago' in date_str:
#                 try:
#                     days = int(''.join(filter(str.isdigit, date_str)))
#                     return days
#                 except ValueError:
#                     return 1000  # Unknown but has "days ago"
#             elif 'week' in date_str:
#                 return 7 * (1 if 'a week' in date_str else 
#                          int(''.join(filter(str.isdigit, date_str)) or 1))
#             elif 'month' in date_str:
#                 return 30 * (1 if 'a month' in date_str else 
#                           int(''.join(filter(str.isdigit, date_str)) or 1))
#             else:
#                 return 9999  # Unknown date format
        
#         # Sort the results list in place
#         results.sort(
#             key=get_date_value, 
#             reverse=sort_order.lower() != 'asc'  # desc = newest first (lowest value)
#         )
            
#     async def _search_site_page(self, site_name: str, params: JobSearchParams, page_start: int) -> List[Dict]:
#         """Search a specific page of a job site"""
#         config = self.site_configs[site_name]
#         results = []
        
#         try:
#             url = config["search_url"].format(
#                 search_term=params.search_term.replace(' ', '+'),
#                 location=params.location.replace(' ', '+') if params.location else '',
#                 start=page_start
#             )
            
#             logger.info(f"Scraping jobs from {site_name} using URL: {url}")
            
#             # Configure client options
#             client_options = {
#                 'headers': self.headers,
#                 'timeout': 30.0,
#                 'follow_redirects': True
#             }
            
#             # Add proxy if configured
#             if params.use_proxies and self.proxies:
#                 proxy = random.choice(self.proxies)
#                 if proxy != "localhost":
#                     client_options['proxies'] = {
#                         'http://': f'http://{proxy}',
#                         'https://': f'http://{proxy}'
#                     }
            
#             async with httpx.AsyncClient(**client_options) as client:
#                 response = await client.get(url)
#                 response.raise_for_status()
                
#                 soup = BeautifulSoup(response.text, 'html.parser')
#                 job_listings = soup.select(config["results_selector"])
                
#                 logger.info(f"Found {len(job_listings)} job listings on {site_name} page {page_start}")
                
#                 for job in job_listings:
#                     try:
#                         # Extract job details
#                         title_elem = job.select_one(config["title_selector"])
#                         company_elem = job.select_one(config["company_selector"])
#                         location_elem = job.select_one(config["location_selector"])
#                         link_elem = job.select_one(config["link_selector"])
#                         date_elem = job.select_one(config["date_selector"])
                        
#                         if not title_elem:
#                             continue
                            
#                         title = title_elem.get_text().strip()
#                         company = company_elem.get_text().strip() if company_elem else "Unknown Company"
#                         location = location_elem.get_text().strip() if location_elem else params.location
#                         link = link_elem.get('href') if link_elem else ""
                        
#                         # Normalize link (some sites have relative URLs)
#                         if link and not link.startswith('http'):
#                             if site_name == "linkedin":
#                                 link = f"https://www.linkedin.com{link}"
#                             elif site_name == "indeed":
#                                 link = f"https://www.indeed.com{link}"
#                             elif site_name == "glassdoor":
#                                 link = f"https://www.glassdoor.com{link}"
                        
#                         # Extract posting date
#                         date_posted = date_elem.get_text().strip() if date_elem else "Recently"
                        
#                         # Create job data object
#                         job_data = {
#                             "title": title,
#                             "company": company,
#                             "location": location,
#                             "date_posted": date_posted,
#                             "url": link,
#                             "source": site_name,
#                             "search_term": params.search_term
#                         }
                        
#                         results.append(job_data)
                        
#                     except Exception as e:
#                         logger.error(f"Error processing job listing from {site_name}: {str(e)}")
#                         continue
                
#                 return results
                
#         except Exception as e:
#             logger.error(f"Error scraping jobs from {site_name} page {page_start}: {str(e)}")
#             return []

# class JobScraperBackgroundTask:
#     """Background task handler for job scraping"""
    
#     def __init__(self):
#         self.scraper = JobScraperService()
#         self.active_tasks = {}
    
#     async def start_job_search(self, task_id: str, params: JobSearchParams):
#         """Start a job search in the background"""
#         try:
#             logger.info(f"Starting background job search task: {task_id}")
#             self.active_tasks[task_id] = {
#                 "status": "processing",
#                 "progress": 0,
#                 "results": []
#             }
            
#             results = await self.scraper.search_jobs(params)
            
#             # Store results in memory (in production, save to database)
#             self.active_tasks[task_id] = {
#                 "status": "completed",
#                 "results": results,
#                 "count": len(results)
#             }
#             logger.info(f"Completed job search task: {task_id}, found {len(results)} jobs")
            
#         except Exception as e:
#             logger.error(f"Error in background job search task: {str(e)}")
#             self.active_tasks[task_id] = {
#                 "status": "failed",
#                 "error": str(e),
#                 "results": []
#             }
    
#     def get_task_status(self, task_id: str) -> Dict:
#         """Get the status of a background task"""
#         if task_id not in self.active_tasks:
#             return {"status": "not_found"}
            
#         return self.active_tasks[task_id]

# # Create a singleton instance
# job_scraper_service = JobScraperService()
# job_scraper_background = JobScraperBackgroundTask()
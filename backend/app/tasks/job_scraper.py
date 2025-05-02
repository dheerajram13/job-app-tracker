from celery import shared_task
from app.services.job_scraper import JobScraperService
import logging
from app.database import SessionLocal
from sqlalchemy.orm import Session
from typing import Dict, List
import json

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def scrape_jobs_task(self, task_id: str, params: Dict) -> Dict:
    """
    Celery task to scrape jobs
    
    Args:
        task_id: Unique identifier for this task
        params: Job search parameters
    
    Returns:
        Dict containing task status and results
    """
    try:
        # Create database session
        db = SessionLocal()
        
        # Convert params to JobSearchParams
        from app.services.job_scraper import JobSearchParams
        search_params = JobSearchParams(**params)
        
        # Initialize job scraper
        scraper = JobScraperService()
        
        # Start job search
        results = scraper.search_jobs(search_params)
        
        # Store results in database
        for job_data in results:
            try:
                from app.models.job import Job
                job = Job(
                    title=job_data.get('title', ''),
                    company=job_data.get('company', ''),
                    location=job_data.get('location', ''),
                    url=job_data.get('url', ''),
                    source=job_data.get('source', ''),
                    date_posted=job_data.get('date_posted', ''),
                    search_term=job_data.get('search_term', '')
                )
                db.add(job)
            except Exception as e:
                logger.error(f"Error saving job to database: {str(e)}")
        
        db.commit()
        
        # Update task status
        self.update_state(state='SUCCESS', meta={'results': results})
        
        return {
            'status': 'completed',
            'results': results,
            'count': len(results)
        }
        
    except Exception as e:
        logger.error(f"Error in job scraping task {task_id}: {str(e)}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        return {
            'status': 'failed',
            'error': str(e)
        }
    finally:
        if 'db' in locals():
            db.close()

@shared_task
async def check_job_status() -> None:
    """
    Periodic task to check status of running jobs
    """
    try:
        # Implementation for checking job status
        pass
    except Exception as e:
        logger.error(f"Error checking job status: {str(e)}")

@shared_task
async def periodic_scrape_jobs(
    search_terms: List[str],
    location: str,
    num_jobs: int,
    sites: List[str],
    hours_old: int,
    fetch_description: bool
) -> None:
    """
    Periodic task to scrape jobs with default parameters
    
    Args:
        search_terms: List of job titles to search for
        location: Location to search in
        num_jobs: Number of jobs to fetch per search
        sites: List of job boards to search
        hours_old: Maximum age of jobs in hours
        fetch_description: Whether to fetch job descriptions
    """
    try:
        # Create database session
        db = SessionLocal()
        
        # Initialize job scraper
        scraper = JobScraperService()
        
        for search_term in search_terms:
            # Create search parameters
            params = JobSearchParams(
                search_term=search_term,
                location=location,
                num_jobs=num_jobs,
                site_name=sites,
                hours_old=hours_old,
                fetch_description=fetch_description,
                sort_order="desc",
                country_code="au"
            )
            
            logger.info(f"Starting periodic job scraping for: {search_term} on sites: {sites}")
            
            # Run the job search
            results = scraper.search_jobs(params)
            
            # Store results in database
            for job_data in results:
                try:
                    from app.models.job import Job
                    job = Job(
                        title=job_data.get('title', ''),
                        company=job_data.get('company', ''),
                        location=job_data.get('location', ''),
                        url=job_data.get('url', ''),
                        source=job_data.get('source', ''),
                        date_posted=job_data.get('date_posted', ''),
                        search_term=job_data.get('search_term', '')
                    )
                    db.add(job)
                except Exception as e:
                    logger.error(f"Error saving job to database: {str(e)}")
        
        db.commit()
        logger.info(f"Completed periodic job scraping - found {len(results)} jobs")
        
    except Exception as e:
        logger.error(f"Error in periodic job scraping: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()

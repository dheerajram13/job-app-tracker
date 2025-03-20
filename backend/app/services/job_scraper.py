# app/services/job_scraper.py
import logging
import pandas as pd
import time
import random
from datetime import datetime
from jobspy import scrape_jobs
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sqlalchemy.orm import Session
from fastapi import Depends, BackgroundTasks
from app.models.job import Job
from app.database import get_db
from typing import List, Optional, Dict
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Ensure NLTK resources are available
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

class JobSpyScraper:
    def __init__(self):
        """Initialize the JobSpy scraper"""
        self.stop_words = set(stopwords.words('english'))
        self.common_skills = [
            'python', 'java', 'javascript', 'js', 'typescript', 'ts', 'c#', 'c++', 
            'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring', 
            'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'oracle',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform',
            'git', 'ci/cd', 'jenkins', 'github', 'gitlab',
            'machine learning', 'ml', 'ai', 'deep learning', 'nlp',
            'data science', 'data analysis', 'statistics', 'data visualization',
            'html', 'css', 'sass', 'less',
            'agile', 'scrum', 'kanban', 'jira',
            'rest', 'api', 'graphql', 'microservices',
            'testing', 'tdd', 'junit', 'selenium'
        ]
    
    def extract_skills(self, description: str) -> List[str]:
        """Extract skills from job description using NLP techniques"""
        if not description or not isinstance(description, str):
            return []
        
        # Convert description to lowercase
        description_lower = description.lower()
        
        # Tokenize text
        tokens = word_tokenize(description_lower)
        
        # Remove stopwords
        filtered_tokens = [word for word in tokens if word.isalpha() and word not in self.stop_words]
        
        # Extract skills
        found_skills = []
        
        # Check for individual skills
        for skill in self.common_skills:
            if ' ' in skill:  # Multi-word skill
                if skill in description_lower:
                    found_skills.append(skill)
            else:  # Single word skill
                if skill in filtered_tokens:
                    found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates
    
    def calculate_relevance_score(self, job_data: Dict, search_query: str) -> float:
        """Calculate relevance score between 0-100 for a job"""
        score = 0
        
        # Title match with search query (0-40 points)
        title = job_data.get('title', '')
        
        if search_query and title:
            # Simple partial matching algorithm
            search_terms = search_query.lower().split()
            title_lower = title.lower()
            
            matches = sum(term in title_lower for term in search_terms)
            title_match_ratio = (matches / len(search_terms)) * 100 if search_terms else 0
            score += title_match_ratio * 0.4  # Max 40 points
        
        # Skills (0-40 points)
        skills = job_data.get('skills', [])
        skill_count = len(skills) if isinstance(skills, list) else 0
        score += min(skill_count * 4, 40)  # 4 points per skill, max 40 points
        
        # Recency (0-20 points)
        date_posted = job_data.get('date', '')
        if date_posted and isinstance(date_posted, str):
            try:
                # Extract days from strings like "5 days ago"
                if 'days ago' in date_posted:
                    days_ago = int(re.search(r'(\d+)', date_posted).group(1))
                    recency_score = max(0, 20 - days_ago)  # Newer is better
                    score += recency_score
                else:
                    # Default to 10 points if we can't parse the date
                    score += 10
            except:
                # Default to 10 points if there's an error
                score += 10
        
        return min(score, 100)  # Cap at 100

    async def scrape_jobs(self, 
                    search_terms: List[str], 
                    db: Session,
                    location: str = "Australia", 
                    results_wanted: int = 20, 
                    hours_old: int = 24) -> Dict:
        """
        Scrape jobs using JobSpy for multiple search terms and store in database
        
        Args:
            search_terms: List of job titles to search for
            db: Database session
            location: Location to search in
            results_wanted: Maximum number of results per search term
            hours_old: Only return jobs posted within this many hours
        """
        logger.info(f"Starting job scraping for {len(search_terms)} search terms")
        
        job_count = {
            "new": 0,
            "updated": 0,
            "total": 0
        }
        
        for search_term in search_terms:
            try:
                logger.info(f"Scraping jobs for '{search_term}' in {location}")
                
                # Use JobSpy to scrape jobs
                results = scrape_jobs(
                    site_name=["indeed", "linkedin", "zip_recruiter", "glassdoor", "google"],
                    search_term=search_term,
                    location=location,
                    results_wanted=results_wanted,
                    hours_old=hours_old,
                    country_indeed='Australia'
                )
                
                if results.empty:
                    logger.warning(f"No jobs found for '{search_term}'")
                    continue
                
                logger.info(f"Found {len(results)} jobs for '{search_term}'")
                job_count["total"] += len(results)
                
                # Process each job and save to database
                for _, job_data in results.iterrows():
                    try:
                        # Extract skills
                        skills = self.extract_skills(job_data.get('description', ''))
                        
                        # Calculate relevance score
                        relevance_score = self.calculate_relevance_score(job_data, search_term)
                        
                        # Check if job already exists by URL
                        existing_job = db.query(Job).filter(Job.url == job_data.get('url')).first()
                        
                        if existing_job:
                            # Update existing job
                            existing_job.title = job_data.get('title', existing_job.title)
                            existing_job.company = job_data.get('company', existing_job.company)
                            existing_job.description = job_data.get('description', existing_job.description)
                            existing_job.location = job_data.get('location', '')
                            existing_job.relevance_score = relevance_score
                            existing_job.skills = ','.join(skills)
                            existing_job.is_scraped = True
                            existing_job.search_query = search_term
                            
                            db.commit()
                            job_count["updated"] += 1
                            
                            logger.debug(f"Updated existing job: {job_data.get('title')} at {job_data.get('company')}")
                        else:
                            # Create new job
                            new_job = Job(
                                title=job_data.get('title', ''),
                                company=job_data.get('company', ''),
                                description=job_data.get('description', ''),
                                url=job_data.get('url', ''),
                                status="Found",  # Custom status for scraped jobs
                                date_applied=datetime.now(),
                                notes=f"Job found via JobSpy search for '{search_term}'",
                                location=job_data.get('location', ''),
                                salary_range=job_data.get('salary', ''),
                                relevance_score=relevance_score,
                                skills=','.join(skills),
                                is_scraped=True,
                                search_query=search_term
                            )
                            db.add(new_job)
                            db.commit()
                            job_count["new"] += 1
                            
                            logger.debug(f"Added new job: {job_data.get('title')} at {job_data.get('company')}")
                        
                    except Exception as e:
                        db.rollback()
                        logger.error(f"Error processing job {job_data.get('title', 'Unknown')}: {str(e)}")
                
                # Sleep to avoid rate limiting
                sleep_time = random.uniform(2, 5)
                logger.debug(f"Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error scraping jobs for '{search_term}': {str(e)}")
        
        logger.info(f"Job scraping complete. New: {job_count['new']}, Updated: {job_count['updated']}, Total: {job_count['total']}")
        return job_count

    def get_scraped_jobs(self, 
                         db: Session,
                         search_query: Optional[str] = None,
                         min_relevance: Optional[float] = None,
                         skills: Optional[List[str]] = None,
                         applied: Optional[bool] = None,
                         limit: int = 50,
                         offset: int = 0):
        """Get scraped jobs with filtering"""
        try:
            # Start with the base query
            query = db.query(Job).filter(Job.is_scraped == True)
            
            # Apply filters
            if search_query:
                query = query.filter(Job.search_query == search_query)
            
            if min_relevance is not None:
                query = query.filter(Job.relevance_score >= min_relevance)
            
            if skills:
                # Filter for jobs containing any of the specified skills
                from sqlalchemy import or_
                skill_conditions = []
                for skill in skills:
                    skill_conditions.append(Job.skills.contains(skill))
                
                if skill_conditions:
                    query = query.filter(or_(*skill_conditions))
            
            if applied is not None:
                if applied:
                    query = query.filter(Job.status == "Applied")
                else:
                    query = query.filter(Job.status != "Applied")
            
            # Sort by relevance score
            query = query.order_by(Job.relevance_score.desc())
            
            # Apply pagination
            total = query.count()
            jobs = query.limit(limit).offset(offset).all()
            
            return jobs, total
            
        except Exception as e:
            logger.error(f"Error retrieving scraped jobs: {str(e)}")
            return [], 0
    
    def get_top_skills(self, db: Session, limit: int = 20):
        """Get the most common skills from scraped jobs"""
        try:
            # Get all skills from jobs
            results = db.query(Job.skills).filter(
                Job.is_scraped == True,
                Job.skills.isnot(None),
                Job.skills != ''
            ).all()
            
            # Count skill occurrences
            skill_counts = {}
            for row in results:
                if row[0]:  # if skills is not None
                    for skill in row[0].split(','):
                        skill = skill.strip().lower()
                        if skill:
                            skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
            # Sort by count and take top skills
            top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
            
            return [skill for skill, _ in top_skills]
        except Exception as e:
            logger.error(f"Error retrieving top skills: {str(e)}")
            return []

# API integration functions

def start_job_scraping(
    background_tasks: BackgroundTasks,
    search_terms: List[str],
    db: Session = Depends(get_db),
    location: str = "Australia",
    results_wanted: int = 20,
    hours_old: int = 24
):
    """Start a job scraping task in the background"""
    scraper = JobSpyScraper()
    
    # Add the task to run in the background
    background_tasks.add_task(
        scraper.scrape_jobs,
        search_terms=search_terms,
        db=db,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old
    )
    
    return {"message": f"Job scraping started for {len(search_terms)} search terms"}

# Initialize on startup
def setup_scheduled_scraping(app):
    """Configure scheduled job scraping on app startup"""
    @app.on_event("startup")
    async def startup_scheduled_scraping():
        # This could be expanded to load search terms from configuration
        # and set up a recurring job using a scheduler
        logger.info("Initializing job scraper on startup")
import logging
import jwt
import json
import requests
import uuid
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from app.database import SessionLocal, engine
from app.models import job, user, resume
from app.services.job_parser import job_parser
from app.services.job_scraper import JobSearchParams, job_scraper_service, job_scraper_background
from app.tasks.job_scraper import scrape_jobs_task
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import List, Optional, Dict
import os
import base64
import asyncio
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# Enhanced logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Pydantic models for request validation
class JobCreate(BaseModel):
    title: str
    company: str
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    status: str = "Applied"
    notes: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    url: Optional[HttpUrl] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class URLRequest(BaseModel):
    url: str

class ScrapeRequest(BaseModel):
    search_terms: List[str]
    location: Optional[str] = "Australia"
    num_jobs: Optional[int] = 30
    sites: Optional[List[str]] = None
    hours_old: Optional[int] = None
    fetch_description: Optional[bool] = False

app = FastAPI(title="Job Application Tracker API", version="2.0.0")

# Environment configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT verification utilities
def ensure_bytes(key):
    if isinstance(key, str):
        key = key.encode('utf-8')
    return key

def decode_value(val):
    decoded = base64.urlsafe_b64decode(ensure_bytes(val + '=' * (4 - len(val) % 4)))
    return int.from_bytes(decoded, 'big')

def get_public_key_from_jwk(jwk):
    e = decode_value(jwk['e'])
    n = decode_value(jwk['n'])
    
    numbers = RSAPublicNumbers(e=e, n=n)
    key = numbers.public_key(backend=default_backend())
    
    pem = key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return pem

# Cache for JWKS
JWKS_CACHE = {}

async def get_public_key(token):
    try:
        token_header = jwt.get_unverified_header(token)
        kid = token_header.get('kid')
        
        if kid not in JWKS_CACHE:
            logger.info(f"Fetching JWKS from Auth0 for kid: {kid}")
            jwks_url = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'
            jwks = requests.get(jwks_url).json()
            
            signing_key = None
            for key in jwks['keys']:
                if key['kid'] == kid:
                    signing_key = key
                    break
            
            if signing_key:
                public_key = get_public_key_from_jwk(signing_key)
                JWKS_CACHE[kid] = public_key
            else:
                raise HTTPException(status_code=401, detail="Unable to find appropriate key")
        
        return JWKS_CACHE[kid]
    except Exception as e:
        logger.error(f"Error getting public key: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        logger.debug(f"Verifying token: {token[:10]}... (length: {len(token)})")
        logger.debug(f"Using AUTH0_DOMAIN: {AUTH0_DOMAIN}, AUTH0_API_AUDIENCE: {AUTH0_API_AUDIENCE}")
        
        # Get the token header to extract kid
        token_header = jwt.get_unverified_header(token)
        logger.debug(f"Token header: {token_header}")
        
        # Get public key
        public_key = await get_public_key(token)
        logger.debug(f"Retrieved public key for kid: {token_header.get('kid')}")
        
        # Decode and verify token
        payload = jwt.decode(
            token,
            key=public_key,
            algorithms=["RS256"],
            audience=AUTH0_API_AUDIENCE,
            issuer=f'https://{AUTH0_DOMAIN}/'
        )
        
        logger.info("Token verified successfully")
        logger.debug(f"Token payload: {payload}")
        return payload
        
    except jwt.ExpiredSignatureError as e:
        logger.error(f"Token verification failed: Expired signature - {str(e)}")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidAudienceError as e:
        logger.error(f"Token verification failed: Invalid audience - {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid audience")
    except jwt.InvalidIssuerError as e:
        logger.error(f"Token verification failed: Invalid issuer - {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid issuer")
    except jwt.InvalidTokenError as e:
        logger.error(f"Token verification failed: Invalid token - {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token verification failed: Unexpected error - {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Token verification failed")

# Database dependency
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create database tables
job.Base.metadata.create_all(bind=engine)
user.Base.metadata.create_all(bind=engine)
resume.Base.metadata.create_all(bind=engine)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.post("/api/jobs/")
async def create_job(job_data: dict, db: Session = Depends(get_db)):
    try:
        if user_id := job_data.get("user_id"):
            existing_user = db.query(user.User).filter(user.User.id == user_id).first()
            
            if not existing_user:
                new_user = user.User(
                    id=user_id,
                    email=job_data.get("user_email", ""),
                    full_name=job_data.get("user_name", "")
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
        
        db_job = job.Job(
            title=job_data.get("title"),
            company=job_data.get("company"),
            description=job_data.get("description", ""),
            url=job_data.get("url", ""),
            status=job_data.get("status", "Applied"),
            notes=job_data.get("notes", ""),
            date_applied=datetime.utcnow(),
            user_id=user_id if user_id else None
        )
        
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
        
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/")
async def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(job.Job).all()
    
    result = []
    for j in jobs:
        job_data = {
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "description": j.description,
            "url": j.url,
            "status": j.status,
            "dateApplied": j.date_applied.isoformat() if j.date_applied else None,
            "notes": j.notes
        }
        result.append(job_data)
        
    return result

@app.get("/api/jobs/{job_id}")
async def get_job(
    job_id: int, 
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    db_job = db.query(job.Job).filter(
        job.Job.id == job_id,
        job.Job.user_id == user_data.get("sub")
    ).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job

@app.put("/api/jobs/{job_id}")
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    db_job = db.query(job.Job).filter(
        job.Job.id == job_id,
        job.Job.user_id == user_data.get("sub")
    ).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    for key, value in job_data.dict(exclude_unset=True).items():
        setattr(db_job, key, value)
    
    try:
        db.commit()
        db.refresh(db_job)
        return db_job
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating job: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating job")

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    try:
        logger.info(f"Attempting to delete job with ID: {job_id}")
        
        db_job = db.query(job.Job).filter(job.Job.id == job_id).first()
        
        if db_job:
            logger.info(f"Found job to delete: {db_job.title} at {db_job.company}")
        else:
            logger.warning(f"No job found with ID: {job_id}")
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
        
        db.delete(db_job)
        db.commit()
        
        logger.info(f"Successfully deleted job with ID: {job_id}")
        return {"message": "Job deleted successfully", "id": job_id}
        
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")

@app.post("/api/jobs/parse-url")
async def parse_job_url(
    request_data: URLRequest,
    user_data: dict = Depends(verify_token)
):
    try:
        logger.info(f"Starting to parse URL: {request_data.url}")
        job_data = await job_parser.parse_job_posting(request_data.url)
        return job_data
    except ValueError as e:
        logger.error(f"Error parsing job URL: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "2.0.0"
    }

async def get_current_user(token: str = Depends(oauth2_scheme)):
    return await verify_token(token)

# Job scraping routes
@app.post("/api/jobs/scrape")
async def scrape_jobs(
    request: ScrapeRequest,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    """Trigger job scraping for specified search terms"""
    try:
        task_ids = []
        for search_term in request.search_terms:
            # Handle site_name parameter - it can be a single string or a list
            site_name = request.sites
            if isinstance(site_name, str):
                site_name = [site_name]
            
            params = JobSearchParams(
                search_term=search_term,
                location=request.location,
                num_jobs=request.num_jobs,
                site_name=site_name,
                hours_old=request.hours_old,
                fetch_description=request.fetch_description,
                sort_order="desc",
                country_code="au"
            )
            
            logger.info(f"Starting job scraping task for: {search_term} on sites: {site_name}")
            
            # Convert params to dict for Celery
            params_dict = params.dict()
            
            # Start the Celery task
            task = scrape_jobs_task.delay(str(uuid.uuid4()), params_dict)
            task_ids.append(task.id)
        
        return {
            "task_ids": task_ids,
            "status": "processing",
            "message": f"Started job scraping for {len(request.search_terms)} search terms"
        }
    except Exception as e:
        logger.error(f"Error starting job scraping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/scrape/{task_id}")
async def get_scraped_jobs(task_id: str):
    """Get the results of a job scraping task"""
    task_status = job_scraper_background.get_task_status(task_id)
    
    if task_status["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Task not found")
        
    return task_status

@app.post("/api/jobs/add-scraped")
async def add_scraped_job(
    job_data: dict,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    """Add a scraped job to the database"""
    try:
        user_id = user_data.get("sub")
        existing_user = db.query(user.User).filter(user.User.id == user_id).first()
        
        if not existing_user:
            new_user = user.User(
                id=user_id,
                email=user_data.get("email", ""),
                full_name=user_data.get("name", "")
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
        
        db_job = job.Job(
            title=job_data.get("title"),
            company=job_data.get("company"),
            description=job_data.get("description", job_data.get("detailed_description", "")),
            url=job_data.get("url", ""),
            status="Bookmarked",
            notes=f"Source: {job_data.get('source', 'Job Board')}\nLocation: {job_data.get('location', 'Not specified')}",
            date_applied=None,
            user_id=user_id,
            location=job_data.get("location", "")
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job
    except Exception as e:
        logger.error(f"Error adding scraped job: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/advanced-search")
async def advanced_search(
    params: dict,
    background_tasks: BackgroundTasks,
    user_data: dict = Depends(verify_token)
):
    """Enhanced job search with multiple parameters"""
    task_id = str(uuid.uuid4())
    
    search_params = JobSearchParams(
        search_term=params.get("search_term", ""),
        location=params.get("location", "Australia"),
        site_name=params.get("sites", None),
        num_jobs=params.get("num_jobs", 50),
        sort_order=params.get("sort_order", "desc"),
        fetch_description=params.get("fetch_description", False),
        use_proxies=params.get("use_proxies", False),
        hours_old=params.get("hours_old", None)
    )
    
    logger.info(f"Received advanced job search request: {search_params.search_term}")
    
    background_tasks.add_task(
        job_scraper_background.start_job_search,
        task_id=task_id,
        params=search_params
    )
    
    return {
        "task_id": task_id,
        "status": "processing",
        "message": f"Started advanced job search for '{search_params.search_term}'"
    }

@app.get("/api/jobs/scraped")
async def get_scraped_jobs(
    search_query: Optional[str] = Query(None, description="Filter by job title, company, or description"),
    min_relevance: Optional[float] = Query(None, ge=0, le=1, description="Minimum relevance score (0-1)"),
    skills: Optional[str] = Query(None, description="Comma-separated list of required skills"),
    applied: Optional[bool] = Query(None, description="Filter by application status"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    """Get scraped jobs with filtering options"""
    try:
        user_id = user_data.get("sub")
        query = db.query(job.Job).filter(job.Job.user_id == user_id)
        
        if applied is not None:
            query = query.filter(job.Job.status == ("Applied" if applied else "Bookmarked"))
        
        if search_query:
            search_filter = or_(
                job.Job.title.ilike(f"%{search_query}%"),
                job.Job.company.ilike(f"%{search_query}%"),
                job.Job.description.ilike(f"%{search_query}%")
            )
            query = query.filter(search_filter)
        
        if skills:
            skills_list = [s.strip().lower() for s in skills.split(',')]
            for skill in skills_list:
                query = query.filter(job.Job.description.ilike(f"%{skill}%"))
        
        total = query.count()
        jobs = query.order_by(desc(job.Job.date_applied)).offset(offset).limit(limit).all()
        
        results = []
        for job_item in jobs:
            skills_list = []
            if job_item.description and skills:
                for skill in skills_list:
                    if skill.lower() in job_item.description.lower():
                        skills_list.append(skill)
            
            date_applied = job_item.date_applied.isoformat() if job_item.date_applied else None
            
            job_details = {
                "id": job_item.id,
                "title": job_item.title,
                "company": job_item.company,
                "description": job_item.description,
                "url": job_item.url,
                "status": job_item.status,
                "location": job_item.location,
                "skills": skills_list,
                "job_type": None,  # Not stored in DB, can be extracted from description if needed
                "salary_range": job_item.salary_range,
                "date_applied": date_applied,
                "date_scraped": None,  # Not stored in DB, can be added as a field if needed
                "relevance_score": 1.0 if min_relevance is None else min_relevance,  # Placeholder
                "search_query": search_query,
                "applied": job_item.status == "Applied"
            }
            results.append(job_details)
        
        return {
            "jobs": results,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting scraped jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/top-skills")
async def get_top_skills(
    limit: int = Query(20, ge=1, le=100, description="Number of skills to return"),
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    """Get the top skills from all scraped jobs"""
    try:
        user_id = user_data.get("sub")
        # Common skills to look for (can be expanded based on your needs)
        common_skills = [
            "python", "javascript", "java", "sql", "aws", "docker", "kubernetes",
            "react", "node.js", "typescript", "git", "linux", "agile", "scrum",
            "machine learning", "data analysis", "cloud computing", "devops"
        ]
        
        # Count occurrences of each skill in job descriptions
        skill_counts = []
        for skill in common_skills:
            count = db.query(job.Job).filter(
                job.Job.user_id == user_id,
                job.Job.description.ilike(f"%{skill}%")
            ).count()
            if count > 0:
                skill_counts.append({"skill": skill, "count": count})
        
        # Sort by count and limit results
        skill_counts.sort(key=lambda x: x["count"], reverse=True)
        return {"skills": skill_counts[:limit]}
    except Exception as e:
        logger.error(f"Error getting top skills: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
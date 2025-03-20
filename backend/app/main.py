import logging
import jwt
import json
import requests
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from app.database import SessionLocal, engine
from app.models import job, user, resume
from app.services.job_parser import job_parser
from app.services.job_scraper import JobSpyScraper, start_job_scraping
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import List, Optional
import os
import base64
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
        # Get the Key ID from the token header
        token_header = jwt.get_unverified_header(token)
        kid = token_header.get('kid')
        
        # If we don't have the key in cache or it's a different key, fetch it
        if kid not in JWKS_CACHE:
            logger.info(f"Fetching JWKS from Auth0 for kid: {kid}")
            jwks_url = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'
            jwks = requests.get(jwks_url).json()
            
            # Find the signing key in JWKS
            signing_key = None
            for key in jwks['keys']:
                if key['kid'] == kid:
                    signing_key = key
                    break
            
            if signing_key:
                # Convert the JWKS key to PEM format
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
        # Log the token (first few characters)
        logger.info(f"Verifying token: {token[:10]}...")
        
        # Get the public key
        public_key = await get_public_key(token)
        
        # Verify the token
        payload = jwt.decode(
            token,
            key=public_key,
            algorithms=["RS256"],
            audience=AUTH0_API_AUDIENCE,
            issuer=f'https://{AUTH0_DOMAIN}/'
        )
        
        logger.info("Token verified successfully")
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTClaimsError as e:
        logger.error(f"Invalid claims: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token claims")
    except jwt.JWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
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

# Update the create_job endpoint in main.py

@app.post("/api/jobs/")
async def create_job(job_data: dict, db: Session = Depends(get_db)):
    try:
        # If user_id is provided, check if user exists
        if user_id := job_data.get("user_id"):
            existing_user = db.query(user.User).filter(user.User.id == user_id).first()
            
            if not existing_user:
                # Create new user if doesn't exist
                new_user = user.User(
                    id=user_id,  # Using the OAuth ID as user ID
                    email=job_data.get("user_email", ""),  # Add user email if available
                    full_name=job_data.get("user_name", "")  # Add user name if available
                )
                db.add(new_user)
                db.commit()
                db.refresh(new_user)
        
        # Create the job
        db_job = job.Job(
            title=job_data.get("title"),
            company=job_data.get("company"),
            description=job_data.get("description", ""),
            url=job_data.get("url", ""),
            status=job_data.get("status", "Applied"),
            notes=job_data.get("notes", ""),
            date_applied=datetime.utcnow(),
            user_id=user_id if user_id else None  # Make user_id optional
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
async def get_jobs(
    status: Optional[str] = None,
    search: Optional[str] = None,
    sortBy: Optional[str] = "dateApplied",
    db: Session = Depends(get_db)
):
    query = db.query(job.Job)

    # Filter by status if provided and not 'all'
    if status and status.lower() != 'all':
        query = query.filter(job.Job.status == status)

    # Handle search
    if search:
        search_filter = or_(
            job.Job.title.ilike(f"%{search}%"),
            job.Job.company.ilike(f"%{search}%"),
            job.Job.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    # Handle sorting
    if sortBy == "dateApplied":
        query = query.order_by(desc(job.Job.date_applied))
    elif sortBy == "company":
        query = query.order_by(job.Job.company)
    elif sortBy == "title":
        query = query.order_by(job.Job.title)
    elif sortBy == "status":
        query = query.order_by(job.Job.status)

    jobs = query.all()
    formatted_jobs = []
    for j in jobs:
        job_dict = {
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "description": j.description,
            "url": j.url,
            "status": j.status,
            "dateApplied": j.date_applied.isoformat(),
            "notes": j.notes,
            "user_id": j.user_id
        }
        formatted_jobs.append(job_dict)

    return formatted_jobs

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
        
        # Try to fetch the job first
        db_job = db.query(job.Job).filter(job.Job.id == job_id).first()
        
        # Log the query result
        if db_job:
            logger.info(f"Found job to delete: {db_job.title} at {db_job.company}")
        else:
            logger.warning(f"No job found with ID: {job_id}")
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
        
        # Perform the deletion
        db.delete(db_job)
        db.commit()
        
        logger.info(f"Successfully deleted job with ID: {job_id}")
        return {"message": "Job deleted successfully", "id": job_id}
        
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")

# URL parsing endpoint
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

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "2.0.0"
    }


# Scrape jobs endpoint
@app.post("/api/jobs/scrape")
async def scrape_jobs(
    request: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Trigger job scraping for specified search terms"""
    search_terms = request.get("search_terms", [])
    location = request.get("location", "Australia")
    
    return start_job_scraping(
        background_tasks=background_tasks,
        search_terms=search_terms,
        db=db,
        location=location
    )

# Get scraped jobs endpoint
@app.get("/api/jobs/scraped")
async def get_scraped_jobs(
    search_query: Optional[str] = None,
    min_relevance: Optional[float] = Query(None, ge=0, le=100),
    skills: Optional[str] = None,
    applied: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get scraped jobs with optional filtering"""
    scraper = JobSpyScraper()
    
    # Parse skills if provided
    skills_list = None
    if skills:
        skills_list = [s.strip() for s in skills.split(',')]
    
    jobs, total = scraper.get_scraped_jobs(
        db=db,
        search_query=search_query,
        min_relevance=min_relevance,
        skills=skills_list,
        applied=applied,
        limit=limit,
        offset=offset
    )
    
    # Format response
    job_results = []
    for job in jobs:
        skills_array = job.skills.split(',') if job.skills else []
        job_results.append({
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "url": job.url,
            "status": job.status,
            "date_applied": job.date_applied.isoformat() if job.date_applied else None,
            "skills": skills_array,
            "relevance_score": job.relevance_score,
            "search_query": job.search_query,
            "applied": job.status == "Applied"
        })
    
    return {
        "jobs": job_results,
        "total": total,
        "limit": limit,
        "offset": offset
    }

# Mark job as applied
@app.post("/api/jobs/scraped/{job_id}/apply")
async def mark_job_applied(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Mark a scraped job as applied"""
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.status = "Applied"
    db.commit()
    
    return {"message": f"Job {job_id} marked as applied"}

# Get top skills
@app.get("/api/jobs/top-skills")
async def get_top_skills(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """Get the most common skills from scraped jobs"""
    scraper = JobSpyScraper()
    skills = scraper.get_top_skills(db, limit)
    
    return {"skills": skills}
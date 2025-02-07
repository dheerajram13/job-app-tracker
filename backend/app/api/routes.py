from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from app.dependencies import get_db
from app.models.job import Job
from app.schemas.job import JobCreate, JobUpdate, JobInDB
from ..services.job_parser import JobParserService
from app.models.user import User
from app.auth.jwt import get_current_user, requires_permission  
import logging
from pydantic import BaseModel
from aiohttp import ClientTimeout
import aiohttp


logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.get("/health/ollama")
async def check_ollama():
    try:
        timeout = ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": "tinyllama",
                    "prompt": "test",
                    "stream": False
                }
            ) as response:
                if response.status == 200:
                    return {"status": "healthy", "ollama": "connected"}
                return {"status": "unhealthy", "ollama": f"error: {response.status}"}
    except Exception as e:
        return {"status": "unhealthy", "ollama": str(e)}


@router.post("/register")
async def register_user(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)  # From Auth0
):
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            User.auth0_id == current_user.get("sub")
        ).first()
        
        if existing_user:
            return {"message": "User already registered"}
            
        # Create new user
        new_user = User(
            auth0_id=current_user.get("sub"),
            email=current_user.get("email")
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {"message": "User registered successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed"
        )

@router.get(
    "/jobs",
    response_model=List[JobInDB],
    summary="Get all jobs for the authenticated user"
)
async def read_jobs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=100),
    search: Optional[str] = Query(None, description="Search term for job title or company"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(requires_permission(["read:jobs"]))  # Changed auth dependency
):
    """
    Retrieve all jobs for the authenticated user with pagination and search.
    """
    try:
        logger.debug(f"User attempting to fetch jobs: {current_user.get('sub')}")
        
        query = db.query(Job).filter(Job.user_id == current_user.get("sub"))
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Job.title.ilike(search_term)) |
                (Job.company.ilike(search_term))
            )
        
        total = query.count()
        jobs = query.offset(skip).limit(limit).all()
        
        logger.info(f"Retrieved {len(jobs)} jobs for user {current_user.get('sub')}")
        return jobs

    except Exception as e:
        logger.error(f"Error retrieving jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving jobs"
        )

@router.post(
    "/jobs",
    response_model=JobInDB,
    status_code=status.HTTP_201_CREATED
)
async def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(requires_permission(["create:jobs"]))  # Changed auth dependency
):
    """
    Create a new job entry for the authenticated user.
    """
    try:
        logger.debug(f"Received job creation request")
        logger.debug(f"Current user: {current_user}")
        logger.debug(f"Job data: {job.dict()}")
        
        db_job = Job(**job.dict(), user_id=current_user.get("sub"))
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        logger.info(f"Created job {db_job.id} for user {current_user.get('sub')}")
        return db_job

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating job: {str(e)}")
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating job: {str(e)}"
        )

@router.put(
    "/jobs/{job_id}",
    response_model=JobInDB
)
async def update_job(
    job_id: int,
    job: JobUpdate,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(requires_permission(["update:jobs"]))  # Changed auth dependency
):
    """
    Update a specific job for the authenticated user.
    """
    try:
        db_job = db.query(Job).filter(
            Job.id == job_id,
            Job.user_id == current_user.get("sub")
        ).first()
        
        if not db_job:
            logger.warning(f"Job {job_id} not found for user {current_user.get('sub')}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
            
        for key, value in job.dict(exclude_unset=True).items():
            setattr(db_job, key, value)
            
        db.commit()
        db.refresh(db_job)
        
        logger.info(f"Updated job {job_id} for user {current_user.get('sub')}")
        return db_job

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating job"
        )

@router.delete(
    "/jobs/{job_id}",
    response_model=JobInDB
)
async def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(requires_permission(["delete:jobs"]))  # Changed auth dependency
):
    """
    Delete a specific job for the authenticated user.
    """
    try:
        db_job = db.query(Job).filter(
            Job.id == job_id,
            Job.user_id == current_user.get("sub")
        ).first()
        
        if not db_job:
            logger.warning(f"Job {job_id} not found for user {current_user.get('sub')}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
            
        db.delete(db_job)
        db.commit()
        
        logger.info(f"Deleted job {job_id} for user {current_user.get('sub')}")
        return db_job

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting job"
        )


class UrlRequest(BaseModel):
    url: str

@router.post("/jobs/parse-url", response_model=Dict)
async def parse_job_url(
    url_data: UrlRequest,
    current_user: Dict = Depends(requires_permission(["create:jobs"])),  # Added auth requirement
    job_parser: JobParserService = Depends(lambda: JobParserService())
):
    try:
        logger.debug(f"Attempting to parse URL: {url_data.url}")
        job_details = await job_parser.parse_job_details(url_data.url)
        logger.debug(f"Raw job details: {job_details}")
        
        formatted_response = {
            "job_title": job_details.get("job_title"),
            "company_name": job_details.get("company_name"),
            "description": job_details.get("description"),
            "location": job_details.get("location"),
            "salary_range": job_details.get("salary_range"),
            "required_experience": job_details.get("required_experience"),
            "key_skills": job_details.get("key_skills", [])
        }
        
        logger.debug(f"Formatted response: {formatted_response}")
        return formatted_response
        
    except Exception as e:
        logger.error(f"Error parsing job URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
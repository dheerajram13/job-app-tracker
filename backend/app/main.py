import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.database import SessionLocal, engine
from app.models import job, user, resume
from app.services.job_parser import job_parser
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
job.Base.metadata.create_all(bind=engine)
user.Base.metadata.create_all(bind=engine)
resume.Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Job routes
@app.post("/api/jobs/")
async def create_job(job_data: dict, db: Session = Depends(get_db)):
    db_job = job.Job(
        title=job_data.get("title"),
        company=job_data.get("company"),
        description=job_data.get("description", ""),
        url=job_data.get("url", ""),
        status=job_data.get("status", "Applied"),
        notes=job_data.get("notes", ""),
        date_applied=datetime.utcnow()
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

@app.get("/api/jobs/")
async def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(job.Job).all()
    return jobs

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: int, db: Session = Depends(get_db)):
    db_job = db.query(job.Job).filter(job.Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    return db_job

@app.put("/api/jobs/{job_id}")
async def update_job(job_id: int, job_data: dict, db: Session = Depends(get_db)):
    db_job = db.query(job.Job).filter(job.Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    for key, value in job_data.items():
        setattr(db_job, key, value)
    
    db.commit()
    db.refresh(db_job)
    return db_job

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: int, db: Session = Depends(get_db)):
    db_job = db.query(job.Job).filter(job.Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(db_job)
    db.commit()
    return {"message": "Job deleted successfully"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class URLRequest(BaseModel):
    url: str

@app.post("/api/jobs/parse-url")
async def parse_job_url(request: URLRequest):
    try:
        logger.info(f"Starting to parse URL: {request.url}")
        job_data = await job_parser.parse_job_posting(request.url)
        
        # Log the parsed data
        logger.info("Successfully parsed job posting. Details:")
        logger.info(f"Title: {job_data.get('title', 'Not found')}")
        logger.info(f"Company: {job_data.get('company', 'Not found')}")
        logger.info(f"Job Type: {job_data.get('job_type', 'Not found')}")
        logger.info(f"Experience Level: {job_data.get('experience_level', 'Not found')}")
        logger.info(f"Location: {job_data.get('location', 'Not found')}")
        logger.info("Requirements:")
        for req in job_data.get('requirements', []):
            logger.info(f"  - {req}")
        logger.info(f"Description preview: {job_data.get('description', 'Not found')[:200]}...")
        
        return job_data
    except ValueError as e:
        logger.error(f"Error parsing job URL: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
# Resume routes
@app.post("/api/resumes/")
async def create_resume(resume_data: dict, db: Session = Depends(get_db)):
    db_resume = resume.Resume(
        title=resume_data.get("title"),
        file_path=resume_data.get("file_path"),
        file_type=resume_data.get("file_type"),
        description=resume_data.get("description"),
        tags=resume_data.get("tags")
    )
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume

@app.get("/api/resumes/")
async def get_resumes(db: Session = Depends(get_db)):
    resumes = db.query(resume.Resume).filter(resume.Resume.is_active == True).all()
    return resumes

@app.get("/api/resumes/{resume_id}")
async def get_resume(resume_id: int, db: Session = Depends(get_db)):
    db_resume = db.query(resume.Resume).filter(resume.Resume.id == resume_id).first()
    if not db_resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return db_resume

@app.put("/api/resumes/{resume_id}")
async def update_resume(resume_id: int, resume_data: dict, db: Session = Depends(get_db)):
    db_resume = db.query(resume.Resume).filter(resume.Resume.id == resume_id).first()
    if not db_resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Increment version if file is being updated
    if "file_path" in resume_data:
        resume_data["version"] = db_resume.version + 1
    
    for key, value in resume_data.items():
        setattr(db_resume, key, value)
    
    db.commit()
    db.refresh(db_resume)
    return db_resume

@app.delete("/api/resumes/{resume_id}")
async def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    db_resume = db.query(resume.Resume).filter(resume.Resume.id == resume_id).first()
    if not db_resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Soft delete - mark as inactive instead of removing from database
    db_resume.is_active = False
    db.commit()
    return {"message": "Resume deleted successfully"}
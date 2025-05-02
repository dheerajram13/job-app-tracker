from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum

class JobStatus(str, enum.Enum):
    APPLIED = "Applied"
    PHONE_SCREEN = "Phone Screen"
    TECHNICAL = "Technical Interview"
    ONSITE = "On-site"
    OFFER = "Offer"
    REJECTED = "Rejected"


# backend/app/models/job.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(512), nullable=True)
    status = Column(String(50), default="Applied")  # Added 'Scraped' as a possible status
    date_applied = Column(DateTime, nullable=True)  # Nullable for scraped jobs
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    salary_range = Column(String(100), nullable=True)
    user_id = Column(String(255), ForeignKey("users.id"), nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    
    date_scraped = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_scraped = Column(Boolean, default=False)  # Flag to identify scraped jobs
    skills = Column(String, nullable=True)  # Comma-separated skills
    job_type = Column(String, nullable=True)  # Full-time, Part-time, Contract, etc.
    search_query = Column(String, nullable=True)  # The search term used to find this job
    relevance_score = Column(Float, default=0.0)  # Score indicating relevance to search query
    
    # Define the relationships
    user = relationship("User", back_populates="jobs")
    resume = relationship("Resume", back_populates="jobs")
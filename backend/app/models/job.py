from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    company = Column(String)
    description = Column(String, nullable=True)
    url = Column(String, nullable=True)
    status = Column(String, default="Applied")
    date_applied = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Define the relationship to user
    user = relationship("User", back_populates="jobs")
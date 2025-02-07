from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    
    # Define the relationship to jobs
    jobs = relationship("Job", back_populates="user")
    resumes = relationship("Resume", back_populates="user")
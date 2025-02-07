# app/schemas/profile.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ProfileBase(BaseModel):
    full_name: str
    title: Optional[str] = None
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None

class ProfileCreate(ProfileBase):
    pass

class ProfileUpdate(ProfileBase):
    pass

class ProfileInDB(ProfileBase):
    id: int
    user_id: str

    class Config:
        orm_mode = True

class ResumeBase(BaseModel):
    title: str

class ResumeCreate(ResumeBase):
    pass

class Resume(ResumeBase):
    id: int
    upload_date: str
    
    class Config:
        orm_mode = True

class Profile(ProfileInDB):
    resumes: List[Resume] = []
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class JobBase(BaseModel):
    title: str
    company: str
    description: Optional[str] = None
    status: Optional[str] = "Applied"
    date_applied: Optional[datetime] = None
    notes: Optional[str] = None
    resume: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobUpdate(JobBase):
    pass

class JobInDB(JobBase):
    id: int

    class Config:
        orm_mode = True

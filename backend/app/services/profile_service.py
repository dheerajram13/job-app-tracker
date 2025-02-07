# app/services/profile_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
import os
from datetime import datetime

from backend.app.models.resume import Profile, Resume
from app.schemas.profile import ProfileCreate, ProfileUpdate

class ProfileService:
    def __init__(self, db: Session):
        self.db = db

    def get_profile_by_user_id(self, user_id: str) -> Profile:
        return self.db.query(Profile).filter(Profile.user_id == user_id).first()

    def create_profile(self, user_id: str, profile_data: ProfileCreate) -> Profile:
        db_profile = Profile(
            user_id=user_id,
            **profile_data.dict()
        )
        self.db.add(db_profile)
        self.db.commit()
        self.db.refresh(db_profile)
        return db_profile

    def update_profile(self, user_id: str, profile_data: ProfileUpdate) -> Profile:
        profile = self.get_profile_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        for field, value in profile_data.dict().items():
            setattr(profile, field, value)
        
        self.db.commit()
        self.db.refresh(profile)
        return profile

    async def upload_resume(self, user_id: str, title: str, file: UploadFile) -> Resume:
        profile = self.get_profile_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # Create uploads directory if it doesn't exist
        upload_dir = f"uploads/{user_id}"
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        file_path = f"{upload_dir}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        with open(file_path, "wb+") as file_object:
            file_object.write(await file.read())

        # Create resume record
        resume = Resume(
            profile_id=profile.id,
            title=title,
            file_path=file_path,
            upload_date=datetime.now().isoformat()
        )
        
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def get_resumes(self, user_id: str) -> list[Resume]:
        profile = self.get_profile_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile.resumes

    async def delete_resume(self, user_id: str, resume_id: int):
        profile = self.get_profile_by_user_id(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        resume = self.db.query(Resume).filter(
            Resume.id == resume_id,
            Resume.profile_id == profile.id
        ).first()

        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Delete file
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)

        self.db.delete(resume)
        self.db.commit()
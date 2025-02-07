from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
from datetime import datetime

from app.dependencies import get_db
from app.auth.jwt import get_current_user, requires_permission
from app.schemas.profile import ProfileCreate, Profile, ProfileUpdate, Resume, ResumeCreate
from app.services.profile_service import ProfileService

router = APIRouter()

@router.get(
    "/profile", 
    response_model=Profile,
    summary="Get user profile"
)
async def get_profile(
    current_user: dict = Depends(requires_permission(["read:profile"])),
    db: Session = Depends(get_db)
):
    """
    Retrieve the profile for the authenticated user.
    """
    service = ProfileService(db)
    profile = service.get_profile_by_user_id(current_user["sub"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.post(
    "/profile", 
    response_model=Profile,
    summary="Create user profile"
)
async def create_profile(
    profile: ProfileCreate,
    current_user: dict = Depends(requires_permission(["create:profile"])),
    db: Session = Depends(get_db)
):
    """
    Create a new profile for the authenticated user.
    """
    service = ProfileService(db)
    return service.create_profile(current_user["sub"], profile)

@router.put(
    "/profile", 
    response_model=Profile,
    summary="Update user profile"
)
async def update_profile(
    profile: ProfileUpdate,
    current_user: dict = Depends(requires_permission(["update:profile"])),
    db: Session = Depends(get_db)
):
    """
    Update the profile for the authenticated user.
    """
    service = ProfileService(db)
    return service.update_profile(current_user["sub"], profile)

@router.post(
    "/resumes", 
    response_model=Resume,
    summary="Upload resume"
)
async def upload_resume(
    title: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(requires_permission(["create:resume"])),
    db: Session = Depends(get_db)
):
    """
    Upload a new resume for the authenticated user.
    """
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=400, 
            detail="Only PDF files are allowed"
        )

    service = ProfileService(db)
    return await service.upload_resume(current_user["sub"], title, file)

@router.get(
    "/resumes", 
    response_model=List[Resume],
    summary="Get user resumes"
)
async def get_resumes(
    current_user: dict = Depends(requires_permission(["read:resume"])),
    db: Session = Depends(get_db)
):
    """
    Retrieve all resumes for the authenticated user.
    """
    service = ProfileService(db)
    return service.get_resumes(current_user["sub"])

@router.delete(
    "/resumes/{resume_id}",
    summary="Delete resume"
)
async def delete_resume(
    resume_id: int,
    current_user: dict = Depends(requires_permission(["delete:resume"])),
    db: Session = Depends(get_db)
):
    """
    Delete a specific resume for the authenticated user.
    """
    service = ProfileService(db)
    await service.delete_resume(current_user["sub"], resume_id)
    return {"message": "Resume deleted successfully"}
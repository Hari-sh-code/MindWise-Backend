"""
Pydantic schemas for Job Application endpoints.
"""
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime


class JobBase(BaseModel):
    """Base schema for job application."""
    company_name: str
    job_title: str
    job_description: str
    resume_drive_link: str
    user_notes: Optional[str] = None


class JobCreate(JobBase):
    """Schema for creating a job application."""
    status: Optional[str] = "pending"


class AIAnalysisResult(BaseModel):
    """Schema for AI analysis results."""
    job_summary: str
    required_skills: List[str]
    resume_skills: List[str]
    skill_gap: List[str]
    match_score: int = Field(..., ge=0, le=100)
    preparation_tips: List[str]


class JobResponse(JobBase):
    """Schema for job application response."""
    id: int
    ai_analysis: Optional[AIAnalysisResult] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Schema for paginated job list response."""
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int


class JobUpdate(BaseModel):
    """Schema for updating job application."""
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    job_description: Optional[str] = None
    user_notes: Optional[str] = None
    status: Optional[str] = None

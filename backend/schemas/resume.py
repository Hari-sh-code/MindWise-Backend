"""
Pydantic schemas for Resume Optimization Engine.
Handles resume generation, optimization, ATS scoring, and comparison.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class ResumeGenerateRequest(BaseModel):
    """Request schema for resume generation."""
    job_description: str = Field(..., description="Job description to optimize resume for")
    job_application_id: Optional[int] = Field(None, description="Optional job application ID to link resume")


class ResumeUpdateRequest(BaseModel):
    """Request schema for updating resume data."""
    resume_data: Dict[str, Any] = Field(..., description="Updated resume data structure")


class ResumeComparisonRequest(BaseModel):
    """Request schema for comparing two resumes."""
    old_resume_id: int = Field(..., description="ID of older/original resume")
    new_resume_id: int = Field(..., description="ID of new/optimized resume")


# ============================================================================
# COMPONENT SCHEMAS (for resume_data structure)
# ============================================================================

class ResumeSkill(BaseModel):
    """Skill component in resume."""
    name: str
    level: Optional[str] = None  # e.g., "Expert", "Intermediate", "Beginner"


class ResumeProject(BaseModel):
    """Project component in resume."""
    title: str
    description: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    github_url: Optional[str] = None


class ResumeExperience(BaseModel):
    """Experience component in resume."""
    company_name: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None


class ResumeEducation(BaseModel):
    """Education component in resume."""
    college: str
    degree: str
    year: Optional[int] = None


class ResumeCertification(BaseModel):
    """Certification component in resume."""
    title: str
    issuer: str
    issue_date: Optional[str] = None
    credential_url: Optional[str] = None


class ResumePersonal(BaseModel):
    """Personal info section in resume."""
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ResumeDataResponse(BaseModel):
    """Complete resume data structure."""
    personal_info: Optional[ResumePersonal] = None
    summary: Optional[str] = None
    skills: Optional[List[ResumeSkill]] = None
    experience: Optional[List[ResumeExperience]] = None
    education: Optional[List[ResumeEducation]] = None
    certifications: Optional[List[ResumeCertification]] = None
    projects: Optional[List[ResumeProject]] = None
    social_links: Optional[Dict[str, str]] = None


class ResumeResponse(BaseModel):
    """Full resume response with metadata."""
    id: int
    user_id: int
    job_description: str
    resume_data: Dict[str, Any]  # Raw resume data structure
    ats_score: Optional[float] = None
    version: int
    created_at: datetime
    updated_at: datetime
    job_application_id: Optional[int] = None

    class Config:
        from_attributes = True


class ResumeListResponse(BaseModel):
    """Paginated list of resumes."""
    resumes: List[ResumeResponse]
    total: int
    page: int
    page_size: int


# ============================================================================
# COMPARISON & ANALYSIS SCHEMAS
# ============================================================================

class ATSScoreDifference(BaseModel):
    """ATS score comparison."""
    old_score: Optional[float]
    new_score: Optional[float]
    improvement: Optional[float] = None  # new - old
    improvement_percentage: Optional[float] = None


class ResumeComparisonResponse(BaseModel):
    """Comparison between two resume versions."""
    old_resume_id: int
    new_resume_id: int
    old_version: int
    new_version: int
    old_ats_score: Optional[float]
    new_ats_score: Optional[float]
    ats_improvement: Optional[float] = None  # new - old
    ats_improvement_percentage: Optional[float] = None
    created_at: datetime


# ============================================================================
# METADATA & STATUS SCHEMAS
# ============================================================================

class ResumeMetadata(BaseModel):
    """Resume metadata (without full content)."""
    id: int
    user_id: int
    version: int
    ats_score: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

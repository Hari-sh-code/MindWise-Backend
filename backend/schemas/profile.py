"""
Pydantic schemas for Profile Management endpoints.
Strictly matches PostgreSQL DB schema — no extra fields.

DB columns per table:
  user_profiles:       id, user_id, phone, summary, created_at
  user_skills:         id, user_id, skill_name, skill_type, created_at
  user_projects:       id, user_id, title, tech_stack, description, github_url, created_at
  user_experience:     id, user_id, company_name, role, duration, description, created_at
  user_education:      id, user_id, college, degree, year, created_at
  user_certifications: id, user_id, title, issuer, issue_date, credential_id, credential_url, created_at
  user_social_links:   id, user_id, platform, url, created_at
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date


# ============================================================================
# PROFILE SCHEMAS
# ============================================================================

class ProfileBasicCreate(BaseModel):
    """Schema for creating/updating basic profile info."""
    phone: Optional[str] = Field(None, max_length=20)
    summary: Optional[str] = Field(None, max_length=1000)


class ProfileBasicResponse(BaseModel):
    """Schema for basic profile response."""
    id: int
    user_id: int
    phone: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SKILL SCHEMAS
# ============================================================================

class SkillCreate(BaseModel):
    """Schema for creating a skill."""
    skill_name: str = Field(..., max_length=100)
    skill_type: str = Field(..., max_length=50)

    @field_validator('skill_name')
    @classmethod
    def validate_skill_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Skill name cannot be empty')
        return v.strip()


class SkillUpdate(BaseModel):
    """Schema for updating a skill."""
    skill_name: Optional[str] = Field(None, max_length=100)
    skill_type: Optional[str] = Field(None, max_length=50)


class SkillResponse(BaseModel):
    """Schema for skill response."""
    id: int
    user_id: int
    skill_name: str
    skill_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    skills: List[SkillResponse]
    total: int


# ============================================================================
# PROJECT SCHEMAS
# ============================================================================

class ProjectCreate(BaseModel):
    """Schema for creating a project."""
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    tech_stack: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Project title cannot be empty')
        return v.strip()

    @field_validator('github_url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    tech_stack: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)


class ProjectResponse(BaseModel):
    """Schema for project response."""
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    tech_stack: Optional[str] = None
    github_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int


# ============================================================================
# EXPERIENCE SCHEMAS
# ============================================================================

class ExperienceCreate(BaseModel):
    """Schema for creating work experience."""
    company_name: str = Field(..., max_length=200)
    role: str = Field(..., max_length=150)
    duration: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=2000)

    @field_validator('company_name', 'role')
    @classmethod
    def validate_required_fields(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('This field cannot be empty')
        return v.strip()


class ExperienceUpdate(BaseModel):
    """Schema for updating work experience."""
    company_name: Optional[str] = Field(None, max_length=200)
    role: Optional[str] = Field(None, max_length=150)
    duration: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = Field(None, max_length=2000)


class ExperienceResponse(BaseModel):
    """Schema for experience response."""
    id: int
    user_id: int
    company_name: str
    role: str
    duration: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExperienceListResponse(BaseModel):
    experience: List[ExperienceResponse]
    total: int


# ============================================================================
# EDUCATION SCHEMAS
# ============================================================================

class EducationCreate(BaseModel):
    """Schema for creating education."""
    college: str = Field(..., max_length=200)
    degree: str = Field(..., max_length=150)
    year: Optional[int] = Field(None, ge=1900, le=2100)

    @field_validator('college', 'degree')
    @classmethod
    def validate_required_fields(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('This field cannot be empty')
        return v.strip()


class EducationUpdate(BaseModel):
    """Schema for updating education."""
    college: Optional[str] = Field(None, max_length=200)
    degree: Optional[str] = Field(None, max_length=150)
    year: Optional[int] = Field(None, ge=1900, le=2100)


class EducationResponse(BaseModel):
    """Schema for education response."""
    id: int
    user_id: int
    college: str
    degree: str
    year: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EducationListResponse(BaseModel):
    education: List[EducationResponse]
    total: int


# ============================================================================
# CERTIFICATION SCHEMAS
# ============================================================================

class CertificationCreate(BaseModel):
    """Schema for creating a certification."""
    title: str = Field(..., max_length=200)
    issuer: str = Field(..., max_length=200)
    issue_date: Optional[date] = Field(None, max_length=50)
    credential_id: Optional[str] = Field(None, max_length=200)
    credential_url: Optional[str] = Field(None, max_length=500)

    @field_validator('title', 'issuer')
    @classmethod
    def validate_required_fields(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('This field cannot be empty')
        return v.strip()

    @field_validator('credential_url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class CertificationUpdate(BaseModel):
    """Schema for updating a certification."""
    title: Optional[str] = Field(None, max_length=200)
    issuer: Optional[str] = Field(None, max_length=200)
    issue_date: Optional[date] = Field(None, max_length=50)
    credential_id: Optional[str] = Field(None, max_length=200)
    credential_url: Optional[str] = Field(None, max_length=500)


class CertificationResponse(BaseModel):
    """Schema for certification response."""
    id: int
    user_id: int
    title: str
    issuer: str
    issue_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CertificationListResponse(BaseModel):
    certifications: List[CertificationResponse]
    total: int


# ============================================================================
# SOCIAL LINK SCHEMAS
# ============================================================================

class SocialLinkCreate(BaseModel):
    """Schema for creating a social link."""
    platform: str = Field(..., max_length=50)
    url: str = Field(..., max_length=500)
    username: Optional[str] = Field(None, max_length=100)

    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Platform cannot be empty')
        return v.strip().lower()

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v or not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class SocialLinkUpdate(BaseModel):
    """Schema for updating a social link."""
    platform: Optional[str] = Field(None, max_length=50)
    url: Optional[str] = Field(None, max_length=500)
    username: Optional[str] = Field(None, max_length=100)


class SocialLinkResponse(BaseModel):
    """Schema for social link response."""
    id: int
    user_id: int
    platform: str
    url: str
    username: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SocialLinkListResponse(BaseModel):
    social_links: List[SocialLinkResponse]
    total: int


# ============================================================================
# COMPLETE PROFILE RESPONSE  (GET /user/profile)
# ============================================================================

class CompleteProfileResponse(BaseModel):
    """
    Merged profile response for GET /user/profile.
    Returns all profile sections in a single response.
    """
    basic: Optional[ProfileBasicResponse] = None
    skills: List[SkillResponse] = []
    projects: List[ProjectResponse] = []
    experience: List[ExperienceResponse] = []
    education: List[EducationResponse] = []
    certifications: List[CertificationResponse] = []
    social_links: List[SocialLinkResponse] = []


# ============================================================================
# SUMMARY / BULK SCHEMAS
# ============================================================================

class ProfileSummaryResponse(BaseModel):
    user_id: int
    profile_complete: bool
    skills_count: int
    projects_count: int
    experience_count: int
    education_count: int
    certifications_count: int
    social_links_count: int
    completion_percentage: float


class BulkSkillCreate(BaseModel):
    skills: List[SkillCreate] = Field(..., description="List of skills")


class BulkDeleteRequest(BaseModel):
    ids: List[int] = Field(..., description="IDs to delete")


class BulkDeleteResponse(BaseModel):
    deleted_count: int
    message: str

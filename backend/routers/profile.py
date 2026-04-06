"""
Profile Management Router.
Handles all user profile CRUD operations.
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session

from database import get_db
from core.auth import get_current_user
from models.user import User
from schemas.profile import (
    ProfileBasicCreate, ProfileBasicResponse,
    SkillCreate, SkillResponse, SkillUpdate, SkillListResponse,
    ProjectCreate, ProjectResponse, ProjectUpdate, ProjectListResponse,
    ExperienceCreate, ExperienceResponse, ExperienceUpdate, ExperienceListResponse,
    EducationCreate, EducationResponse, EducationUpdate, EducationListResponse,
    CertificationCreate, CertificationResponse, CertificationUpdate, CertificationListResponse,
    SocialLinkCreate, SocialLinkResponse, SocialLinkUpdate, SocialLinkListResponse,
    CompleteProfileResponse, ProfileSummaryResponse, BulkDeleteRequest, BulkDeleteResponse
)
from services.profile_service import profile_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["Profile Management"])


# ============================================================================
# PROFILE BASIC INFO
# ============================================================================

@router.get("/profile", response_model=CompleteProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get complete user profile with all data in a single response.

    Returns:
        CompleteProfileResponse with basic, skills, projects,
        experience, education, certifications, and social_links.
    """
    logger.info(f"Getting complete profile for user {current_user.id}")

    try:
        complete_profile = profile_service.get_complete_profile(current_user.id, db)
        return complete_profile
    except Exception as e:
        logger.exception(f"Error getting complete profile for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )


@router.put("/profile", response_model=ProfileBasicResponse)
async def update_profile(
    profile_data: ProfileBasicCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's basic profile information (phone and summary).

    If profile doesn't exist, it will be created.
    """
    logger.info(f"Updating profile for user {current_user.id}")

    try:
        updated_profile = profile_service.update_profile(
            current_user.id,
            profile_data,
            db
        )
        return updated_profile
    except Exception as e:
        logger.exception(f"Error updating profile for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


# ============================================================================
# SKILLS
# ============================================================================

@router.get("/skills", response_model=SkillListResponse)
async def list_skills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skill_type: Optional[str] = Query(None, description="Filter by skill type")
):
    """
    Get all skills for the current user.
    
    Optional Query Parameters:
        - skill_type: Filter by skill type (technical, soft, language, etc.)
    """
    logger.info(f"Listing skills for user {current_user.id}")
    
    try:
        skills = profile_service.get_skills(current_user.id, db)
        
        # Filter by skill_type if provided
        if skill_type:
            skills = [s for s in skills if s.skill_type.lower() == skill_type.lower()]
        
        return SkillListResponse(skills=skills, total=len(skills))
    except Exception as e:
        logger.exception(f"Error listing skills for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve skills"
        )


@router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new skill.
    
    Raises validation error if skill already exists.
    """
    logger.info(f"Creating skill for user {current_user.id}")
    
    try:
        skill = profile_service.create_skill(current_user.id, skill_data, db)
        return skill
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error creating skill for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create skill"
        )


@router.get("/skills/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific skill."""
    logger.info(f"Getting skill {skill_id} for user {current_user.id}")
    
    try:
        skill = profile_service.get_skill(skill_id, current_user.id, db)
        
        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill {skill_id} not found"
            )
        
        return skill
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting skill {skill_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve skill"
        )


@router.put("/skills/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    skill_data: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a skill."""
    logger.info(f"Updating skill {skill_id} for user {current_user.id}")
    
    try:
        skill = profile_service.update_skill(skill_id, current_user.id, skill_data, db)
        return skill
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error updating skill {skill_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update skill"
        )


@router.delete("/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a skill."""
    logger.info(f"Deleting skill {skill_id} for user {current_user.id}")
    
    try:
        deleted = profile_service.delete_skill(skill_id, current_user.id, db)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Skill {skill_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting skill {skill_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete skill"
        )


# ============================================================================
# PROJECTS
# ============================================================================

@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all projects for the current user."""
    logger.info(f"Listing projects for user {current_user.id}")
    
    try:
        projects = profile_service.get_projects(current_user.id, db)
        return ProjectListResponse(projects=projects, total=len(projects))
    except Exception as e:
        logger.exception(f"Error listing projects for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve projects"
        )


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project."""
    logger.info(f"Creating project for user {current_user.id}")
    
    try:
        project = profile_service.create_project(current_user.id, project_data, db)
        return project
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error creating project for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific project."""
    logger.info(f"Getting project {project_id} for user {current_user.id}")
    
    try:
        project = profile_service.get_project(project_id, current_user.id, db)
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting project {project_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project"
        )


@router.put("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a project."""
    logger.info(f"Updating project {project_id} for user {current_user.id}")
    
    try:
        project = profile_service.update_project(
            project_id, current_user.id, project_data, db
        )
        return project
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error updating project {project_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project."""
    logger.info(f"Deleting project {project_id} for user {current_user.id}")
    
    try:
        deleted = profile_service.delete_project(project_id, current_user.id, db)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting project {project_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )


# ============================================================================
# EXPERIENCE
# ============================================================================

@router.get("/experience", response_model=ExperienceListResponse)
async def list_experience(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all work experience for the current user."""
    logger.info(f"Listing experience for user {current_user.id}")
    
    try:
        experiences = profile_service.get_experience(current_user.id, db)
        return ExperienceListResponse(experience=experiences, total=len(experiences))
    except Exception as e:
        logger.exception(f"Error listing experience for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve experience"
        )


@router.post("/experience", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED)
async def create_experience(
    experience_data: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new work experience entry."""
    logger.info(f"Creating experience for user {current_user.id}")
    
    try:
        experience = profile_service.create_experience(
            current_user.id, experience_data, db
        )
        return experience
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error creating experience for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create experience"
        )


@router.get("/experience/{experience_id}", response_model=ExperienceResponse)
async def get_experience(
    experience_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific experience entry."""
    logger.info(f"Getting experience {experience_id} for user {current_user.id}")
    
    try:
        experience = profile_service.get_experience_entry(
            experience_id, current_user.id, db
        )
        
        if not experience:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experience {experience_id} not found"
            )
        
        return experience
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting experience {experience_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve experience"
        )


@router.put("/experience/{experience_id}", response_model=ExperienceResponse)
async def update_experience(
    experience_id: int,
    experience_data: ExperienceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a work experience entry."""
    logger.info(f"Updating experience {experience_id} for user {current_user.id}")
    
    try:
        experience = profile_service.update_experience(
            experience_id, current_user.id, experience_data, db
        )
        return experience
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error updating experience {experience_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update experience"
        )


@router.delete("/experience/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experience(
    experience_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a work experience entry."""
    logger.info(f"Deleting experience {experience_id} for user {current_user.id}")
    
    try:
        deleted = profile_service.delete_experience(
            experience_id, current_user.id, db
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Experience {experience_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting experience {experience_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete experience"
        )


# ============================================================================
# EDUCATION
# ============================================================================

@router.get("/education", response_model=EducationListResponse)
async def list_education(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all education for the current user."""
    logger.info(f"Listing education for user {current_user.id}")
    
    try:
        educations = profile_service.get_education(current_user.id, db)
        return EducationListResponse(education=educations, total=len(educations))
    except Exception as e:
        logger.exception(f"Error listing education for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve education"
        )


@router.post("/education", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
async def create_education(
    education_data: EducationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new education entry."""
    logger.info(f"Creating education for user {current_user.id}")
    
    try:
        education = profile_service.create_education(
            current_user.id, education_data, db
        )
        return education
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error creating education for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create education"
        )


@router.get("/education/{education_id}", response_model=EducationResponse)
async def get_education(
    education_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific education entry."""
    logger.info(f"Getting education {education_id} for user {current_user.id}")
    
    try:
        education = profile_service.get_education_entry(
            education_id, current_user.id, db
        )
        
        if not education:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Education {education_id} not found"
            )
        
        return education
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting education {education_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve education"
        )


@router.put("/education/{education_id}", response_model=EducationResponse)
async def update_education(
    education_id: int,
    education_data: EducationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an education entry."""
    logger.info(f"Updating education {education_id} for user {current_user.id}")
    
    try:
        education = profile_service.update_education(
            education_id, current_user.id, education_data, db
        )
        return education
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error updating education {education_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update education"
        )


@router.delete("/education/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_education(
    education_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an education entry."""
    logger.info(f"Deleting education {education_id} for user {current_user.id}")
    
    try:
        deleted = profile_service.delete_education(
            education_id, current_user.id, db
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Education {education_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting education {education_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete education"
        )


# ============================================================================
# CERTIFICATIONS
# ============================================================================

@router.get("/certifications", response_model=CertificationListResponse)
async def list_certifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all certifications for the current user."""
    logger.info(f"Listing certifications for user {current_user.id}")
    
    try:
        certifications = profile_service.get_certifications(current_user.id, db)
        return CertificationListResponse(
            certifications=certifications,
            total=len(certifications)
        )
    except Exception as e:
        logger.exception(f"Error listing certifications for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve certifications"
        )


@router.post("/certifications", response_model=CertificationResponse, status_code=status.HTTP_201_CREATED)
async def create_certification(
    cert_data: CertificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new certification."""
    logger.info(f"Creating certification for user {current_user.id}")
    
    try:
        certification = profile_service.create_certification(
            current_user.id, cert_data, db
        )
        return certification
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error creating certification for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create certification"
        )


@router.get("/certifications/{certification_id}", response_model=CertificationResponse)
async def get_certification(
    certification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific certification."""
    logger.info(f"Getting certification {certification_id} for user {current_user.id}")
    
    try:
        certification = profile_service.get_certification(
            certification_id, current_user.id, db
        )
        
        if not certification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Certification {certification_id} not found"
            )
        
        return certification
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting certification {certification_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve certification"
        )


@router.put("/certifications/{certification_id}", response_model=CertificationResponse)
async def update_certification(
    certification_id: int,
    cert_data: CertificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a certification."""
    logger.info(f"Updating certification {certification_id} for user {current_user.id}")
    
    try:
        certification = profile_service.update_certification(
            certification_id, current_user.id, cert_data, db
        )
        return certification
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error updating certification {certification_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update certification"
        )


@router.delete("/certifications/{certification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certification(
    certification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a certification."""
    logger.info(f"Deleting certification {certification_id} for user {current_user.id}")
    
    try:
        deleted = profile_service.delete_certification(
            certification_id, current_user.id, db
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Certification {certification_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting certification {certification_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete certification"
        )


# ============================================================================
# SOCIAL LINKS
# ============================================================================

@router.get("/social-links", response_model=SocialLinkListResponse)
async def list_social_links(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all social links for the current user."""
    logger.info(f"Listing social links for user {current_user.id}")
    
    try:
        links = profile_service.get_social_links(current_user.id, db)
        return SocialLinkListResponse(social_links=links, total=len(links))
    except Exception as e:
        logger.exception(f"Error listing social links for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve social links"
        )


@router.post("/social-links", response_model=SocialLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_social_link(
    link_data: SocialLinkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new social link."""
    logger.info(f"Creating social link for user {current_user.id}")
    
    try:
        link = profile_service.create_social_link(
            current_user.id, link_data, db
        )
        return link
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error creating social link for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create social link"
        )


@router.get("/social-links/{link_id}", response_model=SocialLinkResponse)
async def get_social_link(
    link_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific social link."""
    logger.info(f"Getting social link {link_id} for user {current_user.id}")
    
    try:
        link = profile_service.get_social_link(link_id, current_user.id, db)
        
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Social link {link_id} not found"
            )
        
        return link
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting social link {link_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve social link"
        )


@router.put("/social-links/{link_id}", response_model=SocialLinkResponse)
async def update_social_link(
    link_id: int,
    link_data: SocialLinkUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a social link."""
    logger.info(f"Updating social link {link_id} for user {current_user.id}")
    
    try:
        link = profile_service.update_social_link(
            link_id, current_user.id, link_data, db
        )
        return link
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Error updating social link {link_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update social link"
        )


@router.delete("/social-links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_social_link(
    link_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a social link."""
    logger.info(f"Deleting social link {link_id} for user {current_user.id}")
    
    try:
        deleted = profile_service.delete_social_link(
            link_id, current_user.id, db
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Social link {link_id} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error deleting social link {link_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete social link"
        )


# ============================================================================
# AGGREGATED ENDPOINTS
# ============================================================================

@router.get("/profile-complete", response_model=CompleteProfileResponse)
async def get_complete_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Alias for GET /user/profile — returns complete profile.
    Kept for backwards compatibility.
    """
    logger.info(f"Getting complete profile for user {current_user.id}")

    try:
        complete_profile = profile_service.get_complete_profile(
            current_user.id, db
        )
        return complete_profile
    except Exception as e:
        logger.exception(f"Error getting complete profile for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve complete profile"
        )


@router.get("/profile-summary", response_model=ProfileSummaryResponse)
async def get_profile_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get profile completion summary including counts and completion percentage.
    
    Useful for showing profile progress to user.
    """
    logger.info(f"Getting profile summary for user {current_user.id}")
    
    try:
        summary = profile_service.get_profile_summary(current_user.id, db)
        return summary
    except Exception as e:
        logger.exception(f"Error getting profile summary for user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile summary"
        )

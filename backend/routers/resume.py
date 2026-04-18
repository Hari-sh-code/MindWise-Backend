"""
Resume Optimization Router.
Handles resume generation, ATS scoring, comparison, management, and PDF export.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from database import get_db
from models.user import User
from core.auth import get_current_user
from schemas.resume import (
    ResumeGenerateRequest,
    ResumeUpdateRequest,
    ResumeComparisonRequest,
    ResumeResponse,
    ResumeListResponse,
    ResumeComparisonResponse
)
from services.resume_service import resume_service
from services.pdf_service import pdf_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resume", tags=["Resume Optimization"])


# ============================================================================
# GENERATE RESUME
# ============================================================================

@router.post("/generate", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def generate_resume(
    request: ResumeGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an AI-optimized resume for a job.
    
    Uses Gemini AI to tailor resume based on:
    1. User profile (skills, experience, projects, education)
    2. Job description
    
    AI generates:
    - Tailored professional summary
    - Prioritized relevant skills
    - Achievement-focused experience
    - Relevant projects
    
    ATS Score: Calculated using existing AI analysis (match_score).
    
    Graceful fallback: If AI fails, returns structured default resume from profile.
    
    Flow:
    1. Fetch user profile data
    2. Build and send prompt to Gemini AI
    3. Generate structured resume JSON
    4. Score resume using existing AI analysis
    5. Save to database with automatic versioning
    
    Request Parameters:
    - job_description: Job description text (required, min 50 chars)
    - job_application_id: Optional ID to link resume to job application
    
    Returns:
    - ResumeResponse with resume data, ATS score, and metadata
    
    Raises:
    - 400: Invalid job description (too short, empty)
    - 404: User profile not found
    - 500: Resume generation failed
    """
    try:
        if not request.job_description or len(request.job_description.strip()) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Job description must be at least 50 characters long"
            )
        
        logger.info(f"User {current_user.id} requesting resume generation")
        
        resume = resume_service.generate_resume(
            db=db,
            user_id=current_user.id,
            job_description=request.job_description,
            job_application_id=request.job_application_id
        )
        
        logger.info(f"Successfully generated resume {resume.id} for user {current_user.id}")
        return resume
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Resume generation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Resume generation failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate resume. Please try again later."
        )


# ============================================================================
# LIST RESUMES
# ============================================================================

@router.get("/", response_model=ResumeListResponse)
async def list_resumes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all resumes for the current user.
    
    Returns paginated list of generated resumes sorted by creation date (newest first).
    
    Query Parameters:
    - page: Page number (default: 1)
    - page_size: Items per page (default: 10, max: 100)
    
    Returns:
    - ResumeListResponse with paginated resumes list
    """
    try:
        logger.info(f"User {current_user.id} listing resumes (page {page}, size {page_size})")
        
        result = resume_service.list_resumes(
            db=db,
            user_id=current_user.id,
            page=page,
            page_size=page_size
        )
        
        return ResumeListResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to list resumes for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resumes"
        )


# ============================================================================
# GET SINGLE RESUME
# ============================================================================

@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a single resume by ID.
    
    Only the owner of the resume can access it.
    
    Path Parameters:
    - resume_id: Resume ID
    
    Returns:
    - ResumeResponse with full resume data
    
    Raises:
    - 404: Resume not found or unauthorized
    """
    try:
        logger.info(f"User {current_user.id} retrieving resume {resume_id}")
        
        resume = resume_service.get_resume(
            db=db,
            resume_id=resume_id,
            user_id=current_user.id
        )
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or you don't have access to it"
            )
        
        return resume
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resume {resume_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resume"
        )


# ============================================================================
# UPDATE RESUME
# ============================================================================

@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: int,
    request: ResumeUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update resume data (for editable preview).
    
    Allows editing of resume content while preserving metadata (ATS score, version, etc).
    
    Path Parameters:
    - resume_id: Resume ID
    
    Request Body:
    - resume_data: Updated resume data structure
    
    Returns:
    - Updated ResumeResponse
    
    Raises:
    - 404: Resume not found or unauthorized
    """
    try:
        logger.info(f"User {current_user.id} updating resume {resume_id}")
        
        resume = resume_service.update_resume_data(
            db=db,
            resume_id=resume_id,
            user_id=current_user.id,
            resume_data=request.resume_data
        )
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or you don't have access to it"
            )
        
        logger.info(f"Successfully updated resume {resume_id}")
        return resume
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update resume {resume_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update resume"
        )


# ============================================================================
# COMPARE RESUMES
# ============================================================================

@router.post("/compare", response_model=ResumeComparisonResponse)
async def compare_resumes(
    request: ResumeComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compare two resume versions by ATS score.
    
    Shows ATS score difference and improvement percentage between versions.
    
    Request Body:
    - old_resume_id: ID of original/older resume
    - new_resume_id: ID of optimized/newer resume
    
    Returns:
    - ResumeComparisonResponse with ATS score comparison
    
    Raises:
    - 404: One or both resumes not found
    """
    try:
        logger.info(f"User {current_user.id} comparing resumes {request.old_resume_id} and {request.new_resume_id}")
        
        comparison = resume_service.compare_resumes(
            db=db,
            old_resume_id=request.old_resume_id,
            new_resume_id=request.new_resume_id,
            user_id=current_user.id
        )
        
        if not comparison:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both resumes not found or you don't have access to them"
            )
        
        logger.info(f"Successfully compared resumes")
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare resumes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare resumes"
        )


# ============================================================================
# DOWNLOAD RESUME AS PDF
# ============================================================================

@router.get("/{resume_id}/download", response_class=StreamingResponse)
async def download_resume_pdf(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a resume as a PDF file.
    
    Generates a PDF on-demand from stored resume data.
    No PDFs are stored in the database.
    
    Path Parameters:
    - resume_id: Resume ID
    
    Returns:
    - PDF file as downloadable attachment
    
    Response Headers:
    - Content-Type: application/pdf
    - Content-Disposition: attachment; filename="Resume-{name}.pdf"
    
    Raises:
    - 404: Resume not found or unauthorized
    - 500: PDF generation failed
    """
    try:
        logger.info(f"User {current_user.id} requesting PDF download for resume {resume_id}")
        
        # Fetch resume from database
        resume = resume_service.get_resume(
            db=db,
            resume_id=resume_id,
            user_id=current_user.id
        )
        
        if not resume:
            logger.warning(f"Resume {resume_id} not found for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found or you don't have access to it"
            )
        
        # Generate PDF from resume data
        pdf_bytes = pdf_service.generate_pdf(resume.resume_data)
        
        if not pdf_bytes:
            logger.error(f"Failed to generate PDF for resume {resume_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate PDF. Please try again later."
            )
        
        # Generate filename
        personal_info = resume.resume_data.get("personal_info", {})
        first_name = personal_info.get("first_name", "User")
        last_name = personal_info.get("last_name", "Resume")
        filename = f"Resume-{first_name}-{last_name}-v{resume.version}.pdf"
        
        logger.info(f"Successfully generated PDF for resume {resume_id} ({len(pdf_bytes)} bytes)")
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\"",
                "Content-Length": str(len(pdf_bytes))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download resume PDF {resume_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download resume. Please try again later."
        )


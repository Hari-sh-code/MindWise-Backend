"""
Interview Feedback Router.
Handles interview feedback submission, retrieval, and AI-powered improvement plan generation.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from database import get_db
from models.job import JobApplication
from models.user import User
from core.auth import get_current_user
from schemas.interview import (
    InterviewFeedbackCreate,
    InterviewFeedbackResponse,
    InterviewFeedbackSummary,
    ImprovementPlanResponse,
)
from services.interview_service import interview_service
from services.resume_extractor import resume_extractor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Interview Feedback"])


@router.post("/{job_id}/interview-feedback", response_model=InterviewFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_interview_feedback(
    job_id: int,
    feedback_data: InterviewFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit interview feedback for a rejected job application.
    
    - Validates the job belongs to current user
    - Verifies job status is "rejected"
    - Creates interview feedback record
    - Creates individual interview round records
    - Returns created feedback with all rounds
    
    Args:
        job_id: ID of the job application
        feedback_data: Interview feedback data including rounds
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        InterviewFeedbackResponse: Created feedback record with rounds
        
    Raises:
        HTTPException: If job not found, doesn't belong to user, or status is not rejected
    """
    try:
        # Fetch the job application
        job = db.query(JobApplication).filter(JobApplication.id == job_id).first()
        
        if not job:
            logger.warning(f"Job not found: {job_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job application not found"
            )
        
        # Verify user owns this job
        if job.user_id != current_user.id:
            logger.warning(
                f"Unauthorized access attempt: user {current_user.id} accessing job {job_id} owned by {job.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this job application"
            )
        
        # Verify job status is rejected
        if job.status != "rejected":
            logger.warning(
                f"Invalid job status for feedback: expected 'rejected', got '{job.status}'"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Interview feedback can only be submitted for rejected applications. Current status: {job.status}"
            )
        
        # Submit interview feedback
        result = interview_service.submit_interview_feedback(db, job_id, feedback_data)
        
        logger.info(f"Interview feedback submitted for job {job_id} by user {current_user.id}")
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error during feedback submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error submitting interview feedback for job {job_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit interview feedback"
        )


@router.get("/{job_id}/interview-feedback", response_model=InterviewFeedbackResponse)
async def get_interview_feedback(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get interview feedback and rounds for a job application.
    Includes stored improvement plan if available.
    
    Args:
        job_id: ID of the job application
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        InterviewFeedbackResponse: Interview feedback with all rounds and improvement plan
        
    Raises:
        HTTPException: If job not found, doesn't belong to user, or no feedback exists
    """
    try:
        # Fetch the job application
        job = db.query(JobApplication).filter(JobApplication.id == job_id).first()
        
        if not job:
            logger.warning(f"Job not found: {job_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job application not found"
            )
        
        # Verify user owns this job
        if job.user_id != current_user.id:
            logger.warning(
                f"Unauthorized access attempt: user {current_user.id} accessing job {job_id} owned by {job.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this job application"
            )
        
        # Get interview feedback
        feedback = interview_service.get_interview_feedback(db, job_id)
        
        logger.info(f"Retrieved interview feedback for job {job_id} by user {current_user.id}")
        return feedback
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Interview feedback not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error retrieving interview feedback for job {job_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve interview feedback"
        )


@router.post("/{job_id}/improvement-plan", response_model=ImprovementPlanResponse)
async def generate_improvement_plan(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate an AI-powered improvement plan based on interview feedback.
    
    Flow:
    1. Fetches job application details
    2. Fetches interview feedback and rounds
    3. Extracts resume text from Google Drive
    4. Calls AI agent to generate improvement plan
    5. Returns structured improvement plan
    
    Args:
        job_id: ID of the job application
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        ImprovementPlanResponse: AI-generated improvement plan with weak areas, 
                                recommended topics, practice problems, and strategy
        
    Raises:
        HTTPException: If job not found, doesn't belong to user, feedback missing, 
                      or AI generation fails
    """
    try:
        # Fetch the job application
        job = db.query(JobApplication).filter(JobApplication.id == job_id).first()
        
        if not job:
            logger.warning(f"Job not found: {job_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job application not found"
            )
        
        # Verify user owns this job
        if job.user_id != current_user.id:
            logger.warning(
                f"Unauthorized access attempt: user {current_user.id} accessing job {job_id} owned by {job.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this job application"
            )
        
        # Extract resume text
        logger.info(f"Extracting resume for improvement plan generation: {job.resume_drive_link}")
        resume_text = resume_extractor.extract(job.resume_drive_link)
        
        # Generate improvement plan using AI service
        logger.info(f"Generating improvement plan for job {job_id}")
        improvement_plan = interview_service.generate_improvement_plan(db, job, resume_text)
        
        logger.info(f"Improvement plan generated for job {job_id} by user {current_user.id}")
        return improvement_plan
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error during improvement plan generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected error generating improvement plan for job {job_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate improvement plan. Please ensure interview feedback has been submitted."
        )

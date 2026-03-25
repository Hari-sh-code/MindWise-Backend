"""
AI Analysis Router.
Handles AI-powered job-resume matching analysis.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from schemas.job import AIAnalysisResult
from services.resume_extractor import resume_extractor
from services.ai_agent import ai_agent
from models.job import JobApplication
from models.user import User
from core.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


class AnalyzeJobRequest(BaseModel):
    """Request schema for job analysis."""
    company_name: str
    job_title: str
    job_description: str
    resume_drive_link: str


class AnalyzeJobResponse(BaseModel):
    """Response schema for job analysis."""
    job_id: int
    company_name: str
    job_title: str
    analysis: AIAnalysisResult


@router.post("/analyze-job", response_model=AnalyzeJobResponse)
async def analyze_job(
    request: AnalyzeJobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    try:

        logger.info(f"Using provided job description: {len(request.job_description)} characters")
        
        logger.info(f"Extracting resume from: {request.resume_drive_link}")
        resume_text = resume_extractor.extract(request.resume_drive_link)
        logger.info(f"Extracted resume: {len(resume_text)} characters")
        
        logger.info("Performing AI analysis...")
        analysis = ai_agent.analyze_job_resume_match(
            job_description=request.job_description,
            resume_text=resume_text
        )
        logger.info(f"AI analysis completed with score: {analysis.match_score}")
        
        job_application = JobApplication(
            user_id=current_user.id,  
            company_name=request.company_name,
            job_title=request.job_title,
            job_description=request.job_description,
            resume_drive_link=request.resume_drive_link,
            ai_analysis=analysis.model_dump(),
            status="analyzed"
        )
        
        db.add(job_application)
        db.commit()
        db.refresh(job_application)
        
        logger.info(f"Saved job application with ID: {job_application.id}")
        
        return AnalyzeJobResponse(
            job_id=job_application.id,
            company_name=job_application.company_name,
            job_title=job_application.job_title,
            analysis=analysis
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

"""
Pydantic schemas for Interview Feedback endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class InterviewRoundBase(BaseModel):
    """Base schema for interview round."""
    round_number: int = Field(..., ge=1, description="Round number (starting from 1)")
    type: str = Field(..., description="Type of round (e.g., 'technical', 'hr', 'case_study')")
    topics: Optional[str] = Field(default=None, description="Topics covered in this round (comma-separated)")
    difficulty: str = Field(..., description="Difficulty level (easy, medium, hard)")
    result: str = Field(..., description="Round result (passed, failed)")
    notes: Optional[str] = Field(default=None, description="Additional notes about the round")


class InterviewRoundCreate(InterviewRoundBase):
    """Schema for creating an interview round."""
    pass


class InterviewRoundResponse(InterviewRoundBase):
    """Schema for interview round response."""
    id: int
    interview_feedback_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class InterviewFeedbackBase(BaseModel):
    """Base schema for interview feedback."""
    total_rounds: int = Field(..., ge=1, description="Total number of interview rounds")
    rounds_passed: int = Field(..., ge=0, description="Number of rounds passed")


class InterviewFeedbackCreate(InterviewFeedbackBase):
    """Schema for creating interview feedback."""
    rounds: List[InterviewRoundCreate] = Field(..., description="List of interview rounds")


class InterviewFeedbackResponse(InterviewFeedbackBase):
    id: int
    job_application_id: int
    interview_rounds: List[InterviewRoundResponse]
    improvement_plan: Optional["ImprovementPlanResponse"] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class InterviewFeedbackSummary(BaseModel):
    """Schema for interview feedback summary."""
    total_rounds: int
    rounds_passed: int
    rounds_failed: int
    pass_rate: float
    rounds: List[InterviewRoundResponse]


class ImprovementArea(BaseModel):
    """Schema for identified weak area."""
    area: str
    reason: str


class PracticeProblem(BaseModel):
    """Schema for practice problem recommendation."""
    title: str
    description: str
    difficulty: str


class ImprovementPlanResponse(BaseModel):
    """Schema for AI-generated improvement plan."""
    failure_stage: str = Field(..., description="At which stage the application failed")
    weak_areas: List[ImprovementArea] = Field(..., description="Identified weak areas")
    recommended_topics: List[str] = Field(..., description="Topics to focus on")
    practice_problems: List[PracticeProblem] = Field(..., description="Recommended practice problems")
    improvement_strategy: List[str] = Field(..., description="Step-by-step improvement strategy")


# Rebuild models to resolve forward references
InterviewFeedbackResponse.model_rebuild()

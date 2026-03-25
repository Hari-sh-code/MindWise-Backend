"""
Interview Feedback and Rounds database models.
Stores interview feedback with individual round details for rejected job applications.
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class InterviewFeedback(Base):

    __tablename__ = "interview_feedback"

    id = Column(Integer, primary_key=True, index=True)
    job_application_id = Column(Integer, ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_rounds = Column(Integer, nullable=False)
    rounds_passed = Column(Integer, nullable=False)
    improvement_plan = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    job_application = relationship("JobApplication", foreign_keys=[job_application_id])
    interview_rounds = relationship("InterviewRound", back_populates="interview_feedback", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<InterviewFeedback(id={self.id}, job_id={self.job_application_id}, passed={self.rounds_passed}/{self.total_rounds})>"


class InterviewRound(Base):
    """
    Stores details for individual interview rounds.
    """
    __tablename__ = "interview_rounds"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_feedback_id = Column(Integer, ForeignKey("interview_feedback.id", ondelete="CASCADE"), nullable=False)
    round_number = Column(Integer, nullable=False)
    type = Column(String(50), nullable=False)  # "technical", "hr", "case_study", etc.
    topics = Column(Text, nullable=True)  # List of topics covered
    difficulty = Column(String(20), nullable=False)  # "easy", "medium", "hard"
    result = Column(String(20), nullable=False)  # "passed", "failed"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    interview_feedback = relationship("InterviewFeedback", back_populates="interview_rounds")
    
    def __repr__(self):
        return f"<InterviewRound(id={self.id}, round={self.round_number}, result={self.result})>"

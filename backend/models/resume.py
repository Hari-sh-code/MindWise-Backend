"""
Resume database model.
Stores generated and optimized resumes with ATS scoring and versioning.
"""
from sqlalchemy import Column, Integer, String, Text, JSON, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Resume(Base):
    """
    Resumes table:
    - id: Primary key
    - user_id: Foreign key to users
    - job_description: Original job description
    - jd_keywords: JSONB array of extracted keywords
    - resume_data: JSONB object containing structured resume content
    - ats_score: Numeric ATS matching score (0-100)
    - keyword_coverage: Numeric keyword coverage percentage (0-100)
    - is_ai_enhanced: Boolean indicating if AI enhancement was applied
    - version: Integer version number (auto-incrementing per user)
    - created_at: Timestamp
    - updated_at: Timestamp
    - job_application_id: Optional foreign key to job_applications (for linking)
    """

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    job_description = Column(Text, nullable=False)
    jd_keywords = Column(JSON, nullable=True)  # JSONB: array of keywords
    
    resume_data = Column(JSON, nullable=False)  # JSONB: structured resume content
    
    ats_score = Column(Numeric(5, 2), nullable=True)  # 0-100 with decimals
    keyword_coverage = Column(Numeric(5, 2), nullable=True)  # 0-100 percentage
    
    is_ai_enhanced = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    job_application_id = Column(Integer, ForeignKey("job_applications.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    user = relationship("User", backref="resumes")
    job_application = relationship("JobApplication", backref="resumes")

    def __repr__(self):
        return f"<Resume(id={self.id}, user_id={self.user_id}, version={self.version}, ats_score={self.ats_score})>"

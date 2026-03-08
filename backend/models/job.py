"""
JobApplication database model.
Stores job applications with extracted job descriptions and AI analysis.
"""
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class JobApplication(Base):

    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    job_description = Column(Text, nullable=False)
    resume_drive_link = Column(Text, nullable=False)
    user_notes = Column(Text, nullable=True)  # User notes about company (NOT sent to AI)
    ai_analysis = Column(JSON, nullable=True)  # Stores AI analysis results
    status = Column(String(50), default="pending")  # pending, analyzed, applied, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="job_applications")
    
    def __repr__(self):
        return f"<JobApplication(id={self.id}, company='{self.company_name}', title='{self.job_title}')>"

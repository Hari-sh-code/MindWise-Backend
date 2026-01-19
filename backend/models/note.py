"""
Note database model.
Stores user reference notes for job applications.
Notes are for tracking purposes only and are NOT sent to AI.
"""
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Note(Base):
    """
    Represents a reference note for a job application.
    These notes are stored in DB only and NOT used in AI analysis.
    """
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_applications.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with job application
    job = relationship("JobApplication", back_populates="reference_notes")
    
    def __repr__(self):
        return f"<Note(id={self.id}, job_id={self.job_id})>"

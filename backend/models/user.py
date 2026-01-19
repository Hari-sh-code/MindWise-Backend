"""
User database model.
Stores user authentication and profile information.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """
    Represents a user account.
    Contains authentication credentials and profile information.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_fresher = Column(Boolean, default=True)  # True for fresher, False for experienced
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with job applications
    job_applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', name='{self.first_name} {self.last_name}')>"

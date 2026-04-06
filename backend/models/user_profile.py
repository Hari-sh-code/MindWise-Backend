"""
User Profile models.
Strictly matches the PostgreSQL database schema — do NOT add columns not in the DB.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from database import Base


class UserProfile(Base):
    """user_profiles table: id, user_id, phone, summary, created_at"""

    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    phone = Column(String(20), nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref=backref("profile", uselist=False))

    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, phone='{self.phone}')>"


class UserSocialLink(Base):
    """user_social_links table: id, user_id, platform, url, created_at"""

    __tablename__ = "user_social_links"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    url = Column(String(500), nullable=False)
    username = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="social_links")

    def __repr__(self):
        return f"<UserSocialLink(user_id={self.user_id}, platform='{self.platform}')>"


class UserSkill(Base):
    """user_skills table: id, user_id, skill_name, skill_type, created_at"""

    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    skill_type = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="skills")

    def __repr__(self):
        return f"<UserSkill(user_id={self.user_id}, skill='{self.skill_name}', type='{self.skill_type}')>"


class UserProject(Base):
    """user_projects table: id, user_id, title, tech_stack, description, github_url, created_at"""

    __tablename__ = "user_projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    tech_stack = Column(Text, nullable=True)
    github_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="projects")

    def __repr__(self):
        return f"<UserProject(user_id={self.user_id}, title='{self.title}')>"


class UserExperience(Base):
    """user_experience table: id, user_id, company_name, role, duration, description, created_at"""

    __tablename__ = "user_experience"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name = Column(String(200), nullable=False)
    role = Column(String(150), nullable=False)
    duration = Column(String(100), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="experience")

    @property
    def is_current(self):
        return self.end_date is None

    def __repr__(self):
        return f"<UserExperience(user_id={self.user_id}, company='{self.company_name}', role='{self.role}')>"


class UserEducation(Base):
    """user_education table: id, user_id, college, degree, year, created_at"""

    __tablename__ = "user_education"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    college = Column(String(200), nullable=False)
    degree = Column(String(150), nullable=False)
    year = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="education")

    def __repr__(self):
        return f"<UserEducation(user_id={self.user_id}, college='{self.college}', degree='{self.degree}')>"


class UserCertification(Base):
    """user_certifications table: id, user_id, title, issuer, issue_date, credential_id, credential_url, created_at"""

    __tablename__ = "user_certifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    issuer = Column(String(200), nullable=False)
    issue_date = Column(Date, nullable=True)
    credential_id = Column(String(200), nullable=True)
    credential_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", backref="certifications")

    def __repr__(self):
        return f"<UserCertification(user_id={self.user_id}, title='{self.title}', issuer='{self.issuer}')>"

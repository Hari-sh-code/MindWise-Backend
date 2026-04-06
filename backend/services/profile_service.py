"""
Profile Management Service Layer.
Handles business logic for user profile operations.
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from models.user import User
from models.user_profile import (
    UserProfile, UserSkill, UserSocialLink, UserProject,
    UserExperience, UserEducation, UserCertification
)
from schemas.profile import (
    ProfileBasicCreate, ProfileBasicResponse,
    SkillCreate, SkillResponse, SkillUpdate,
    ProjectCreate, ProjectResponse, ProjectUpdate,
    ExperienceCreate, ExperienceResponse, ExperienceUpdate,
    EducationCreate, EducationResponse, EducationUpdate,
    CertificationCreate, CertificationResponse, CertificationUpdate,
    SocialLinkCreate, SocialLinkResponse, SocialLinkUpdate,
    CompleteProfileResponse, ProfileSummaryResponse
)

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for managing user profiles."""
    
    # ========================================================================
    # PROFILE BASIC INFO
    # ========================================================================
    
    def get_or_create_profile(self, user_id: int, db: Session) -> UserProfile:
        """Get existing profile or create a new one."""
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.add(profile)
            db.commit()
            db.refresh(profile)
            logger.info(f"Created new profile for user {user_id}")
        
        return profile
    
    def get_profile(self, user_id: int, db: Session) -> Optional[ProfileBasicResponse]:
        """Get user's basic profile."""
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not profile:
            return None
        
        return ProfileBasicResponse.from_orm(profile)
    
    def update_profile(
        self,
        user_id: int,
        profile_data: ProfileBasicCreate,
        db: Session
    ) -> ProfileBasicResponse:
        """Update user's basic profile."""
        profile = self.get_or_create_profile(user_id, db)
        
        if profile_data.phone is not None:
            profile.phone = profile_data.phone
        if profile_data.summary is not None:
            profile.summary = profile_data.summary
        
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Updated profile for user {user_id}")
        
        return ProfileBasicResponse.from_orm(profile)
    
    # ========================================================================
    # SKILLS
    # ========================================================================
    
    def create_skill(
        self,
        user_id: int,
        skill_data: SkillCreate,
        db: Session
    ) -> SkillResponse:
        """Create a new skill."""
        # Check for duplicate skill
        existing = db.query(UserSkill).filter(
            UserSkill.user_id == user_id,
            UserSkill.skill_name == skill_data.skill_name.strip()
        ).first()
        
        if existing:
            logger.warning(f"Duplicate skill '{skill_data.skill_name}' for user {user_id}")
            raise ValueError(f"Skill '{skill_data.skill_name}' already exists")
        
        skill = UserSkill(
            user_id=user_id,
            skill_name=skill_data.skill_name.strip(),
            skill_type=skill_data.skill_type
        )
        
        db.add(skill)
        db.commit()
        db.refresh(skill)
        
        logger.info(f"Created skill '{skill_data.skill_name}' for user {user_id}")
        
        return SkillResponse.from_orm(skill)
    
    def get_skills(self, user_id: int, db: Session) -> List[SkillResponse]:
        """Get all skills for a user."""
        skills = db.query(UserSkill).filter(
            UserSkill.user_id == user_id
        ).all()
        
        return [SkillResponse.from_orm(skill) for skill in skills]
    
    def get_skill(self, skill_id: int, user_id: int, db: Session) -> Optional[SkillResponse]:
        """Get a specific skill."""
        skill = db.query(UserSkill).filter(
            UserSkill.id == skill_id,
            UserSkill.user_id == user_id
        ).first()
        
        if not skill:
            return None
        
        return SkillResponse.from_orm(skill)
    
    def update_skill(
        self,
        skill_id: int,
        user_id: int,
        skill_data: SkillUpdate,
        db: Session
    ) -> SkillResponse:
        """Update a skill."""
        skill = db.query(UserSkill).filter(
            UserSkill.id == skill_id,
            UserSkill.user_id == user_id
        ).first()
        
        if not skill:
            raise ValueError("Skill not found")
        
        if skill_data.skill_name is not None:
            skill.skill_name = skill_data.skill_name.strip()
        if skill_data.skill_type is not None:
            skill.skill_type = skill_data.skill_type
        
        db.commit()
        db.refresh(skill)
        
        logger.info(f"Updated skill {skill_id} for user {user_id}")
        
        return SkillResponse.from_orm(skill)
    
    def delete_skill(self, skill_id: int, user_id: int, db: Session) -> bool:
        """Delete a skill."""
        skill = db.query(UserSkill).filter(
            UserSkill.id == skill_id,
            UserSkill.user_id == user_id
        ).first()
        
        if not skill:
            return False
        
        db.delete(skill)
        db.commit()
        
        logger.info(f"Deleted skill {skill_id} for user {user_id}")
        
        return True
    
    # ========================================================================
    # PROJECTS
    # ========================================================================
    
    def create_project(
        self,
        user_id: int,
        project_data: ProjectCreate,
        db: Session
    ) -> ProjectResponse:
        """Create a new project."""
        project = UserProject(
            user_id=user_id,
            title=project_data.title.strip(),
            description=project_data.description,
            tech_stack=project_data.tech_stack,
            github_url=project_data.github_url
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        logger.info(f"Created project '{project_data.title}' for user {user_id}")
        
        return ProjectResponse.from_orm(project)
    
    def get_projects(self, user_id: int, db: Session) -> List[ProjectResponse]:
        """Get all projects for a user."""
        projects = db.query(UserProject).filter(
            UserProject.user_id == user_id
        ).order_by(UserProject.created_at.desc()).all()
        
        return [ProjectResponse.from_orm(project) for project in projects]
    
    def get_project(self, project_id: int, user_id: int, db: Session) -> Optional[ProjectResponse]:
        """Get a specific project."""
        project = db.query(UserProject).filter(
            UserProject.id == project_id,
            UserProject.user_id == user_id
        ).first()
        
        if not project:
            return None
        
        return ProjectResponse.from_orm(project)
    
    def update_project(
        self,
        project_id: int,
        user_id: int,
        project_data: ProjectUpdate,
        db: Session
    ) -> ProjectResponse:
        """Update a project."""
        project = db.query(UserProject).filter(
            UserProject.id == project_id,
            UserProject.user_id == user_id
        ).first()
        
        if not project:
            raise ValueError("Project not found")
        
        if project_data.title is not None:
            project.title = project_data.title.strip()
        if project_data.description is not None:
            project.description = project_data.description
        if project_data.tech_stack is not None:
            project.tech_stack = project_data.tech_stack
        if project_data.github_url is not None:
            project.github_url = project_data.github_url
        
        db.commit()
        db.refresh(project)
        
        logger.info(f"Updated project {project_id} for user {user_id}")
        
        return ProjectResponse.from_orm(project)
    
    def delete_project(self, project_id: int, user_id: int, db: Session) -> bool:
        """Delete a project."""
        project = db.query(UserProject).filter(
            UserProject.id == project_id,
            UserProject.user_id == user_id
        ).first()
        
        if not project:
            return False
        
        db.delete(project)
        db.commit()
        
        logger.info(f"Deleted project {project_id} for user {user_id}")
        
        return True
    
    # ========================================================================
    # EXPERIENCE
    # ========================================================================
    
    def create_experience(
        self,
        user_id: int,
        experience_data: ExperienceCreate,
        db: Session
    ) -> ExperienceResponse:
        """Create a new experience entry."""
        if experience_data.start_date and experience_data.end_date:
            if experience_data.start_date > experience_data.end_date:
                raise ValueError("start_date cannot be after end_date")
                
        experience = UserExperience(
            user_id=user_id,
            company_name=experience_data.company_name.strip(),
            role=experience_data.role.strip(),
            duration=experience_data.duration,
            start_date=experience_data.start_date,
            end_date=experience_data.end_date,
            description=experience_data.description
        )
        
        db.add(experience)
        db.commit()
        db.refresh(experience)
        
        logger.info(f"Created experience at '{experience_data.company_name}' for user {user_id}")
        
        return ExperienceResponse.from_orm(experience)
    
    def get_experience(self, user_id: int, db: Session) -> List[ExperienceResponse]:
        """Get all experience for a user."""
        experiences = db.query(UserExperience).filter(
            UserExperience.user_id == user_id
        ).order_by(UserExperience.start_date.desc().nullslast(), UserExperience.created_at.desc()).all()
        
        return [ExperienceResponse.from_orm(exp) for exp in experiences]
    
    def get_experience_entry(
        self,
        experience_id: int,
        user_id: int,
        db: Session
    ) -> Optional[ExperienceResponse]:
        """Get a specific experience entry."""
        experience = db.query(UserExperience).filter(
            UserExperience.id == experience_id,
            UserExperience.user_id == user_id
        ).first()
        
        if not experience:
            return None
        
        return ExperienceResponse.from_orm(experience)
    
    def update_experience(
        self,
        experience_id: int,
        user_id: int,
        experience_data: ExperienceUpdate,
        db: Session
    ) -> ExperienceResponse:
        """Update an experience entry."""
        experience = db.query(UserExperience).filter(
            UserExperience.id == experience_id,
            UserExperience.user_id == user_id
        ).first()
        
        if not experience:
            raise ValueError("Experience not found")
        
        update_data = experience_data.model_dump(exclude_unset=True) if hasattr(experience_data, 'model_dump') else experience_data.dict(exclude_unset=True)
        
        chk_start = update_data.get('start_date', experience.start_date)
        chk_end = update_data.get('end_date', experience.end_date)
        if chk_start and chk_end and chk_start > chk_end:
            raise ValueError("start_date cannot be after end_date")
            
        if experience_data.company_name is not None:
            experience.company_name = experience_data.company_name.strip()
        if experience_data.role is not None:
            experience.role = experience_data.role.strip()
        if experience_data.duration is not None:
            experience.duration = experience_data.duration
        if 'start_date' in update_data:
            experience.start_date = update_data['start_date']
        if 'end_date' in update_data:
            experience.end_date = update_data['end_date']
        if experience_data.description is not None:
            experience.description = experience_data.description
        
        db.commit()
        db.refresh(experience)
        
        logger.info(f"Updated experience {experience_id} for user {user_id}")
        
        return ExperienceResponse.from_orm(experience)
    
    def delete_experience(self, experience_id: int, user_id: int, db: Session) -> bool:
        """Delete an experience entry."""
        experience = db.query(UserExperience).filter(
            UserExperience.id == experience_id,
            UserExperience.user_id == user_id
        ).first()
        
        if not experience:
            return False
        
        db.delete(experience)
        db.commit()
        
        logger.info(f"Deleted experience {experience_id} for user {user_id}")
        
        return True
    
    # ========================================================================
    # EDUCATION
    # ========================================================================
    
    def create_education(
        self,
        user_id: int,
        education_data: EducationCreate,
        db: Session
    ) -> EducationResponse:
        """Create a new education entry."""
        education = UserEducation(
            user_id=user_id,
            college=education_data.college.strip(),
            degree=education_data.degree.strip(),
            year=education_data.year
        )
        
        db.add(education)
        db.commit()
        db.refresh(education)
        
        logger.info(f"Created education '{education_data.degree}' from '{education_data.college}' for user {user_id}")
        
        return EducationResponse.from_orm(education)
    
    def get_education(self, user_id: int, db: Session) -> List[EducationResponse]:
        """Get all education for a user."""
        educations = db.query(UserEducation).filter(
            UserEducation.user_id == user_id
        ).order_by(UserEducation.year.desc()).all()
        
        return [EducationResponse.from_orm(edu) for edu in educations]
    
    def get_education_entry(
        self,
        education_id: int,
        user_id: int,
        db: Session
    ) -> Optional[EducationResponse]:
        """Get a specific education entry."""
        education = db.query(UserEducation).filter(
            UserEducation.id == education_id,
            UserEducation.user_id == user_id
        ).first()
        
        if not education:
            return None
        
        return EducationResponse.from_orm(education)
    
    def update_education(
        self,
        education_id: int,
        user_id: int,
        education_data: EducationUpdate,
        db: Session
    ) -> EducationResponse:
        """Update an education entry."""
        education = db.query(UserEducation).filter(
            UserEducation.id == education_id,
            UserEducation.user_id == user_id
        ).first()
        
        if not education:
            raise ValueError("Education not found")
        
        if education_data.college is not None:
            education.college = education_data.college.strip()
        if education_data.degree is not None:
            education.degree = education_data.degree.strip()
        if education_data.year is not None:
            education.year = education_data.year
        
        db.commit()
        db.refresh(education)
        
        logger.info(f"Updated education {education_id} for user {user_id}")
        
        return EducationResponse.from_orm(education)
    
    def delete_education(self, education_id: int, user_id: int, db: Session) -> bool:
        """Delete an education entry."""
        education = db.query(UserEducation).filter(
            UserEducation.id == education_id,
            UserEducation.user_id == user_id
        ).first()
        
        if not education:
            return False
        
        db.delete(education)
        db.commit()
        
        logger.info(f"Deleted education {education_id} for user {user_id}")
        
        return True
    
    # ========================================================================
    # CERTIFICATIONS
    # ========================================================================
    
    def create_certification(
        self,
        user_id: int,
        cert_data: CertificationCreate,
        db: Session
    ) -> CertificationResponse:
        """Create a new certification."""
        certification = UserCertification(
            user_id=user_id,
            title=cert_data.title.strip(),
            issuer=cert_data.issuer.strip(),
            issue_date=cert_data.issue_date,
            credential_id=cert_data.credential_id,
            credential_url=cert_data.credential_url
        )
        
        db.add(certification)
        db.commit()
        db.refresh(certification)
        
        logger.info(f"Created certification '{cert_data.title}' from '{cert_data.issuer}' for user {user_id}")
        
        return CertificationResponse.from_orm(certification)
    
    def get_certifications(self, user_id: int, db: Session) -> List[CertificationResponse]:
        """Get all certifications for a user."""
        certifications = db.query(UserCertification).filter(
            UserCertification.user_id == user_id
        ).order_by(UserCertification.issue_date.desc()).all()
        
        return [CertificationResponse.from_orm(cert) for cert in certifications]
    
    def get_certification(
        self,
        certification_id: int,
        user_id: int,
        db: Session
    ) -> Optional[CertificationResponse]:
        """Get a specific certification."""
        certification = db.query(UserCertification).filter(
            UserCertification.id == certification_id,
            UserCertification.user_id == user_id
        ).first()
        
        if not certification:
            return None
        
        return CertificationResponse.from_orm(certification)
    
    def update_certification(
        self,
        certification_id: int,
        user_id: int,
        cert_data: CertificationUpdate,
        db: Session
    ) -> CertificationResponse:
        """Update a certification."""
        certification = db.query(UserCertification).filter(
            UserCertification.id == certification_id,
            UserCertification.user_id == user_id
        ).first()
        
        if not certification:
            raise ValueError("Certification not found")
        
        if cert_data.title is not None:
            certification.title = cert_data.title.strip()
        if cert_data.issuer is not None:
            certification.issuer = cert_data.issuer.strip()
        if cert_data.issue_date is not None:
            certification.issue_date = cert_data.issue_date
        if cert_data.credential_id is not None:
            certification.credential_id = cert_data.credential_id
        if cert_data.credential_url is not None:
            certification.credential_url = cert_data.credential_url
        
        db.commit()
        db.refresh(certification)
        
        logger.info(f"Updated certification {certification_id} for user {user_id}")
        
        return CertificationResponse.from_orm(certification)
    
    def delete_certification(self, certification_id: int, user_id: int, db: Session) -> bool:
        """Delete a certification."""
        certification = db.query(UserCertification).filter(
            UserCertification.id == certification_id,
            UserCertification.user_id == user_id
        ).first()
        
        if not certification:
            return False
        
        db.delete(certification)
        db.commit()
        
        logger.info(f"Deleted certification {certification_id} for user {user_id}")
        
        return True
    
    # ========================================================================
    # SOCIAL LINKS
    # ========================================================================
    
    from urllib.parse import urlparse

    @staticmethod
    def _extract_username(url: str) -> str | None:
        try:
            parsed = urlparse(url)
            parts = [p for p in parsed.path.split("/") if p]

            if not parts:
                return None

            host = parsed.netloc.lower()

            if "linkedin.com" in host and parts[0] == "in":
                return parts[1] if len(parts) > 1 else None

            if "hackerrank.com" in host and parts[0] == "profile":
                return parts[1] if len(parts) > 1 else None

            if "leetcode.com" in host and parts[0] == "u":
                return parts[1] if len(parts) > 1 else None

            if "codechef.com" in host and parts[0] == "users":
                return parts[1] if len(parts) > 1 else None

            return parts[0]
        except:
            return None
    def create_social_link(
        self,
        user_id: int,
        link_data: SocialLinkCreate,
        db: Session
    ) -> SocialLinkResponse:
        """Create a new social link."""
        # Check for duplicate platform
        existing = db.query(UserSocialLink).filter(
            UserSocialLink.user_id == user_id,
            UserSocialLink.platform == link_data.platform.lower()
        ).first()
        
        if existing:
            logger.warning(f"Duplicate social link '{link_data.platform}' for user {user_id}")
            raise ValueError(f"Social link for '{link_data.platform}' already exists")
        
        username = link_data.username or self._extract_username(link_data.url)
        
        social_link = UserSocialLink(
            user_id=user_id,
            platform=link_data.platform.lower(),
            url=link_data.url,
            username=username
        )
        
        db.add(social_link)
        db.commit()
        db.refresh(social_link)
        
        logger.info(f"Created social link '{link_data.platform}' for user {user_id}")
        
        return SocialLinkResponse.from_orm(social_link)
    
    def get_social_links(self, user_id: int, db: Session) -> List[SocialLinkResponse]:
        """Get all social links for a user."""
        links = db.query(UserSocialLink).filter(
            UserSocialLink.user_id == user_id
        ).all()
        
        return [SocialLinkResponse.from_orm(link) for link in links]
    
    def get_social_link(
        self,
        link_id: int,
        user_id: int,
        db: Session
    ) -> Optional[SocialLinkResponse]:
        """Get a specific social link."""
        link = db.query(UserSocialLink).filter(
            UserSocialLink.id == link_id,
            UserSocialLink.user_id == user_id
        ).first()
        
        if not link:
            return None
        
        return SocialLinkResponse.from_orm(link)
    
    def update_social_link(
        self,
        link_id: int,
        user_id: int,
        link_data: SocialLinkUpdate,
        db: Session
    ) -> SocialLinkResponse:
        """Update a social link."""
        link = db.query(UserSocialLink).filter(
            UserSocialLink.id == link_id,
            UserSocialLink.user_id == user_id
        ).first()
        
        if not link:
            raise ValueError("Social link not found")
        
        if link_data.platform is not None:
            link.platform = link_data.platform.lower()
        if link_data.url is not None:
            link.url = link_data.url
            if not link_data.username:
                link.username = self._extract_username(link_data.url)
        if link_data.username is not None:
            link.username = link_data.username
        
        db.commit()
        db.refresh(link)
        
        logger.info(f"Updated social link {link_id} for user {user_id}")
        
        return SocialLinkResponse.from_orm(link)
    
    def delete_social_link(self, link_id: int, user_id: int, db: Session) -> bool:
        """Delete a social link."""
        link = db.query(UserSocialLink).filter(
            UserSocialLink.id == link_id,
            UserSocialLink.user_id == user_id
        ).first()
        
        if not link:
            return False
        
        db.delete(link)
        db.commit()
        
        logger.info(f"Deleted social link {link_id} for user {user_id}")
        
        return True
    
    # ========================================================================
    # COMPLETE PROFILE
    # ========================================================================
    
    def get_complete_profile(self, user_id: int, db: Session) -> CompleteProfileResponse:
        """Get complete user profile with all data."""
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        basic_response = None
        if profile:
            basic_response = ProfileBasicResponse.from_orm(profile)

        skills = self.get_skills(user_id, db)
        projects = self.get_projects(user_id, db)
        experiences = self.get_experience(user_id, db)
        educations = self.get_education(user_id, db)
        certifications = self.get_certifications(user_id, db)
        social_links = self.get_social_links(user_id, db)

        return CompleteProfileResponse(
            basic=basic_response,
            skills=skills,
            projects=projects,
            experience=experiences,
            education=educations,
            certifications=certifications,
            social_links=social_links
        )
    
    def get_profile_summary(self, user_id: int, db: Session) -> ProfileSummaryResponse:
        """Get profile completion summary."""
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        skills_count = db.query(UserSkill).filter(UserSkill.user_id == user_id).count()
        projects_count = db.query(UserProject).filter(UserProject.user_id == user_id).count()
        experience_count = db.query(UserExperience).filter(UserExperience.user_id == user_id).count()
        education_count = db.query(UserEducation).filter(UserEducation.user_id == user_id).count()
        certifications_count = db.query(UserCertification).filter(UserCertification.user_id == user_id).count()
        social_links_count = db.query(UserSocialLink).filter(UserSocialLink.user_id == user_id).count()
        
        # Calculate completion percentage
        total_fields = 7  # profile, skills, projects, experience, education, certifications, social_links
        completed_fields = 0
        
        if profile:
            if profile.phone or profile.summary:
                completed_fields += 1
        
        if skills_count > 0:
            completed_fields += 1
        if projects_count > 0:
            completed_fields += 1
        if experience_count > 0:
            completed_fields += 1
        if education_count > 0:
            completed_fields += 1
        if certifications_count > 0:
            completed_fields += 1
        if social_links_count > 0:
            completed_fields += 1
        
        completion_percentage = (completed_fields / total_fields) * 100
        
        return ProfileSummaryResponse(
            user_id=user_id,
            profile_complete=profile is not None,
            skills_count=skills_count,
            projects_count=projects_count,
            experience_count=experience_count,
            education_count=education_count,
            certifications_count=certifications_count,
            social_links_count=social_links_count,
            completion_percentage=completion_percentage
        )


# Singleton instance
profile_service = ProfileService()

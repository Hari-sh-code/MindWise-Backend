"""
Simplified AI Resume Generation Service.
Generates AI-optimized resumes using Gemini and scores them with existing ai_analysis.
Minimal dependencies, no keyword extraction, no manual NLP processing.
"""
import json
import logging
import re
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from models.resume import Resume
from models.user import User
from models.user_profile import (
    UserProfile, UserSkill, UserProject, UserExperience, UserEducation, UserCertification
)
from schemas.resume import ResumeResponse
from services.ai_agent import ai_agent

logger = logging.getLogger(__name__)


class ResumeService:
    """Simplified AI-driven resume generation service."""
    
    # ========================================================================
    # MAIN FLOW: Resume Generation
    # ========================================================================
    
    def generate_resume(
        self,
        db: Session,
        user_id: int,
        job_description: str,
        job_application_id: Optional[int] = None
    ) -> ResumeResponse:
        """
        Main flow to generate an AI-optimized resume.
        """
        try:
            logger.info(f"Starting AI resume generation for user {user_id}")
            
            # Step 1: Fetch profile data
            profile_data = self.fetch_profile_data(db, user_id)
            
            # Step 2: Build AI prompt
            prompt = self.build_prompt(profile_data, job_description)
            
            # Step 3: Generate resume via AI (or fallback)
            resume_data = self.generate_resume_with_ai(prompt, profile_data)
            
            # Step 4: Calculate ATS score using existing AI agent functionality
            ats_score = self.get_ats_score_from_ai_analysis(job_description, resume_data)
            
            # Step 5: Save to database
            resume_entry = self.create_resume_entry(
                db=db,
                user_id=user_id,
                job_description=job_description,
                resume_data=resume_data,
                ats_score=ats_score,
                job_application_id=job_application_id
            )
            
            # Step 6: Return response
            return self._format_resume_response(resume_entry)
            
        except Exception as e:
            logger.error(f"Failed to generate resume for user {user_id}: {e}")
            raise
    
    # ========================================================================
    # STEP 1: Fetch Profile Data
    # ========================================================================
    
    def fetch_profile_data(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Fetch all user profile data for AI context."""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            profile_data = {
                "personal_info": {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "phone": profile.phone if profile else None,
                    "summary": profile.summary if profile else None,
                },
                "skills": [
                    {
                        "name": s.skill_name,
                        "level": s.skill_type
                    }
                    for s in db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
                ],
                "projects": [
                    {
                        "title": p.title,
                        "description": p.description,
                        "tech_stack": p.tech_stack.split(',') if p.tech_stack else [],
                        "github_url": p.github_url
                    }
                    for p in db.query(UserProject).filter(UserProject.user_id == user_id).all()
                ],
                "experience": [
                    {
                        "company_name": e.company_name,
                        "role": e.role,
                        "start_date": e.start_date.isoformat() if e.start_date else None,
                        "end_date": e.end_date.isoformat() if e.end_date else None,
                        "description": e.description
                    }
                    for e in db.query(UserExperience).filter(UserExperience.user_id == user_id).all()
                ],
                "education": [
                    {
                        "college": e.college,
                        "degree": e.degree,
                        "year": e.year
                    }
                    for e in db.query(UserEducation).filter(UserEducation.user_id == user_id).all()
                ],
                "certifications": [
                    {
                        "title": c.title,
                        "issuer": c.issuer,
                        "issue_date": c.issue_date.isoformat() if c.issue_date else None,
                        "credential_url": c.credential_url
                    }
                    for c in db.query(UserCertification).filter(UserCertification.user_id == user_id).all()
                ]
            }
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Failed to fetch profile data for user {user_id}: {e}")
            raise
    
    # ========================================================================
    # STEP 2: Build AI Prompt
    # ========================================================================
    
    def build_prompt(self, profile_data: Dict[str, Any], job_description: str) -> str:
        """
        Build optimized JD-focused prompt for Gemini AI.
        
        Strategy:
        - Provide full candidate data
        - Strict instructions to filter ONLY relevant content
        - Limit projects to top 3, certificates to top 5 relevant to JD
        - Avoid overwhelming with unnecessary information
        """
        try:
            prompt = f"""You are an expert resume writer specializing in ATS-optimized, JD-focused resumes.
Your task: Generate a CONCISE, highly relevant resume that matches this specific job.

CRITICAL RULES:
- Only include content DIRECTLY relevant to the job description
- Be selective: quality over quantity
- Projects: Select ONLY the top 3 most relevant projects
- Certifications: Select ONLY the top 5 most relevant certifications
- Skills: Select only skills mentioned or implied in the job description
- Experience: Highlight achievements that match job requirements
- Keep professional summary to 2-3 sentences maximum
- IGNORE irrelevant projects, certifications, or skills

CANDIDATE PROFILE:
Name: {profile_data['personal_info']['first_name']} {profile_data['personal_info']['last_name']}
Email: {profile_data['personal_info']['email']}
Phone: {profile_data['personal_info']['phone'] or 'Not provided'}
Professional Summary: {profile_data['personal_info']['summary'] or 'Professional'}

Available Skills: {json.dumps(profile_data['skills'])}
Work Experience: {json.dumps(profile_data['experience'])}
Education: {json.dumps(profile_data['education'])}
Available Projects: {json.dumps(profile_data['projects'])}
Available Certifications: {json.dumps(profile_data['certifications'])}

JOB DESCRIPTION:
{job_description}

SELECTION INSTRUCTIONS:
1. Skills: Extract 5-7 skills most relevant to the JD
2. Projects: Select ONLY top 3 projects that align with job requirements
3. Certifications: Select ONLY up to 5 certifications relevant to the role (or none if not relevant)
4. Experience: Keep 3-5 most relevant roles, adjust descriptions to match JD requirements
5. Summary: Create 2-3 sentence summary highlighting fit for THIS specific job

RESPONSE FORMAT - STRICT JSON (no other text):
{{
  "name": "Full Name",
  "summary": "2-3 sentence professional summary tailored ONLY to this job",
  "skills": ["top_skill_1", "top_skill_2", "top_skill_3", "top_skill_4", "top_skill_5"],
  "experience": [
    {{
      "company_name": "Company",
      "role": "Title",
      "duration": "Start - End",
      "description": "Key achievement matching job requirements"
    }}
  ],
  "projects": [
    {{
      "title": "Project Title",
      "description": "Brief description showing relevance",
      "tech_stack": ["tech1", "tech2"]
    }}
  ],
  "education": [
    {{
      "school": "School Name",
      "degree": "Degree",
      "year": "Year"
    }}
  ],
  "certifications": [
    {{
      "title": "Certification Name",
      "issuer": "Issuer"
    }}
  ]
}}

IMPORTANT:
- Return ONLY valid JSON, nothing else
- NO explanations, NO code blocks, NO extra text
- Include certifications array ONLY if certifications are relevant
- Be ruthless about relevance: omit non-matching content"""
            
            return prompt
            
        except Exception as e:
            logger.error(f"Failed to build prompt: {e}")
            raise
    
    # ========================================================================
    # STEP 3: Generate Resume via AI
    # ========================================================================
    
    def generate_resume_with_ai(self, prompt: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call Gemini API. On failure, returns fallback resume."""
        try:
            response = ai_agent.client.models.generate_content(
                model=ai_agent.model_name,
                contents=prompt
            )
            
            response_text = response.text.strip()
            
            try:
                # Remove code blocks if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:-3].strip()
                elif response_text.startswith("```"):
                    response_text = response_text[3:-3].strip()

                resume_data = json.loads(response_text)
                return self._transform_ai_response(resume_data)
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse Gemini JSON response: {e}")
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        resume_data = json.loads(json_match.group())
                        return self._transform_ai_response(resume_data)
                    except json.JSONDecodeError:
                        pass
                return self.generate_fallback_resume(profile_data)
            
        except Exception as e:
            logger.error(f"AI resume generation failed: {e}. Using fallback.")
            return self.generate_fallback_resume(profile_data)
    
    def _transform_ai_response(self, ai_resume: Dict[str, Any]) -> Dict[str, Any]:
        """Transform API response to internal resume format - includes JD-relevant certifications."""
        return {
            "personal_info": {
                "first_name": ai_resume.get("name", "").split()[0] if ai_resume.get("name") else "User",
                "last_name": " ".join(ai_resume.get("name", "").split()[1:]) if len(ai_resume.get("name", "").split()) > 1 else "",
                "email": None,
                "phone": None,
                "summary": ai_resume.get("summary")
            },
            "summary": ai_resume.get("summary"),
            "skills": [
                {"name": s, "level": None} for s in ai_resume.get("skills", [])
            ],
            "experience": [
                {
                    "company_name": exp.get("company_name"),
                    "role": exp.get("role"),
                    "start_date": None,
                    "end_date": None,
                    "is_current": None,
                    "description": exp.get("description")
                }
                for exp in ai_resume.get("experience", [])
            ],
            "education": [
                {
                    "college": edu.get("school", edu.get("college")),
                    "degree": edu.get("degree"),
                    "year": edu.get("year")
                }
                for edu in ai_resume.get("education", [])
            ],
            "projects": [
                {
                    "title": proj.get("title"),
                    "description": proj.get("description"),
                    "tech_stack": proj.get("tech_stack"),
                    "github_url": None
                }
                for proj in ai_resume.get("projects", [])
            ],
            "certifications": [
                {
                    "title": cert.get("title"),
                    "issuer": cert.get("issuer"),
                    "issue_date": None,
                    "credential_url": None
                }
                for cert in ai_resume.get("certifications", [])
            ],
            "social_links": None
        }
    
    def generate_fallback_resume(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate basic structured resume from profile when AI fails - selective about projects and certifications."""
        try:
            return {
                "personal_info": {
                    "first_name": profile_data["personal_info"]["first_name"],
                    "last_name": profile_data["personal_info"]["last_name"],
                    "email": profile_data["personal_info"]["email"],
                    "phone": profile_data["personal_info"]["phone"],
                    "summary": profile_data["personal_info"]["summary"] or "Professional seeking challenging opportunities"
                },
                "summary": profile_data["personal_info"]["summary"] or "Professional seeking challenging opportunities",
                "skills": [
                    {"name": s["name"], "level": s.get("level")} for s in profile_data.get("skills", [])[:7]  # Limit to 7 skills
                ],
                "experience": [
                    {
                        "company_name": e.get("company_name"),
                        "role": e.get("role"),
                        "start_date": e.get("start_date"),
                        "end_date": e.get("end_date"),
                        "is_current": e.get("end_date") is None,
                        "description": e.get("description")
                    }
                    for e in profile_data.get("experience", [])[:5]  # Limit to 5 experiences
                ],
                "education": [
                    {
                        "college": e.get("college"),
                        "degree": e.get("degree"),
                        "year": e.get("year")
                    }
                    for e in profile_data.get("education", [])
                ],
                "projects": [
                    {
                        "title": p.get("title"),
                        "description": p.get("description"),
                        "tech_stack": p.get("tech_stack"),
                        "github_url": p.get("github_url")
                    }
                    for p in profile_data.get("projects", [])[:3]  # Limit to top 3 projects
                ],
                "certifications": [
                    {
                        "title": c.get("title"),
                        "issuer": c.get("issuer"),
                        "issue_date": c.get("issue_date"),
                        "credential_url": c.get("credential_url")
                    }
                    for c in profile_data.get("certifications", [])[:5]  # Limit to top 5 certifications
                ],
                "social_links": None
            }
        except Exception as e:
            logger.error(f"Failed to generate fallback resume: {e}")
            raise

    # ========================================================================
    # STEP 4: ATS Scoring via AI
    # ========================================================================

    def get_ats_score_from_ai_analysis(self, job_description: str, resume_data: Dict[str, Any]) -> float:
        """
        Use existing ai_analysis logic to extract ATS match score without recreating logic.
        """
        try:
            # We stringify the resume_data to pass it identically to how a PDF text extraction would pass to the agent
            resume_text = json.dumps(resume_data, indent=2)
            analysis_result = ai_agent.analyze_job_resume_match(job_description, resume_text)
            
            score = float(analysis_result.match_score)
            logger.info(f"Retrieved ATS score from ai_agent: {score}")
            return score
            
        except Exception as e:
            logger.error(f"Failed to fetch ATS score via AI Analysis: {e}")
            return 50.0 # Default graceful fallback

    # ========================================================================
    # STEP 5: Create Resume Entry (Database)
    # ========================================================================
    
    def create_resume_entry(
        self,
        db: Session,
        user_id: int,
        job_description: str,
        resume_data: Dict[str, Any],
        ats_score: float,
        job_application_id: Optional[int] = None
    ) -> Resume:
        """Save resume to database with automatic versioning."""
        try:
            latest = db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.version.desc()).first()
            next_version = (latest.version + 1) if latest else 1
            
            new_resume = Resume(
                user_id=user_id,
                job_description=job_description,
                resume_data=resume_data,
                ats_score=ats_score,
                is_ai_enhanced=True,
                version=next_version,
                job_application_id=job_application_id
            )
            
            db.add(new_resume)
            db.commit()
            db.refresh(new_resume)
            
            return new_resume
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create resume entry: {e}")
            raise
    
    # ========================================================================
    # GET/LIST/UPDATE/COMPARE
    # ========================================================================
    
    def get_resume(self, db: Session, resume_id: int, user_id: int) -> Optional[ResumeResponse]:
        """Get single resume."""
        try:
            resume = db.query(Resume).filter(
                Resume.id == resume_id,
                Resume.user_id == user_id
            ).first()
            return self._format_resume_response(resume) if resume else None
        except Exception as e:
            logger.error(f"Failed to get resume {resume_id}: {e}")
            return None
    
    def list_resumes(
        self,
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """List all resumes for user."""
        try:
            query = db.query(Resume).filter(Resume.user_id == user_id)
            total = query.count()
            
            offset = (page - 1) * page_size
            resumes = query.order_by(Resume.created_at.desc()).offset(offset).limit(page_size).all()
            
            return {
                "resumes": [self._format_resume_response(r) for r in resumes],
                "total": total,
                "page": page,
                "page_size": page_size
            }
        except Exception as e:
            logger.error(f"Failed to list resumes: {e}")
            return {"resumes": [], "total": 0, "page": page, "page_size": page_size}
    
    def update_resume_data(
        self,
        db: Session,
        resume_id: int,
        user_id: int,
        resume_data: Dict[str, Any]
    ) -> Optional[ResumeResponse]:
        """Update resume data."""
        try:
            resume = db.query(Resume).filter(
                Resume.id == resume_id,
                Resume.user_id == user_id
            ).first()
            
            if not resume:
                return None
            
            resume.resume_data = resume_data
            db.commit()
            db.refresh(resume)
            
            return self._format_resume_response(resume)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update resume: {e}")
            return None
    
    def compare_resumes(
        self,
        db: Session,
        old_resume_id: int,
        new_resume_id: int,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Compare two resumes - return only ATS score comparison."""
        try:
            old = db.query(Resume).filter(Resume.id == old_resume_id, Resume.user_id == user_id).first()
            new = db.query(Resume).filter(Resume.id == new_resume_id, Resume.user_id == user_id).first()
            
            if not old or not new:
                return None
            
            old_ats = float(old.ats_score) if old.ats_score else 0.0
            new_ats = float(new.ats_score) if new.ats_score else 0.0
            ats_diff = new_ats - old_ats
            ats_improvement = (ats_diff / old_ats * 100) if old_ats > 0 else 0.0
            
            logger.info(f"Compared resumes: {old_score}%.0f -> {new_score}%.0f", old_ats, new_ats)
            
            return {
                "old_resume_id": old_resume_id,
                "new_resume_id": new_resume_id,
                "old_version": old.version,
                "new_version": new.version,
                "old_ats_score": old_ats,
                "new_ats_score": new_ats,
                "ats_improvement": round(ats_diff, 2),
                "ats_improvement_percentage": round(ats_improvement, 2),
                "created_at": new.created_at
            }
            
        except Exception as e:
            logger.error(f"Failed to compare resumes: {e}")
            return None
    
    def _format_resume_response(self, resume: Resume) -> ResumeResponse:
        """Format Resume ORM to Response schema - simplified."""
        return ResumeResponse(
            id=resume.id,
            user_id=resume.user_id,
            job_description=resume.job_description,
            resume_data=resume.resume_data,
            ats_score=float(resume.ats_score) if resume.ats_score else None,
            version=resume.version,
            created_at=resume.created_at,
            updated_at=resume.updated_at,
            job_application_id=resume.job_application_id
        )


# Create singleton instance
resume_service = ResumeService()

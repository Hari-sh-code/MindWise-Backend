"""
Hybrid AI + Database-driven Resume Generation Service.
Database is source of truth. AI enhances text only (summary, descriptions).
"""
import json
import logging
import re
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from models.resume import Resume
from models.user import User
from models.user_profile import (
    UserProfile, UserSkill, UserProject, UserExperience, UserEducation, UserCertification, UserSocialLink
)
from schemas.resume import ResumeResponse
from services.ai_agent import ai_agent

logger = logging.getLogger(__name__)


def extract_keywords_from_jd(job_description: str) -> List[str]:
    """Extract and normalize keywords from job description."""
    try:
        text = job_description.lower()
        STOPWORDS = {"with", "the", "and", "for", "you", "are", "this", "that"}
        words = [
            w for w in re.findall(r'\b[a-z]{3,}\b', text)
            if w not in STOPWORDS
        ]
        return list(set(words))
    except Exception:
        return []


def rebuild_skill_categories(skills):
    """Organize skills by category with strict priority ordering."""
    CATEGORY_ORDER = [
        "Programming Languages",
        "Frameworks & Libraries",
        "Databases",
        "Tools & Technologies",
        "Core Computer Science",
        "Domain Skills",
        "Soft Skills"
    ]
    
    categories = {}
    for skill in skills:
        name = skill.get("name")
        if not name:
            continue
        category = skill.get("category") or "Domain Skills"
        if category not in categories:
            categories[category] = []
        categories[category].append(name)
    
    # Build ordered dict — known categories first, then any custom ones
    ordered = {}
    for cat in CATEGORY_ORDER:
        if cat in categories:
            ordered[cat] = categories[cat]
    # Append any custom user-defined categories not in the standard list
    for cat, skills_list in categories.items():
        if cat not in ordered:
            ordered[cat] = skills_list
    
    return ordered

class ResumeService:

    def get_ats_score_from_ai_analysis(self, job_description, resume_data):
        try:
            resume_text = json.dumps(resume_data, indent=2)
            analysis_result = ai_agent.analyze_job_resume_match(job_description, resume_text, job_title="")
            
            # Safely extract match_score
            if not analysis_result:
                logger.warning("AI analysis returned empty result")
                return 50.0
            
            match_score = getattr(analysis_result, 'match_score', None)
            if match_score is None:
                logger.warning("AI analysis did not return match_score attribute")
                return 50.0
            
            # Convert and validate
            score = float(match_score)
            if score < 0 or score > 100:
                logger.warning(f"ATS score out of range: {score}, clamping to 0-100")
                score = max(0, min(100, score))
            
            logger.info(f"ATS score extracted successfully: {score}")
            return score

        except (ValueError, TypeError) as e:
            logger.error(f"Failed to convert ATS score to float: {e}")
            return 50.0
        except Exception as e:
            logger.error(f"ATS scoring failed: {e}")
            return 50.0
        
    """Hybrid AI + database-driven resume generation service."""
    
    # ========================================================================
    # MAIN FLOW: Hybrid Resume Generation (DB + AI)
    # ========================================================================
    
    def generate_resume(
        self,
        db: Session,
        user_id: int,
        job_description: str,
        job_application_id: Optional[int] = None
    ) -> ResumeResponse:
        """
        Main pipeline: Database as source of truth, AI for text enhancement only.
        
        Steps:
        1. Fetch all profile data
        2. Filter relevant projects, experience, certifications
        3. Build limited AI request (summary, descriptions only)
        4. Merge AI enhancements with DB data
        5. Calculate ATS score
        6. Save and return
        """
        try:
            logger.info(f"Starting hybrid resume generation for user {user_id}")
            
            # Step 1: Fetch all profile data
            profile_data = self.fetch_profile_data(db, user_id)
            
            # Step 2: Filter relevant data
            filtered_data = self.filter_profile_data(profile_data, job_description)
            logger.info(f"Filtered data: {len(filtered_data['projects'])} projects, {len(filtered_data['experience'])} experiences")
            
            # Step 3: Get AI enhancements (summary + descriptions only)
            ai_enhancements = self.enhance_with_ai(filtered_data, job_description)
            logger.info(f"AI enhancements generated successfully")
            
            # Step 4: Merge AI output with DB data
            resume_data = self.merge_resume_data(profile_data, filtered_data, ai_enhancements)
            logger.info(f"Resume data merged successfully")
            
            # Step 5: Calculate ATS score
            ats_score = self.get_ats_score_from_ai_analysis(job_description, resume_data)
            logger.info(f"ATS score calculated: {ats_score}")
            
            # Step 6: Save to database
            resume_entry = self.create_resume_entry(
                db=db,
                user_id=user_id,
                job_description=job_description,
                resume_data=resume_data,
                ats_score=ats_score,
                job_application_id=job_application_id
            )
            
            logger.info(f"Resume saved with ID {resume_entry.id}")
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
                        "category": s.skill_type
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
                ],
                # ADD this to profile_data dict in fetch_profile_data
                "social_links": [
                    {
                        "platform": l.platform,
                        "url": l.url,
                        "username": l.username
                    }
                    for l in db.query(UserSocialLink).filter(UserSocialLink.user_id == user_id).all()
                ],
            }
            logger.info(profile_data)
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Failed to fetch profile data for user {user_id}: {e}")
            raise
    
    # ========================================================================
    # STEP 2: Filter Relevant Data
    # ========================================================================
    
    def filter_profile_data(self, profile_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """
        Filter profile data to keep only relevant items.
        Returns: projects (top 3), experience (latest 2), certifications (relevant).
        """
        try:
            jd_keywords = set(extract_keywords_from_jd(job_description))
            
            filtered = {
                "projects": self.filter_projects(profile_data.get("projects", []), jd_keywords),
                "experience": self.filter_experience(profile_data.get("experience", [])),
                "certifications": self.filter_certifications(profile_data.get("certifications", []), jd_keywords),
                "skills": profile_data.get("skills", []),
                "education": profile_data.get("education", []),
                "personal_info": profile_data.get("personal_info", {})
            }
            
            logger.info(f"Filtered: {len(filtered['projects'])} projects, {len(filtered['experience'])} experiences, {len(filtered['certifications'])} certifications")
            return filtered
            
        except Exception as e:
            logger.error(f"Failed to filter profile data: {e}")
            raise
    
    # CORRECT — build scored_projects first
    def filter_projects(self, projects, jd_keywords):
        if not projects:
            return []
        
        scored_projects = []
        for p in projects:
            tech = [t.lower() for t in p.get("tech_stack", [])]
            desc = (p.get("description") or "").lower()
            combined = set(tech + re.findall(r'\b[a-z]{3,}\b', desc))
            score = len(combined & jd_keywords)
            scored_projects.append((score, p))
        
        scored_projects = sorted(scored_projects, key=lambda x: x[0], reverse=True)
        filtered = [p for score, p in scored_projects if score > 0]
        return (filtered if filtered else [p for _, p in scored_projects])[:3]
    
    def filter_experience(self, experiences: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Return latest 2 experiences sorted by start_date DESC.
        Preserve company_name, role, dates (do not modify).
        """
        try:
            if not experiences:
                return []
            
            def parse_date(date_str):
                try:
                    return datetime.fromisoformat(date_str) if date_str else datetime.min
                except Exception:
                    return datetime.min
            
            sorted_exp = sorted(
                experiences,
                key=lambda x: parse_date(x.get("start_date")),
                reverse=True
            )
            
            return sorted_exp[:2]
            
        except Exception as e:
            logger.error(f"Failed to filter experience: {e}")
            return experiences[:2]
    
    def filter_certifications(self, certifications: List[Dict[str, Any]], jd_keywords: set) -> List[Dict[str, Any]]:
        """
        Match certifications to job description keywords.
        Sort by relevance, then by date. Return 3-5 items.
        """
        try:
            if not certifications:
                return []
            
            scored_certs = []
            for cert in certifications:
                title = (cert.get("title") or "").lower()
                issuer = (cert.get("issuer") or "").lower()
                cert_text = f"{title} {issuer}"
                cert_words = set(re.findall(r'\b[a-z]{3,}\b', cert_text))
                
                match_score = len(cert_words & jd_keywords)
                scored_certs.append((match_score, cert))
            
            # Sort by relevance (descending), then by issue_date if available
            def get_issue_date(cert_tuple):
                cert = cert_tuple[1]
                try:
                    return datetime.fromisoformat(cert.get("issue_date")) if cert.get("issue_date") else datetime.min
                except:
                    return datetime.min
            
            scored_certs.sort(key=lambda x: (x[0], get_issue_date(x)), reverse=True)
            
            # Return 3-5 most relevant certifications
            result = [c[1] for c in scored_certs[:5]]
            return result if result else certifications[:3]
            
        except Exception as e:
            logger.error(f"Failed to filter certifications: {e}")
            return certifications[:5]
    
    # ========================================================================
    # STEP 3: AI Enhancement (Text Only - Summary & Descriptions)
    # ========================================================================
    
    def enhance_with_ai(self, filtered_data: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """
        Get AI enhancements for text only:
        - Professional summary
        - Project descriptions
        - Experience descriptions
        
        Strict rules: AI must not invent data, only enhance existing text.
        """
        try:
            prompt = self._build_enhancement_prompt(filtered_data, job_description)
            ai_output = self._call_ai_for_enhancements(prompt)
            logger.info("AI enhancements retrieved successfully")
            return ai_output
            
        except Exception as e:
            logger.error(f"AI enhancement failed: {e}. Using fallback (DB data only).")
            return self._fallback_enhancement(filtered_data)
    
    def _build_enhancement_prompt(self, filtered_data: Dict[str, Any], job_description: str) -> str:
        """
        Build a strict prompt for AI to enhance text only.
        Input is pre-filtered, so AI only enhances descriptions.
        """
        projects_json = json.dumps(filtered_data.get("projects", []))
        experience_json = json.dumps(filtered_data.get("experience", []))
        profile_summary = filtered_data.get("personal_info", {}).get("summary") or ""
        
        prompt = f"""You are an expert resume optimizer. Your task is ONLY to enhance text descriptions.

CRITICAL RULES - DO NOT VIOLATE:
- Do NOT invent new data
- Do NOT change job titles or company names
- Do NOT modify dates
- Do NOT add skills that don't exist
- ONLY rewrite existing descriptions to be more impactful and ATS-friendly
- Keep output concise (2-3 bullet points per item)
- Use strong action verbs
- Highlight metrics and outcomes

JOB DESCRIPTION:
{job_description}

EXISTING PROFILE DATA (DO NOT MODIFY FACTS):

Projects (tech stack already listed):
{projects_json}

Experience (company and role already set):
{experience_json}

Current Summary:
{profile_summary}

TASK:
1. Generate a 2-3 sentence professional summary tailored to this job
2. For EACH project: Improve the description (write 2-3 bullet points with impact focus)
3. For EACH experience: Improve the description (write 2-3 bullet points with metrics/outcomes)

RESPONSE FORMAT - STRICT JSON (no other text):
{{
  "summary": "2-3 sentence summary highlighting fit for this role",
  "projects": [
    {{
      "title": "SAME AS INPUT - DO NOT CHANGE",
      "description": "Bullet 1\\nBullet 2\\nBullet 3"
    }}
  ],
  "experience": [
    {{
      "company_name": "SAME AS INPUT - DO NOT CHANGE",
      "role": "SAME AS INPUT - DO NOT CHANGE",
      "description": "Bullet 1 with metric\\nBullet 2 with impact\\nBullet 3 with outcome"
    }}
  ]
}}

IMPORTANT:
- Return ONLY valid JSON
- NO explanations, NO code blocks
- Titles and company names MUST match input exactly
- Dates MUST NOT be modified
- Use bullet points (\\n) for clarity"""
        
        return prompt
    
    def _call_ai_for_enhancements(self, prompt: str) -> Dict[str, Any]:
        """Call Gemini API and parse response."""
        try:
            response = ai_agent.client.models.generate_content(
                model=ai_agent.model_name,
                contents=prompt
            )
            
            response_text = response.text.strip()
            
            # Remove code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            
            ai_output = json.loads(response_text)
            logger.info("AI response parsed successfully")
            return ai_output
            
        except json.JSONDecodeError as e:
            logger.warning(f"AI response JSON parse failed: {e}")
            # Use safer JSON extraction without regex
            try:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start >= 0 and end > start:
                    json_str = response_text[start:end]
                    return json.loads(json_str)
            except json.JSONDecodeError:
                logger.warning("Failed to extract JSON using fallback method")
                pass
            raise
    
    def _fallback_enhancement(self, filtered_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return minimal enhancements when AI fails (use DB data as-is)."""
        return {
            "summary": filtered_data.get("personal_info", {}).get("summary") or "Skilled professional",
            "projects": [
                {
                    "title": p.get("title"),
                    "description": p.get("description")
                }
                for p in filtered_data.get("projects", [])
            ],
            "experience": [
                {
                    "company_name": e.get("company_name"),
                    "role": e.get("role"),
                    "description": e.get("description")
                }
                for e in filtered_data.get("experience", [])
            ]
        }
    
    # ========================================================================
    # STEP 4: Merge DB Data with AI Enhancements
    # ========================================================================
    
    def merge_resume_data(
        self,
        profile_data: Dict[str, Any],
        filtered_data: Dict[str, Any],
        ai_enhancements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge AI enhancements with DB data.
        Database structure is the base; AI only updates text fields.
        """
        try:
            # Build projects with AI-enhanced descriptions
            projects = []
            ai_projects_map = {p.get("title"): p for p in ai_enhancements.get("projects", [])}
            for project in filtered_data.get("projects", []):
                ai_proj = ai_projects_map.get(project.get("title"), {})
                projects.append({
                    "title": project.get("title"),
                    "description": ai_proj.get("description", project.get("description")),
                    "tech_stack": project.get("tech_stack"),
                    "github_url": project.get("github_url")
                })
            
            # Build experience with AI-enhanced descriptions
            experiences = []
            ai_exp_map = {
                f"{e.get('company_name')}_{e.get('role')}": e
                for e in ai_enhancements.get("experience", [])
            }
            for exp in filtered_data.get("experience", []):
                key = f"{exp.get('company_name')}_{exp.get('role')}"
                ai_exp = ai_exp_map.get(key, {})
                experiences.append({
                    "company_name": exp.get("company_name"),
                    "role": exp.get("role"),
                    "start_date": exp.get("start_date"),
                    "end_date": exp.get("end_date"),
                    "is_current": exp.get("end_date") is None,
                    "description": ai_exp.get("description", exp.get("description"))
                })
            
            # Categorize skills by category
            skills_categorized = rebuild_skill_categories(filtered_data.get("skills", []))
            
            # Final resume structure
            resume_data = {
                "personal_info": {
                    "first_name": profile_data.get("personal_info", {}).get("first_name"),
                    "last_name": profile_data.get("personal_info", {}).get("last_name"),
                    "email": profile_data.get("personal_info", {}).get("email"),
                    "phone": profile_data.get("personal_info", {}).get("phone"),
                    "summary": ai_enhancements.get("summary", profile_data.get("personal_info", {}).get("summary"))
                },
                "summary": ai_enhancements.get("summary", profile_data.get("personal_info", {}).get("summary")),
                "skills": skills_categorized,
                "experience": experiences,
                "projects": projects,
                "education": filtered_data.get("education", []),
                "certifications": filtered_data.get("certifications", []),
                "social_links": {
                    link["platform"]: link["url"]
                    for link in profile_data.get("social_links", [])
                    if link.get("url")
                },
            }
            
            logger.info("Resume data merged successfully")
            return resume_data
            
        except Exception as e:
            logger.error(f"Failed to merge resume data: {e}")
            raise

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
            
            logger.info(f"Compared resumes: {old_ats:.0f}% -> {new_ats:.0f}%")
            
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

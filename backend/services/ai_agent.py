"""
AI Agent Service using Google Gemini (NEW SDK).
Analyzes job descriptions and resumes to provide matching insights.

IMPORTANT:
- Uses ONLY job description and resume text
- User notes are NEVER passed
"""

from google import genai
from core.config import settings
from schemas.job import AIAnalysisResult
import json
import logging

logger = logging.getLogger(__name__)


class AIAgent:
    """AI Agent for job-resume matching using Google Gemini."""

    def __init__(self):
        """Initialize Gemini client."""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-3-flash-preview"

    def analyze_job_resume_match(
        self,
        job_description: str,
        resume_text: str
    ) -> AIAnalysisResult:
        """
        Analyze job description and resume.

        CRITICAL:
        - ONLY job_description & resume_text
        - NO notes, NO metadata
        """

        try:
            prompt = self._build_analysis_prompt(job_description, resume_text)

            # ✅ CORRECT Gemini call (no generation_config)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            result_text = response.text.strip()
            result_dict = json.loads(result_text)

            analysis_result = AIAnalysisResult(**result_dict)

            logger.info(
                "AI analysis completed | Match score: %s",
                analysis_result.match_score
            )

            return analysis_result

        except json.JSONDecodeError:
            logger.error("Invalid JSON returned by Gemini: %s", response.text)
            raise ValueError("AI returned invalid JSON")

        except Exception as e:
            logger.exception("AI analysis failed")
            raise ValueError(f"AI analysis failed: {str(e)}")

    def _build_analysis_prompt(self, job_description: str, resume_text: str) -> str:
        """Build Gemini analysis prompt."""

        return f"""
You are an expert ATS analyzer and career advisor.

Analyze the JOB DESCRIPTION and RESUME below and return a STRICT JSON response.

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

Return ONLY valid JSON in this exact schema:

{{
  "job_summary": "2-3 sentence summary of the role",
  "required_skills": ["skill1", "skill2"],
  "resume_skills": ["skill1", "skill2"],
  "skill_gap": ["missing_skill1"],
  "match_score": 0,
  "preparation_tips": [
    "Actionable tip 1",
    "Actionable tip 2",
    "Actionable tip 3",
    "Actionable tip 4",
    "Actionable tip 5"
  ]
}}

Rules:
- JSON ONLY (no markdown, no explanation)
- match_score must be integer between 0 and 100
- Be concise and accurate
- Focus on skills, gaps, and preparation
- Preparation tips should focus on Techinical HR Interview like what are the key topics should focus (Mentioned in Job Description)
"""


# Singleton instance
ai_agent = AIAgent()

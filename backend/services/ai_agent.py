"""
AI Agent Service using Google Gemini (NEW SDK).
Analyzes job descriptions and resumes to provide matching insights.

"""

from google import genai
from core.config import settings
from schemas.job import AIAnalysisResult
import json
import logging

logger = logging.getLogger(__name__)


class AIAgent:

    def __init__(self):

        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-3-flash-preview"

    def analyze_job_resume_match(
        self,
        job_description: str,
        resume_text: str,
        job_title: str
    ) -> AIAnalysisResult:

        try:
            prompt = self._build_analysis_prompt(job_description, resume_text, job_title)

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

    def _build_analysis_prompt(self, job_description: str, resume_text: str, job_title: str) -> str:

        return f"""

You are an expert ATS analyzer and {job_title} advisor.

Analyze the JOB DESCRIPTION and RESUME and return STRICT JSON.

---

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

---

### TASKS:

1. Extract top 6–8 REQUIRED SKILLS from the job description
   - Focus on specific tools, technologies, and languages only

2. Extract RESUME SKILLS
   - Only include explicitly mentioned skills
   - Do NOT infer or assume

3. Identify SKILL GAP
   - Skills in job description but missing in resume

---


### OUTPUT (STRICT JSON ONLY):

{{
"job_summary": "2-3 concise sentences",

"required_skills": [],

"resume_skills": [],

"skill_gap": [],

"match_score": 0,

"preparation_tips": [
"5 specific technical + HR tips based ONLY on missing skills"
]
}}

---

### RULES:

* Return ONLY valid JSON (no markdown, no explanation)
* match_score must be integer between 0 and 100
* Limit required_skills to top 6–8 only
* Avoid duplicates in any list
* Be concise and precise
* Focus on relevant and high-impact skills only
* Do NOT hallucinate skills not present in job description or resume
* Do not expand a skill into related concepts
* Each skill must be a single, distinct item
* Avoid combining concepts with tools
* List each skill separately (no grouping)
* Only include explicitly mentioned skills

"""

    def generate_improvement_plan(self, context: dict) -> dict:
        """
        Generate an AI-powered improvement plan based on interview feedback.
        
        Args:
            context: Dictionary containing job_title, company_name, job_description,
                    resume_text, ai_job_analysis, and interview_feedback
        
        Returns:
            Dictionary with failure_stage, weak_areas, recommended_topics, 
            practice_problems, and improvement_strategy
        """
        try:
            prompt = self._build_improvement_plan_prompt(context)
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            result_text = response.text.strip()
            result_dict = json.loads(result_text)
            
            logger.info(
                "Improvement plan generated | Weak areas identified: %s",
                len(result_dict.get("weak_areas", []))
            )
            
            return result_dict
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON returned by Gemini: %s", response.text if 'response' in locals() else "Unknown")
            raise ValueError("AI returned invalid JSON")
        
        except Exception as e:
            logger.exception("Improvement plan generation failed")
            raise ValueError(f"Improvement plan generation failed: {str(e)}")
    
    def _build_improvement_plan_prompt(self, context: dict) -> str:
        """
        Build the prompt for AI improvement plan generation.
        
        Args:
            context: Dictionary with job and interview data
        
        Returns:
            Formatted prompt string
        """
        job_title = context.get("job_title", "")
        company_name = context.get("company_name", "")
        job_description = context.get("job_description", "")
        resume_text = context.get("resume_text", "")
        ai_job_analysis = context.get("ai_job_analysis", {})
        interview_feedback = context.get("interview_feedback", {})
        
        # Format rounds information
        rounds_info = ""
        for round_data in interview_feedback.get("rounds", []):
            rounds_info += f"\n- Round {round_data.get('round_number')}: {round_data.get('type')} ({round_data.get('difficulty')})"
            rounds_info += f"\n  Result: {round_data.get('result')}"
            if round_data.get('topics'):
                rounds_info += f"\n  Topics: {', '.join(round_data.get('topics', []))}"
            if round_data.get('notes'):
                rounds_info += f"\n  Notes: {round_data.get('notes')}"
        
        # Format AI analysis
        ai_analysis_info = ""
        if ai_job_analysis:
            if isinstance(ai_job_analysis, dict):
                ai_analysis_info = f"Job match score: {ai_job_analysis.get('match_score', 'N/A')}/100\n"
                ai_analysis_info += f"Skill gaps identified: {', '.join(ai_job_analysis.get('skill_gap', []))}\n"
                ai_analysis_info += f"Preparation tips: {', '.join(ai_job_analysis.get('preparation_tips', []))}"
        
        return f"""
You are an expert career coach and interview preparation specialist.

Analyze the interview feedback below and generate a personalized improvement plan.

JOB DETAILS:
- Position: {job_title}
- Company: {company_name}

JOB DESCRIPTION:
{job_description}

CANDIDATE'S RESUME:
{resume_text}

INITIAL AI JOB ANALYSIS:
{ai_analysis_info}

INTERVIEW FEEDBACK:
- Total Rounds: {interview_feedback.get('total_rounds', 'N/A')}
- Rounds Passed: {interview_feedback.get('rounds_passed', 'N/A')}
- Rounds Failed: {interview_feedback.get('rounds_failed', 'N/A')}

INTERVIEW ROUNDS DETAILS:{rounds_info}

Based on the above information, generate a detailed improvement plan. Return ONLY valid JSON in this exact schema:

{{
  "failure_stage": "At which round/stage did the candidate primarily fail (e.g., 'Round 2: HR Interview')",
  "weak_areas": [
    {{
      "area": "Specific weak area (e.g., 'System Design')",
      "reason": "Why this was a weakness based on feedback"
    }}
  ],
  "recommended_topics": [
    "Topic 1 to learn/practice",
    "Topic 2 to learn/practice",
    "Topic 3 to learn/practice",
    "Topic 4 to learn/practice",
    "Topic 5 to learn/practice"
  ],
  "practice_problems": [
    {{
      "title": "Problem title",
      "description": "Brief description of the problem",
      "difficulty": "easy|medium|hard"
    }}
  ],
  "improvement_strategy": [
    "Step 1: Specific action for improvement",
    "Step 2: Specific action for improvement",
    "Step 3: Specific action for improvement",
    "Step 4: Specific action for improvement",
    "Step 5: Specific action for improvement"
  ]
}}

Rules:
- JSON ONLY (no markdown, no explanation)
- Be specific and actionable
- Focus on the candidate's actual weaknesses from the interview
- Recommend topics directly related to failed rounds
- Include at least 3 practice problems
- Strategy should be implementable within 2-4 weeks
"""

ai_agent = AIAgent()

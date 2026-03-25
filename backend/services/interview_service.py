"""
Interview Service Layer.
Handles business logic for interview feedback management and improvement plan generation.
"""
import json
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models.interview import InterviewFeedback, InterviewRound
from models.job import JobApplication
from schemas.interview import (
    InterviewFeedbackCreate,
    InterviewFeedbackResponse,
    InterviewFeedbackSummary,
    InterviewRoundResponse,
    ImprovementPlanResponse,
    ImprovementArea,
    PracticeProblem,
)
from services.resume_extractor import resume_extractor
from services.ai_agent import ai_agent

logger = logging.getLogger(__name__)


class InterviewService:
    """Service for managing interview feedback and improvement plans."""
    
    def submit_interview_feedback(
        self,
        db: Session,
        job_application_id: int,
        feedback_data: InterviewFeedbackCreate
    ) -> InterviewFeedbackResponse:
        """
        Submit interview feedback with rounds for a job application.
        
        Args:
            db: Database session
            job_application_id: ID of the job application
            feedback_data: Interview feedback data with rounds
            
        Returns:
            InterviewFeedbackResponse: Created feedback with all rounds
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate that rounds_passed <= total_rounds
            if feedback_data.rounds_passed > feedback_data.total_rounds:
                raise ValueError("Rounds passed cannot exceed total rounds")
            
            # Validate that number of rounds matches total_rounds
            if len(feedback_data.rounds) != feedback_data.total_rounds:
                raise ValueError(f"Expected {feedback_data.total_rounds} rounds, got {len(feedback_data.rounds)}")
            
            # Create interview feedback record
            interview_feedback = InterviewFeedback(
                job_application_id=job_application_id,
                total_rounds=feedback_data.total_rounds,
                rounds_passed=feedback_data.rounds_passed,
            )
            db.add(interview_feedback)
            db.flush()  # Flush to get the ID
            
            # Create interview rounds
            for round_data in feedback_data.rounds:
                interview_round = InterviewRound(
                    interview_feedback_id=interview_feedback.id,
                    round_number=round_data.round_number,
                    type=round_data.type,
                    topics=round_data.topics or [],
                    difficulty=round_data.difficulty,
                    result=round_data.result,
                    notes=round_data.notes,
                )
                db.add(interview_round)
            
            db.commit()
            db.refresh(interview_feedback)
            
            logger.info(f"Created interview feedback for job application {job_application_id}")
            return InterviewFeedbackResponse.model_validate(interview_feedback)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to submit interview feedback: {e}")
            raise
    
    def get_interview_feedback(
        self,
        db: Session,
        job_application_id: int
    ) -> InterviewFeedbackResponse:
        """
        Get interview feedback and rounds for a job application.
        Includes any stored improvement plan if available.
        
        Args:
            db: Database session
            job_application_id: ID of the job application
            
        Returns:
            InterviewFeedbackResponse: Feedback with rounds and improvement plan
            
        Raises:
            ValueError: If feedback not found
        """
        try:
            interview_feedback = db.query(InterviewFeedback).filter(
                InterviewFeedback.job_application_id == job_application_id
            ).first()
            
            if not interview_feedback:
                raise ValueError(f"No interview feedback found for job application {job_application_id}")
            
            # Parse improvement plan if available
            improvement_plan = None
            if interview_feedback.improvement_plan:
                try:
                    improvement_plan = self._parse_improvement_plan_response(interview_feedback.improvement_plan)
                except Exception as e:
                    logger.warning(f"Could not parse stored improvement plan: {e}")
            
            logger.info(f"Retrieved interview feedback for job application {job_application_id}")
            return InterviewFeedbackResponse(
                id=interview_feedback.id,
                job_application_id=interview_feedback.job_application_id,
                total_rounds=interview_feedback.total_rounds,
                rounds_passed=interview_feedback.rounds_passed,
                interview_rounds=[
                    InterviewRoundResponse.model_validate(r)
                    for r in interview_feedback.interview_rounds
                ],
                improvement_plan=improvement_plan,
                created_at=interview_feedback.created_at,
            )
            
        except Exception as e:
            logger.error(f"Failed to get interview feedback: {e}")
            raise
    
    def generate_improvement_plan(
        self,
        db: Session,
        job_application: JobApplication,
        resume_text: str,
    ) -> ImprovementPlanResponse:
        """
        Generate an AI-powered improvement plan based on interview feedback.
        Implements caching: if a plan already exists, returns the stored one.
        
        Args:
            db: Database session
            job_application: The job application object
            resume_text: Extracted resume text
            
        Returns:
            ImprovementPlanResponse: AI-generated improvement plan
            
        Raises:
            ValueError: If data is incomplete or AI generation fails
        """
        try:
            # Get interview feedback
            interview_feedback = db.query(InterviewFeedback).filter(
                InterviewFeedback.job_application_id == job_application.id
            ).first()
            
            if not interview_feedback:
                raise ValueError("No interview feedback found for this job application")
            
            # Check if improvement plan already exists (caching)
            if interview_feedback.improvement_plan:
                logger.info(f"Returning cached improvement plan for job application {job_application.id}")
                return self._parse_improvement_plan_response(interview_feedback.improvement_plan)
            
            # Build context for AI
            context = self._build_improvement_plan_context(
                job_application=job_application,
                interview_feedback=interview_feedback,
                resume_text=resume_text,
            )
            
            # Call AI agent to generate improvement plan
            logger.info(f"Generating improvement plan for job application {job_application.id}")
            improvement_plan_data = ai_agent.generate_improvement_plan(context)
            
            # Parse and validate response
            improvement_plan = self._parse_improvement_plan_response(improvement_plan_data)
            
            # Store the improvement plan in the database
            interview_feedback.improvement_plan = improvement_plan_data
            db.commit()
            db.refresh(interview_feedback)
            
            logger.info(f"Successfully generated and stored improvement plan for job application {job_application.id}")
            return improvement_plan
            
        except Exception as e:
            logger.error(f"Failed to generate improvement plan: {e}")
            raise
    
    def _build_improvement_plan_context(
        self,
        job_application: JobApplication,
        interview_feedback: InterviewFeedback,
        resume_text: str,
    ) -> Dict[str, Any]:
        """
        Build structured context for AI improvement plan generation.
        
        Args:
            job_application: The job application
            interview_feedback: The interview feedback data
            resume_text: Extracted resume text
            
        Returns:
            Dictionary with structured context for AI
        """
        # Get interview rounds data
        rounds_data = []
        for round_obj in interview_feedback.interview_rounds:
            rounds_data.append({
                "round_number": round_obj.round_number,
                "type": round_obj.type,
                "topics": round_obj.topics or [],
                "difficulty": round_obj.difficulty,
                "result": round_obj.result,
                "notes": round_obj.notes or "",
            })
        
        # Extract AI analysis if available
        ai_analysis = {}
        if job_application.ai_analysis:
            try:
                if isinstance(job_application.ai_analysis, dict):
                    ai_analysis = job_application.ai_analysis
                elif isinstance(job_application.ai_analysis, str):
                    ai_analysis = json.loads(job_application.ai_analysis)
            except json.JSONDecodeError:
                logger.warning(f"Could not parse AI analysis for job {job_application.id}")
        
        context = {
            "job_title": job_application.job_title,
            "company_name": job_application.company_name,
            "job_description": job_application.job_description,
            "resume_text": resume_text,
            "ai_job_analysis": ai_analysis,
            "interview_feedback": {
                "total_rounds": interview_feedback.total_rounds,
                "rounds_passed": interview_feedback.rounds_passed,
                "rounds_failed": interview_feedback.total_rounds - interview_feedback.rounds_passed,
                "rounds": rounds_data,
            }
        }
        
        return context
    
    def _parse_improvement_plan_response(self, response_data: Dict[str, Any]) -> ImprovementPlanResponse:
        """
        Parse and validate AI response for improvement plan.
        
        Args:
            response_data: Raw response from AI agent
            
        Returns:
            ImprovementPlanResponse: Validated improvement plan
            
        Raises:
            ValueError: If response format is invalid
        """
        try:
            # Parse weak areas
            weak_areas = []
            if isinstance(response_data.get("weak_areas"), list):
                for area in response_data["weak_areas"]:
                    if isinstance(area, dict):
                        weak_areas.append(ImprovementArea(
                            area=area.get("area", "Unknown"),
                            reason=area.get("reason", ""),
                        ))
                    elif isinstance(area, str):
                        weak_areas.append(ImprovementArea(
                            area=area,
                            reason="",
                        ))
            
            # Parse practice problems
            practice_problems = []
            if isinstance(response_data.get("practice_problems"), list):
                for problem in response_data["practice_problems"]:
                    if isinstance(problem, dict):
                        practice_problems.append(PracticeProblem(
                            title=problem.get("title", "Problem"),
                            description=problem.get("description", ""),
                            difficulty=problem.get("difficulty", "medium"),
                        ))
                    elif isinstance(problem, str):
                        practice_problems.append(PracticeProblem(
                            title=problem,
                            description="",
                            difficulty="medium",
                        ))
            
            # Ensure required_topics is a list of strings
            recommended_topics = response_data.get("recommended_topics", [])
            if not isinstance(recommended_topics, list):
                recommended_topics = [recommended_topics]
            recommended_topics = [str(t) for t in recommended_topics]
            
            # Ensure improvement_strategy is a list of strings
            improvement_strategy = response_data.get("improvement_strategy", [])
            if not isinstance(improvement_strategy, list):
                improvement_strategy = [improvement_strategy]
            improvement_strategy = [str(s) for s in improvement_strategy]
            
            return ImprovementPlanResponse(
                failure_stage=response_data.get("failure_stage", "Unknown stage"),
                weak_areas=weak_areas,
                recommended_topics=recommended_topics,
                practice_problems=practice_problems,
                improvement_strategy=improvement_strategy,
            )
            
        except Exception as e:
            logger.error(f"Failed to parse improvement plan response: {e}")
            raise ValueError(f"Invalid AI response format: {str(e)}")


interview_service = InterviewService()

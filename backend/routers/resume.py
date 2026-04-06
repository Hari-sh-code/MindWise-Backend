# Resume router removed.
# All resume generation endpoints have been disabled to maintain system stability.
# The ai_analysis field on job_applications is reserved for AI job analysis only.

from fastapi import APIRouter

router = APIRouter(prefix="/resume", tags=["Resume"])

# No routes registered — resume feature is disabled.

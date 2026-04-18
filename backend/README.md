# MindWise Backend

FastAPI backend for MindWise, an AI-powered job application decision-support system for freshers.

## What We Have Done

### Core implementation
- Built a FastAPI backend with modular routing (`auth`, `ai`, `jobs`, `user`).
- Added PostgreSQL integration using SQLAlchemy ORM.
- Added JWT-based authentication with password hashing (`passlib` + `python-jose`).
- Added AI analysis flow using Google Gemini (`google-genai`).
- Added resume text extraction from Google Drive PDF links.

### Profile Management System (NEW)
- **Complete CRUD**: Comprehensive profile sections including Basic Info, Skills, Projects, Experience, Education, Certifications, and Social Links.
- **Hybrid Social Links**: Implemented intelligent username extraction from platform URLs (LinkedIn, GitHub, LeetCode, etc.) while allowing manual overrides.
- **Structured Experience**: Refactored experience tracking from simple strings to structured `start_date` and `end_date` (Date type) with automatic "Present" detection for current roles.
- **Aggregated Responses**: Provided a `GET /user/profile` endpoint returning the complete professional profile in a single optimized payload.

### Resume Optimization System (NEW)
- **Rule-Based Generation**: Generates ATS-optimized resumes without AI dependency.
- **Keyword Extraction**: Smart keyword extraction from job descriptions with stop-word filtering and deduplication.
- **Relevance Scoring**: Scores skills, projects, and experience based on job keyword matches; filters and reorders content by relevance.
- **ATS Score Calculation**: Composite scoring formula (35% skill match + 40% keyword coverage + 25% structure completeness).
- **AI-Optional Enhancement**: Optional Gemini API enhancement for suggestions; non-blocking if unavailable.
- **Versioning**: Automatic version tracking per user for resume history and comparison.
- **Resume Comparison**: Compare old vs new resumes with detailed improvement metrics (ATS score improvement, keyword coverage improvement, specific improvements list).
- **Editable Preview**: Full edit support for resume content before finalization.

### Recent refactors and cleanup
- **Notes Module Removal**: Removed the `Notes` module and `user_notes` fields from job models and schemas for a leaner architecture.
- **Schema Alignment**: Strictly aligned SQLAlchemy models with the PostgreSQL database schema.

## Tech Stack
- Python 3.12+
- FastAPI + Uvicorn
- SQLAlchemy
- PostgreSQL (Supabase supported)
- Pydantic v2
- Google Gemini SDK (`google-genai`)
- PDF parsing (`pdfplumber`)

## Project Structure

```text
backend/
├── main.py
├── database.py
├── core/
│   ├── config.py
│   └── auth.py
├── models/
│   ├── user.py
│   ├── job.py
│   ├── user_profile.py
│   ├── interview.py
│   └── resume.py
├── schemas/
│   ├── user.py
│   ├── job.py
│   ├── profile.py
│   ├── interview.py
│   └── resume.py
├── routers/
│   ├── auth.py
│   ├── ai.py
│   ├── jobs.py
│   ├── interviews.py
│   ├── resume.py
│   └── profile.py
└── services/
    ├── ai_agent.py
    ├── resume_extractor.py
    ├── resume_service.py
    ├── interview_service.py
    ├── job_extractor.py
    └── profile_service.py
```

## Environment Variables
Create a `.env` file in the backend root.

Required keys:
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `GEMINI_API_KEY`
- `ALLOWED_ORIGINS` (comma-separated or `*`)
- `APP_NAME`
- `APP_VERSION`
- `DEBUG`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the Server

```bash
uvicorn main:app --reload
```

App URLs:
- API: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Database
- Tables are created on startup from SQLAlchemy models via `init_db()` in `main.py` lifespan (if using development mode).
- **Active Tables**:
  - `users`
  - `job_applications`
  - `interview_feedback`
  - `interview_rounds`
  - `resumes`
  - `user_profiles`
  - `user_skills`
  - `user_projects`
  - `user_experience`
  - `user_education`
  - `user_certifications`
  - `user_social_links`

## Key API Endpoints

### Authentication
- `POST /auth/register`: Create user and return JWT.
- `POST /auth/login`: Authenticated via email/password.
- `GET /auth/me`: Get current user details.

### Profile Management
- `GET /user/profile`: Fetch the entire profile (Basic + Skills + Projects + Exp + Edu + Cert + Social).
- `PUT /user/profile`: Update basic info (phone, summary).
- `POST /user/{section}`: Generic pattern for adding profile components.

### Resume Optimization
- `POST /resume/generate`: Generate ATS-optimized resume for a job description (rule-based, AI-optional).
- `GET /resume/`: List all user resumes (paginated).
- `GET /resume/{id}`: Get single resume with full details.
- `PUT /resume/{id}`: Update resume content (editable preview).
- `POST /resume/compare`: Compare two resume versions with improvement metrics.

### AI and Job Flows
- `POST /ai/analyze-job`: Analyze Match between a Google Drive resume and a job description.
- `GET /jobs/`: List all analyzed job applications.
- `PATCH /jobs/{job_id}`: Update application status.

### Interview Feedback
- `POST /jobs/{job_id}/interview-feedback`: Submit interview feedback with rounds.
- `GET /jobs/{job_id}/interview-feedback`: Get interview feedback for a job.
- `POST /jobs/{job_id}/improvement-plan`: Generate AI-powered improvement plan.

## Security Notes
- `.env` is git-ignored and should never be committed.
- Rotate `SECRET_KEY`, DB credentials, and API keys if exposed.
- Restrict `ALLOWED_ORIGINS` in production.

## Known Codebase Notes
- **Resume Engine**: Production-ready Resume Optimization Engine with rule-based generation (AI-optional).
  - Keyword extraction, relevance scoring, ATS calculation, versioning, and comparison.
  - Located in `models/resume.py`, `schemas/resume.py`, `services/resume_service.py`, `routers/resume.py`.
- `services/job_extractor.py` handles manual text processing for `job_description`.
- **AI Integration**: Optional AI enhancements via Google Gemini (`google-genai`) for interview improvement plans and resume suggestions. Non-blocking if unavailable.

## Suggested Next Improvements
- Implement Alembic migrations for production database management.
- Add unit/integration tests for the Profile CRUD logic.
- Add centralized exception handlers for consistent API error responses.
- Implement soft-delete or archive functionality for job applications.
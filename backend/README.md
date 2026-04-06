# MindWise Backend

FastAPI backend for MindWise, an AI-powered job application decision-support system for freshers.

## What We Have Done

### Core implementation
- Built a FastAPI backend with modular routing (`auth`, `ai`, `jobs`).
- Added PostgreSQL integration using SQLAlchemy ORM.
- Added JWT-based authentication with password hashing (`passlib` + `python-jose`).
- Added AI analysis flow using Google Gemini (`google-genai`).
- Added resume text extraction from Google Drive PDF links.

### Recent refactors and cleanup
- Removed the complete Notes module from backend (models, schemas, router, and references).
- Switched away from job URL scraping flow in active endpoints.
- Kept job analysis based on manually provided `job_description` input.
- Added/kept a job description processing utility (`services/job_extractor.py`) that now contains `JobDescriptionProcessor`.

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
│   └── job.py
├── schemas/
│   ├── user.py
│   └── job.py
├── routers/
│   ├── auth.py
│   ├── ai.py
│   └── jobs.py
└── services/
    ├── ai_agent.py
    ├── resume_extractor.py
    └── job_extractor.py
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
- Tables are created on startup from SQLAlchemy models via `init_db()` in `main.py` lifespan.
- Active models:
  - `users`
  - `job_applications`

## Authentication Flow

### Register
- `POST /auth/register`
- Creates user and returns JWT token + user payload.

### Login
- `POST /auth/login`
- Uses `OAuth2PasswordRequestForm` (`username` = email, `password` = password).
- Returns JWT token + user payload.

### Current User
- `GET /auth/me`
- Requires `Authorization: Bearer <token>`.

## AI and Job Flows

### Analyze Job vs Resume
- `POST /ai/analyze-job`
- Input:
  - `company_name`
  - `job_title`
  - `job_description` (manually pasted)
  - `resume_drive_link`
  
- Flow:
  1. Extract resume text from Google Drive PDF.
  2. Analyze match with Gemini.
  3. Save to `job_applications` with `ai_analysis` and status `analyzed`.

### Job CRUD
- `GET /jobs/` (paginated, optional status filter)
- `GET /jobs/{job_id}`
- `PATCH /jobs/{job_id}`
- `DELETE /jobs/{job_id}`

## Security Notes
- `.env` is git-ignored and should never be committed.
- Rotate `SECRET_KEY`, DB credentials, and API keys if exposed.
- Restrict `ALLOWED_ORIGINS` in production.

## Known Codebase Notes
- `services/job_extractor.py` now contains `JobDescriptionProcessor` (manual text processor) rather than URL scraping logic.
- `schemas/job_analysis.py` and `/jobs/analyze` are not present in the current checked-in state.

## Suggested Next Improvements
- Add explicit request/response schema for a dedicated `/jobs/analyze` endpoint if needed.
- Add Alembic migrations for controlled schema evolution.
- Add unit/integration tests for auth, resume extraction, and AI analysis routes.
- Add centralized exception handlers for consistent API error responses.
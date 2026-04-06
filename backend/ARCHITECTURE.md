# MindWise Backend Architecture

## Overview

MindWise is an AI-powered job application decision-support system tailored for freshers. The backend is designed as a modular, RESTful API built with **FastAPI** and **Python 3.12+**. It uses **SQLAlchemy** for ORM over a **PostgreSQL** database and integrates seamlessly with **Google Gemini SDK** to provide rich AI analysis for job applications, resumes, and interview feedback.

---

## 🏗️ Architectural Layers

The backend follows a standard layered architecture for separation of concerns:

1. **Routing Layer (`routers/`)**: FastAPI endpoints grouping endpoints by resource domain.
2. **Service/Business Logic Layer (`services/`)**: Contains reusable, domain-specific logic and integrations (e.g., AI Agents, PDF Extraction).
3. **Data Access & Modeling (`models/`)**: SQLAlchemy declarative models mapping objects to PostgreSQL tables.
4. **Validation Layer (`schemas/`)**: Pydantic models for strict Request/Response validation, data serialization, and OpenAPI documentation.
5. **Core Module (`core/`)**: Cross-cutting utilities like JWT authentication, config management, and security logic.

---

## 🗄️ Domain Modules & Capabilities

### 1. Authentication & Users
- **Components:** `routers/auth.py`, `models/user.py`
- **Features:**
  - JWT-based authorization (Token generation & validation).
  - Password hashing using `passlib` and `bcrypt`.
  - Defines the core `User` model, linking all subsequent profile, job, and interview data.

### 2. Comprehensive Profile Management
- **Components:** `routers/profile.py`, `services/profile_service.py`, `models/user_profile.py`
- **Models:** Built distinct interconnected tables (`UserProfile`, `UserSkill`, `UserProject`, `UserExperience`, `UserEducation`, `UserCertification`, `UserSocialLink`).
- **Features:** 
  - Tracks detailed candidates' credentials to power dynamic AI features natively.
  - Supports full CRUD actions for each profile subset (e.g. adding a tech skill, recording a degree).
  - *Recent Fix:* Streamlined models by removing unused/un-migrated columns (like `updated_at` and `proficiency`), strictly syncing SQLAlchemy classes with PostgreSQL tables to prevent 500 errors.

### 3. Job Extraction & AI Analysis
- **Components:** `routers/ai.py`, `services/ai_agent.py`, `services/resume_extractor.py`, `services/job_extractor.py`
- **Features:**
  - Retrieves PDF resumes via Google Drive links (`pdfplumber` backend).
  - Leverages Google Gemini (`google-genai`) to map the extracted resume text against a provided Job Description.
  - Generates comprehensive suitability reports: Fit percentages, missing skills, and strategic recommendations.

### 4. Job Application Tracking
- **Components:** `routers/jobs.py`, `models/job.py`
- **Features:**
  - Simple Kanban-esque CRUD tracking for applications (`draft`, `analyzed`, `applied`, `interviewing`, `rejected`, `offered`).
  - Seamlessly links previous AI analyses to the saved jobs to persist AI insights.

### 5. AI-Powered Resume Generation
- **Components:** `routers/resume.py`, `services/resume_service.py`
- **Features:**
  - Constructs highly focused, **ATS-optimized resumes** tailored dynamically to specific jobs.
  - Generative process gathers data from the **Profile Management** module (basic info, skills, projects, experience).
  - Outputs a structured JSON AI response, which is then dynamically converted into clean HTML representations for inline viewing/download.

### 6. Interview Feedback & Improvement Tracking
- **Components:** `routers/interviews.py`, `models/interview.py`, `services/interview_service.py`
- **Features:**
  - Users log individual interview rounds mapped to a `JobApplication`.
  - AI engine generates a tactical **Improvement Plan** based on user-provided feedback (what went right/wrong).

---

## 🛠️ Technology Stack

| Capability | Technology |
|---|---|
| **Web Framework** | FastAPI (ASGI via Uvicorn) |
| **Database** | PostgreSQL |
| **ORM** | SQLAlchemy 2.0+ |
| **Serialization** | Pydantic v2 |
| **AI Integration** | `google-genai` (Google Gemini 1.5/3.0) |
| **Authentication** | `python-jose` (JWT), `passlib[bcrypt]` |
| **PDF Processing** | `pdfplumber` |
| **HTML/PDF Generation** | `WeasyPrint` |

---

## 🔄 Interaction Flow Example: Resume Generation

1. **Client** hits `POST /resume/generate/{job_id}`.
2. **Router (`routers/resume.py`)** extracts JWT user info.
3. **Service (`resume_service.py`)** pulls the `User`, all associated `UserProfile` relationships, and the `JobApplication` target.
4. **Service** constructs a vast LLM prompt contextualized by the User's explicit Profile credentials vs. the target Job Description.
5. **Gemini AI** responds with a strictly structured ATS JSON Resume.
6. **Backend** saves/caches the JSON and returns it alongside an HTML representation to the frontend.

---

## 🚀 Recent Architecture Iterations

1. **Decoupling Data Sync:** The model base was cleaned regarding strictly non-migrated columns. E.g., `proficiency` from the `UserSkill` model and isolated tracking timestamps were removed so APIs match the live PostgreSQL instances flawlessly without dropping tables.
2. **Deprecation of "Notes" logic:** We transitioned away from loose Note objects in favor of formal and structured Interview Feedback models and Improvement Plans.
3. **Structured Resume Builder:** We transitioned from simple scraped extraction logic to a deeply integrated generative module that references internal Relational DB instances (Projects, Exp, Skills).

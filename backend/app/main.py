from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Jobs:
    job_id: int
    company_name: str
    role: str
    job_link: str
    resume_version: str

    def __init__(self, job_id: int, company_name: str, role: str, job_link: str, resume_version: str):
        self.job_id = job_id
        self.company_name = company_name
        self.role = role
        self.job_link = job_link
        self.resume_version = resume_version

class JobRequest(BaseModel):
    job_id: Optional[int] = None
    company_name: str
    role: str
    job_link: str
    resume_version: str

JOBS = [
    Jobs(1, "Meta", "Software Developer Intern", "https://www.meta.com/careers/softwareDeveloperIntern", "https://www.drive.com/resume_meta_softwareDeveloperIntern"),
    Jobs(2, "Amazon", "Data Engineering Intern", "https://www.amazon.com/careers/dataEngineeringIntern", "https://www.drive.com/resume_amazon_dataEngineeringIntern"),
]

@app.get("/jobs")
async def get_jobs(data = JOBS):
    return data

@app.post("/create_job")
async def create_job(job_request: JobRequest):
    new_job = Jobs(**job_request.model_dump())
    JOBS.append(find_book_id(new_job))

def find_book_id(job : Jobs):
    if len(JOBS) > 0:
        job.job_id = JOBS[-1].job_id + 1
    else:
        job.job_id = 1
    return job

@app.get("/jobs/{role}")
async def get_job(role: str):
    for job in JOBS:
        if job["role"] == role:
            return job
    return None
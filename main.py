from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

demo_data = [
    {
        "job_id": 1,
        "company_name": "Meta",
        "role": "Software Developer Intern",
        "job_link": "https://www.meta.com/careers/softwareDeveloperIntern",
        "resume_version": 2
    },
    {
        "job_id": 2,
        "company_name": "Amazon",
        "role": "Data Engineering Intern",
        "job_link": "https://www.amazon.com/careers/dataEngineeringIntern",
        "resume_version": 1
    }
]

class Job(BaseModel):
    job_id: int
    company_name: str
    role: str
    job_link: str

@app.get("/jobs")
async def get_jobs(data = demo_data):
    return data

@app.post("/create_job")
async def create_job(job: Job):
    demo_data.append(job.model_dump())
    return job

@app.get("/jobs/{role}")
async def get_job(role: str):
    for job in demo_data:
        if job["role"] == role:
            return job
    return None
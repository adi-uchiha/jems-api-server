from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from scripts.enqueue_task import enqueue_task

router = APIRouter()

class TaskCreate(BaseModel):
    job_title: str
    location: str
    country: str
    num_jobs: int
    site_names: List[str]

@router.post("/create")
async def create_task(task: TaskCreate):
    try:
        task_id = enqueue_task(
            job_title=task.job_title,
            location=task.location,
            country=task.country,
            num_jobs=task.num_jobs,
            site_names=task.site_names
        )
        return {"status": "success", "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

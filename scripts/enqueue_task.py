from uuid import uuid4
from datetime import datetime
from pathlib import Path
import sys

project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app.services.celery_blueprint import process_task

def enqueue_task(job_title: str, location: str, country: str, num_jobs: int, site_names: list):
    """Enqueue a job scraping task"""
    task_data = {
        "request_id": str(uuid4()),
        "task_type": "SCRAPE_AND_EMBED_JOB",
        "parameters": {
            "job_title": job_title,
            "location": location,
            "country": country,
            "num_jobs": num_jobs,
            "site_name": site_names
        },
        "metadata": {
            "user_id": "system_test",  # Can be parameterized if needed
            "request_timestamp": datetime.utcnow().isoformat()
        }
    }
    
    # Send task to Celery
    result = process_task.delay(task_data)
    return result.id

if __name__ == "__main__":
    # Example usage
    task_id = enqueue_task(
        job_title="Software Engineer",
        location="Remote",
        country="us",
        num_jobs=25,
        site_names=["linkedin", "glassdoor"]
    )
    print(f"Enqueued task with id: {task_id}")

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class CeleryTask(BaseModel):
    id: Optional[int] = None
    task_id: str
    status: str = "PENDING"
    task_name: str
    task_args: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retries: int = 0
    last_retry_at: Optional[datetime] = None

class RawJob(BaseModel):
    id: Optional[int] = None
    task_id: str
    external_id: Optional[str] = None
    raw_data: Dict[str, Any]
    source_site: Optional[str] = None
    title: str
    company: str
    location: Optional[str] = None
    job_url: Optional[str] = None
    job_type: Optional[str] = None
    salary_interval: Optional[str] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_currency: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

class ProcessedJob(BaseModel):
    id: Optional[int] = None
    raw_job_id: int
    task_id: str
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_currency: Optional[str] = None
    pinecone_id: Optional[str] = None
    embedding_status: str = "PENDING"
    processed_at: Optional[datetime] = None

class TaskLog(BaseModel):
    id: Optional[int] = None
    task_id: int
    log_level: str
    message: str
    created_at: Optional[datetime] = None

# Response Models
class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: Optional[str] = None

class JobProcessingResponse(BaseModel):
    task_id: str
    processed_count: int
    failed_count: int = 0
    status: str = "completed"
    error: Optional[str] = None

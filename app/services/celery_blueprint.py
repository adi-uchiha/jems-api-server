from celery import Celery
import ssl
import certifi
from app.core.config import settings
from app.db.connection import init_connection_pool
from celery.signals import worker_ready


# Configure Celery client
celery_app = Celery('celery_worker',
             broker=settings.celery_broker_url,
             backend=settings.celery_result_backend_url)

# Basic configuration to connect to the celery broker
celery_app.conf.update(
    broker_use_ssl={
        'ssl_cert_reqs': ssl.CERT_REQUIRED,
        'ssl_ca_certs': certifi.where(),
    },
    redis_backend_use_ssl={
        'ssl_cert_reqs': ssl.CERT_REQUIRED,
        'ssl_ca_certs': certifi.where(),
    },
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_track_started=True,
    task_ignore_result=False,
    result_expires=3600,
    task_default_queue=settings.REDIS_TASKS_QUEUE,
    broker_connection_retry_on_startup=True,
)
@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    try:
        init_connection_pool()
        print("✅ Database connection pool initialized")
    except Exception as e:
        print(f"❌ Failed to initialize database connection pool: {e}")
        raise
    
# Update task reference to match worker's task name
process_task = celery_app.signature('tasks.process_job_task')
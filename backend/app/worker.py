from celery import Celery
from backend.app.core.config import settings

celery_app = Celery(
    "lead_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[],  # task modules added here as we build them
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # one task at a time per worker — good for LLM calls
)




from celery import Celery
from backend.app.core.config import settings

celery_app = Celery(
    "lead_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["backend.app.tasks.lead_tasks"],  # register our tasks
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Retry policy for the whole broker connection
    broker_connection_retry_on_startup=True,
    # Result expiry — keep task results for 24 hours
    result_expires=86400,
)

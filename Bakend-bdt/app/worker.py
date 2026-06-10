"""Minimal Celery configuration for La Brújula del Trader."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "brujula",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Bogota",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks from these modules
celery_app.autodiscover_tasks([
    "app.modules.reports.tasks",
    "app.modules.ai_engine.tasks",
])

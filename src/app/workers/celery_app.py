import os

from celery import Celery

celery_app = Celery(
    "afm_lbl",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
    include=["app.workers.tasks"],
)
celery_app.conf.task_acks_late = True
celery_app.conf.task_default_retry_delay = 30
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]

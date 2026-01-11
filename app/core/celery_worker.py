from celery import Celery
import time
# import app.tasks.email


from app.core.config import settings


celery_app = Celery(
    "loan_api",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.email", "app.tasks.debit"],
)




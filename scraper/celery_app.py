from celery import Celery
import os

redis_url = f"rediss://:{os.environ['REDIS_PASSWORD']}@{os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}/0?ssl_cert_reqs=none"

app = Celery(
    'scraper',
    broker=redis_url,
    backend=redis_url,
    include=['scraper.tasks']  # ✅ Make sure this matches your repo structure
)

app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    worker_concurrency=2,
    worker_prefetch_multiplier=1,
)


from celery import Celery
import os

redis_url = f"rediss://:{os.environ['REDIS_PASSWORD']}@{os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}/0?ssl_cert_reqs=none"

app = Celery(
    'scraper',
    broker=redis_url,
    backend=redis_url,
    include=['scraper.tasks']
)

app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    worker_concurrency=8,
    worker_prefetch_multiplier=4,
    broker_connection_retry_on_startup=True,
    task_time_limit=600,
    task_soft_time_limit=300,
    broker_pool_limit=None,
    broker_heartbeat=60,
    broker_heartbeat_checkrate=2
)

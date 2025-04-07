
from celery import Celery
import os

redis_host = os.environ.get('REDIS_HOST', '0.0.0.0')
redis_port = os.environ.get('REDIS_PORT', '6379')
redis_password = os.environ.get('REDIS_PASSWORD', '')

redis_url = f"rediss://:{redis_password}@{redis_host}:{redis_port}/0?ssl_cert_reqs=none"

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
    worker_concurrency=2,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    broker_host='0.0.0.0',
    broker_port=5000
)

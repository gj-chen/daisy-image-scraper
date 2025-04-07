
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
    worker_concurrency=8,  # Increased worker processes
    worker_prefetch_multiplier=4,  # Increased task prefetching
    task_time_limit=300,
    broker_transport_options={
        'visibility_timeout': 300,
        'socket_timeout': 10,
        'socket_connect_timeout': 10,
        'retry_on_timeout': True
    },
    broker_connection_max_retries=3,
    broker_connection_timeout=10,
    broker_pool_limit=None,  # Allow unlimited connections
    broker_connection_retry_on_startup=True,
    broker_host=redis_host,
    broker_port=redis_port,
    worker_max_tasks_per_child=200,  # Prevent memory leaks
    worker_max_memory_per_child=150000  # 150MB memory limit per worker
)

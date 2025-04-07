
from scraper.celery_app import app
import scraper.tasks  # ✅ Force-load task definitions
import uuid
import socket

if __name__ == '__main__':
    # Generate unique worker name using UUID and hostname
    unique_id = str(uuid.uuid4())[:8]
    hostname = socket.gethostname()
    worker_name = f"celery@worker-{unique_id}-{hostname}"
    
    app.worker_main(argv=[
        "worker",
        f"-n={worker_name}",
        "--loglevel=info",
        "--concurrency=4"
    ])

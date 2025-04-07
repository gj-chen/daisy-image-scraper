
from scraper.celery_app import app
import scraper.tasks  # ✅ Force-load task definitions
import uuid

if __name__ == '__main__':
    # Generate unique worker name
    worker_name = f"worker-{uuid.uuid4()}"
    app.worker_main(argv=["worker", f"--hostname={worker_name}", "--loglevel=info", "--concurrency=4"])

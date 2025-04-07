
from scraper.celery_app import app
import scraper.tasks  # ✅ Force-load task definitions

if __name__ == '__main__':
    app.worker_main(argv=["worker", "--loglevel=info"])

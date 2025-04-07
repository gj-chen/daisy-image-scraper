from scraper.celery_app import app
import scraper.tasks  # ✅ Required for registration
from scraper.tasks import scrape_page
import time

if __name__ == '__main__':
    seed_url = "https://sheerluxe.com/fashion"
    scrape_page.delay(seed_url)  # Dispatch the scraping task
    print(f"[DISPATCHED] {seed_url}")
    time.sleep(2)  # Allow time for the task to be registered
    app.worker_main(argv=["worker", "--loglevel=info"])  # Start the Celery worker
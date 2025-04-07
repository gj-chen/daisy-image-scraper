# run_once.py
from scraper.tasks import scrape_page
from scraper.celery_app import app

import time

if __name__ == '__main__':
    seed_url = "https://sheerluxe.com/fashion"
    scrape_page.delay(seed_url)
    print(f"[DISPATCHED] {seed_url}")
    time.sleep(2)

    app.worker_main(argv=["worker", "--loglevel=info"])
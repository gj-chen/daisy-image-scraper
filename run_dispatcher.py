import os
import time
import redis
from scraper.tasks import scrape_page

redis_client = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=os.environ["REDIS_PORT"],
    password=os.environ["REDIS_PASSWORD"],
    ssl=True,
    decode_responses=True
)

SEED_URL = os.environ.get("SCRAPER_SEED_URL", "https://sheerluxe.com/fashion")

def wait_for_celery():
    print("[DISPATCHER] Waiting for workers to become ready...")
    max_attempts = 10
    for attempt in range(max_attempts):
        active_workers = redis_client.smembers("celery@workers")
        if active_workers:
            print(f"[DISPATCHER] Found workers: {active_workers}")
            return True
        time.sleep(2)
    print("[DISPATCHER] ⚠️ No workers found. Dispatching anyway...")
    return False

def main():
    print("[DISPATCHER] Starting dispatcher script...")
    wait_for_celery()
    print(f"[SEED] Initial seed URL: {SEED_URL}")
    scrape_page.delay(SEED_URL)
    print(f"[DISPATCH] ✨ Successfully seeded: {SEED_URL}")

if __name__ == "__main__":
    main()

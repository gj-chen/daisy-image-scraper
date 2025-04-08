import os
import time
import redis
from scraper.tasks import scrape_page

# Redis setup (same as in your workers)
redis_client = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=os.environ["REDIS_PORT"],
    password=os.environ["REDIS_PASSWORD"],
    ssl=True,
    decode_responses=True
)

SEED_URL = os.environ.get("SCRAPER_SEED_URL", "https://sheerluxe.com/fashion")

def wait_for_celery():
    print("[DISPATCHER] Waiting for Celery workers to become ready...")
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            clients = redis_client.info("clients")
            connected = clients.get("connected_clients", 0)
            print(f"[DISPATCHER] Redis connected clients: {connected}")
            if connected > 1:  # 1 = just this script, >1 = worker(s) + this
                print("[DISPATCHER] ✅ Celery worker(s) detected!")
                return
        except Exception as e:
            print(f"[DISPATCHER] Redis check failed: {e}")
        time.sleep(2)
    print("[DISPATCHER] ⚠️ No workers detected after waiting. Dispatching anyway...")

def main():
    print("[DISPATCHER] 🚀 Starting dispatcher script")
    wait_for_celery()
    print(f"[SEED] Initial seed URL: {SEED_URL}")
    scrape_page.delay(SEED_URL)
    print(f"[DISPATCH] ✨ Successfully seeded: {SEED_URL}")

if __name__ == "__main__":
    main()

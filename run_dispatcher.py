import os
import time
import redis
from scraper.tasks import scrape_page

# Redis setup
redis_client = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=int(os.environ["REDIS_PORT"]),
    password=os.environ["REDIS_PASSWORD"],
    ssl=True,
    decode_responses=True
)

# List of seed URLs to dispatch
SEED_URLS = [
    "https://slman.com/style",
    "https://sheerluxe.com/luxegen/fashion",
    "https://sheerluxe.com/gold/fashion",
    "https://sheerluxe.com/weddings"
]

def wait_for_celery():
    print("[DISPATCHER] Waiting for Celery workers to become ready...")
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            clients = redis_client.info("clients")
            connected = clients.get("connected_clients", 0)
            print(f"[DISPATCHER] Redis connected clients: {connected}")
            if connected > 1:
                print("[DISPATCHER] ✅ Celery worker(s) detected!")
                return
        except Exception as e:
            print(f"[DISPATCHER] Redis check failed: {e}")
        time.sleep(2)
    print("[DISPATCHER] ⚠️ No workers detected after waiting. Dispatching anyway...")

def main():
    print("[DISPATCHER] 🚀 Starting dispatcher script")
    wait_for_celery()

    for url in SEED_URLS:
        print(f"[SEED] Dispatching URL: {url}")

        # Optional: for manual visibility (DO NOT mark as processed)
        redis_client.lpush("url_queue", url)

        # ✅ Let scrape_page handle deduping, not here
        scrape_page.delay(url)

    print(f"[DISPATCH] ✨ Successfully seeded {len(SEED_URLS)} URLs")

if __name__ == "__main__":
    main()

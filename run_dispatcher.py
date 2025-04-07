import os
import time
import redis
from scraper.tasks import scrape_page

# Redis setup (matches your worker)
redis_client = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=os.environ["REDIS_PORT"],
    password=os.environ["REDIS_PASSWORD"],
    ssl=True,
    decode_responses=True
)

SEED_URL = os.environ.get("SCRAPER_SEED_URL", "https://sheerluxe.com/fashion")
CHECK_INTERVAL = 15  # seconds between checks
MAX_WAIT_BEFORE_RESEED = 60  # reseed if nothing processed after this many seconds

def main():
    print(f"[SEED] Initial seed URL: {SEED_URL}")
    scrape_page.delay(SEED_URL)
    print(f"[DISPATCH] ✨ Successfully seeded first URL: {SEED_URL}")

    last_processed_count = 0
    last_check_time = time.time()

    while True:
        time.sleep(CHECK_INTERVAL)

        current_urls = redis_client.scard("processed_urls")
        current_images = redis_client.scard("processed_images")

        print(f"[STATUS] Processed URLs: {current_urls}, Images: {current_images}")

        # If no URLs have been processed in a while → reseed
        if current_urls == 0 and (time.time() - last_check_time) > MAX_WAIT_BEFORE_RESEED:
            print("[REDISPATCH] No URLs processed, reseeding...")
            scrape_page.delay(SEED_URL)
            last_check_time = time.time()
        elif current_urls > last_processed_count:
            last_processed_count = current_urls
            last_check_time = time.time()

if __name__ == "__main__":
    main()

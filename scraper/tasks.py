import os
import time
import redis
from celery import shared_task
from .celery_app import app
from .utils import fetch_and_extract_urls_and_images, download_image_file
from .openai_client import generate_gpt_structured_metadata_sync
from .supabase_client import upload_image_to_supabase, store_analysis_result
from scraper.openai_client import is_meaningful_metadata
from scraper.openai_client import (
    summarize_metadata_for_embedding,
    generate_embedding_from_text
)
import os

redis_client = redis.Redis.from_url(
    f"rediss://:{os.environ['REDIS_PASSWORD']}@{os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}/0?ssl_cert_reqs=none",
    decode_responses=True
)

@app.task(bind=True, default_retry_delay=180, max_retries=3)
def process_image(self, image_url):
    if redis_client.sadd('processed_images', image_url) == 0:
        print(f"[SKIP] Already processed image: {image_url}")
        return

    try:
        print(f"[IMAGE] Processing: {image_url}")

        ext = os.path.splitext(image_url.split("?")[0])[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            print(f"[SKIP] Unsupported image format: {image_url}")
            return

        image_bytes = download_image_file(image_url)
        if not image_bytes:
            print(f"[SKIP] Could not download: {image_url}")
            return

        image_context = {
            "image_url": image_url,
            "alt_text": "",
            "title": "",
            "surrounding_text": "",
            "source_url": "https://sheerluxe.com/fashion"  # placeholder, update later
        }

        metadata = generate_gpt_structured_metadata_sync(image_context, image_bytes)
        if not metadata or not is_meaningful_metadata(metadata):
            print(f"[SKIP] No meaningful metadata for: {image_url}")
            return

        summary = summarize_metadata_for_embedding(metadata)
        embedding = generate_embedding_from_text(summary)

        stored_image_url = upload_image_to_supabase(image_url, image_bytes)

        if not stored_image_url:
            print(f"[SKIP] Failed to upload image to Supabase: {image_url}")
            return

        store_analysis_result(
            image_url=image_url,
            metadata=metadata,
            embedding=embedding,
            stored_image_url=stored_image_url,
            source_url=image_context["source_url"],
            title=image_context["title"],
            description=image_context["surrounding_text"]
        )

        redis_client.sadd('processed_images', image_url)
        print(f"[✅ STORED] {image_url}")

    except Exception as e:
        print(f"[ERROR] process_image failed on {image_url}: {e}")
        self.retry(exc=e)


@app.task(bind=True, default_retry_delay=180, max_retries=3)
def scrape_page(self, url):
    print(f"[SCRAPE] 👀 Running scrape_page for: {url}")

    from scraper.utils import fetch_and_extract_urls_and_images
    from scraper.tasks import process_image

    ALLOWED_SEED_PREFIXES = [
        "https://slman.com/style",
        "https://sheerluxe.com/luxegen/fashion",
        "https://sheerluxe.com/gold/fashion",
        "https://sheerluxe.com/weddings"
    ]

    try:
        # ✅ Only mark as processed inside this task
        if redis_client.sadd("processed_urls", url) == 0:
            print(f"[SKIP] Already processed: {url}")
            return

        print(f"[SCRAPE] Fetching: {url}")
        urls, images = fetch_and_extract_urls_and_images(url)
        print(f"[PARSE] Found {len(urls)} links and {len(images)} images")

        for next_url in urls:
            ALLOWED_SEED_PREFIXES = [
                "https://slman.com/style",
                "https://sheerluxe.com/luxegen/fashion",
                "https://sheerluxe.com/gold/fashion",
                "https://sheerluxe.com/weddings"
            ]

            def is_allowed_child_url(url):
                return any(url.startswith(prefix) for prefix in ALLOWED_SEED_PREFIXES)

            for next_url in urls:
                if not is_allowed_child_url(next_url):
                    continue
                if redis_client.sadd("processed_urls", next_url) == 0:
                    print(f"[DUPLICATE] Skipping already seen URL: {next_url}")
                    continue
                print(f"[ENQUEUE] scrape_page → {next_url}")
                scrape_page.delay(next_url)

            
            if redis_client.sadd("processed_urls", next_url) == 0:
                print(f"[DUPLICATE] Skipping already seen URL: {next_url}")
                continue
            print(f"[ENQUEUE] scrape_page → {next_url}")
            scrape_page.delay(next_url)

        for image_url in images:
            if "sheerluxe.com" not in image_url and "slman.com" not in image_url:
                continue
            if redis_client.sadd("processed_images", image_url) == 0:
                print(f"[DUPLICATE] Skipping already seen image: {image_url}")
                continue
            print(f"[ENQUEUE] process_image → {image_url}")
            process_image.delay(image_url)

    except Exception as e:
        print(f"[ERROR] ❌ scrape_page failed for {url}: {e}")
        self.retry(exc=e)



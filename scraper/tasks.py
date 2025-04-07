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
    f"rediss://:{os.environ.get('REDIS_PASSWORD', '')}@{os.environ.get('REDIS_HOST', '0.0.0.0')}:{os.environ.get('REDIS_PORT', '6379')}/0?ssl_cert_reqs=none",
    decode_responses=True
)

@app.task(bind=True, default_retry_delay=180, max_retries=3)
def process_image(self, image_url):
    if redis_client.sismember('processed_images', image_url):
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
            return  # ✅ Avoid saving incomplete rows

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




@shared_task(bind=True, default_retry_delay=180, max_retries=3)
def scrape_page(self, url):
    if not url.startswith("https://sheerluxe.com/fashion"):
        print(f"[SKIP] Not a fashion URL: {url}")
        return

    if redis_client.sismember('processed_urls', url):
        print(f"[SKIP] Already processed: {url}")
        return

    try:
        print(f"[SCRAPE] Fetching: {url}")
        urls, images = fetch_and_extract_urls_and_images(url)

        redis_client.sadd('processed_urls', url)
        time.sleep(1)  # Rate limiting

        for next_url in urls:
            if not next_url.startswith("https://sheerluxe.com/fashion"):
                continue
            if redis_client.sismember('processed_urls', next_url):
                continue
            scrape_page.delay(next_url)

        for image_url in images:
            if "sheerluxe.com" not in image_url:
                continue
            if redis_client.sismember('processed_images', image_url):
                continue
            process_image.delay(image_url)

    except Exception as e:
        print(f"[ERROR] scrape_page failed on {url}: {e}")
        self.retry(exc=e)
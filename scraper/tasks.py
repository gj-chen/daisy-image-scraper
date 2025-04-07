
from .celery_app import app
from .utils import fetch_and_extract_urls_and_images, download_image_file
from .openai_client import analyze_image_with_openai
from .supabase_client import upload_image_to_supabase, store_analysis_result
import redis
import os

redis_client = redis.Redis.from_url(
    f"rediss://:{os.environ['REDIS_PASSWORD']}@{os.environ['REDIS_HOST']}:{os.environ['REDIS_PORT']}/0?ssl_cert_reqs=none",
    decode_responses=True
)

@app.task(bind=True, default_retry_delay=180, max_retries=3)
def process_image(self, image_url):
    try:
        image_data = download_image_file(image_url)
        if not image_data:
            return

        storage_url = upload_image_to_supabase(image_data)
        if not storage_url:
            return

        analysis = analyze_image_with_openai({
            "image_url": image_url,
            "alt_text": "",
            "title": "",
            "surrounding_text": ""
        })
        if not analysis:
            return

        store_analysis_result(analysis, storage_url, image_url)

    except Exception as e:
        print(f"[ERROR] process_image failed on {image_url}: {e}")
        self.retry(exc=e)

@app.task(bind=True, default_retry_delay=180, max_retries=3)
def scrape_page(self, url):
    if redis_client.sadd('processed_urls', url) == 0:
        print(f"[SKIP] URL already processed: {url}")
        return

    if not url.startswith("https://sheerluxe.com/fashion"):
        print(f"[SKIP] Non-fashion page: {url}")
        return

    try:
        print(f"[SCRAPE] Fetching: {url}")
        urls, images = fetch_and_extract_urls_and_images(url)

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

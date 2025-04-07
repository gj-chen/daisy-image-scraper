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

@app.task(bind=True)
def scrape_page(self, url):
    if redis_client.sadd('processed_urls', url) == 0:
        print(f"[SKIP] URL already processed: {url}")
        return

    try:
        urls, images = fetch_and_extract_urls_and_images(url)

        for next_url in urls:
            scrape_page.delay(next_url)

        for image_url in images:
            process_image.delay(image_url)

    except Exception as e:
        print(f"[ERROR] scrape_page failed on {url}: {e}")
        self.retry(exc=e)

        @app.task(bind=True)
        def process_image(self, image_url):
            if redis_client.sadd('processed_images', image_url) == 0:
                print(f"[SKIP] Image already processed: {image_url}")
                return

            try:
                image_bytes = download_image_file(image_url)
                if not image_bytes:
                    print(f"[SKIP] Could not download: {image_url}")
                    return

                image_context = {
                    "image_url": image_url,
                    "alt_text": "",
                    "title": "",
                    "surrounding_text": ""
                }

                analysis = analyze_image_with_openai(image_context)

                if not analysis or analysis.strip() == "":
                    print(f"[SKIP] No meaningful metadata for: {image_url}")
                    return

                upload_image_to_supabase(image_url, image_bytes)
                store_analysis_result(image_url, analysis)

            except Exception as e:
                print(f"[ERROR] process_image failed on {image_url}: {e}")
                self.retry(exc=e)


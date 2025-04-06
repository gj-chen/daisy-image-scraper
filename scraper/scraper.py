import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils.openai_utils import generate_gpt_structured_metadata_sync
from utils.db_utils import generate_embedding_sync, insert_metadata_to_supabase_sync, prepare_metadata_record
import logging

logger = logging.getLogger(__name__)

def scrape_page(url):
    logger.info(f"Scraping URL: {url}")
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    images = soup.find_all("img")
    inserted_images = []

    for img in images:
        raw_src = img.get("src")
        if not raw_src:
            logger.warning("Image without src skipped.")
            continue

        image_url = urljoin(url, raw_src)
        context = {
            "image_url": image_url,
            "alt_text": img.get("alt", ""),
            "title": soup.title.string if soup.title else "",
            "surrounding_text": img.parent.get_text(strip=True) if img.parent else ""
        }

        metadata = generate_gpt_structured_metadata_sync(context)
        if not metadata:
            logger.error(f"GPT metadata generation failed for {image_url}")
            continue

        embedding = generate_embedding_sync(metadata)
        if not embedding:
            logger.error(f"Embedding generation failed for {image_url}")
            continue

        record = prepare_metadata_record(
            image_url=image_url,
            source_url=url,
            title=context['title'],
            description=context['alt_text'],
            structured_metadata=metadata,
            embedding=embedding
        )

        try:
            insert_metadata_to_supabase_sync([record])
            inserted_images.append(image_url)
            logger.info(f"Inserted {image_url} successfully.")
        except Exception as e:
            logger.error(f"Supabase insertion failed for {image_url}: {str(e)}")

    logger.info(f"Scraping finished. {len(inserted_images)} images inserted.")
    return inserted_images

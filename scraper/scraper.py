import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils.openai_utils import generate_gpt_structured_metadata_sync
from utils.db_utils import insert_metadata_to_supabase_sync, generate_embedding_sync, prepare_metadata_record
import logging

logger = logging.getLogger(__name__)

def scrape_page(url):
    logger.info(f"Starting scrape for: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    images = soup.find_all("img")
    inserted_images = []

    for img in images:
        raw_src = img.get("src")
        if not raw_src:
            logger.warning("Image without src encountered, skipping.")
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
            logger.error(f"GPT metadata failed for image: {image_url}")
            continue
        logger.info(f"GPT metadata succeeded for image: {image_url}")

        embedding = generate_embedding_sync(metadata)
        if not embedding:
            logger.error(f"Embedding failed for image: {image_url}")
            continue
        logger.info(f"Embedding succeeded for image: {image_url}")

        data_record = prepare_metadata_record(
            image_url=image_url,
            source_url=url,
            title=context['title'],
            description=context['alt_text'],
            structured_metadata=metadata,
            embedding=embedding
        )

        insert_metadata_to_supabase_sync([data_record])
        inserted_images.append(image_url)
        logger.info(f"Inserted successfully: {image_url}")

    logger.info(f"Scraping complete. Total inserted: {len(inserted_images)}")
    return inserted_images

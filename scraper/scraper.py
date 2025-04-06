import requests
from bs4 import BeautifulSoup
from utils.openai_utils import generate_gpt_structured_metadata
from utils.db_utils import insert_metadata_to_supabase, generate_embedding
import logging

logger = logging.getLogger(__name__)

class SheerLuxeScraper:
    def scrape_page(self, url):
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        images = soup.find_all("img")

        inserted_images = []

        for img in images:
            image_url = img.get("src")
            if not image_url:
                logger.warning("Image without src encountered, skipping.")
                continue

            context = {
                "image_url": image_url,
                "alt_text": img.get("alt", ""),
                "title": soup.title.string if soup.title else "",
                "surrounding_text": img.parent.get_text(strip=True) if img.parent else ""
            }

            structured_metadata = generate_gpt_structured_metadata(context)
            if structured_metadata is None:
                logger.error(f"Skipping image due to GPT failure: {image_url}")
                continue

            embedding = generate_embedding(structured_metadata)

            data_record = {
                "image_url": image_url,
                "metadata": structured_metadata,
                "embedding": embedding
            }

            insert_metadata_to_supabase([data_record])
            logger.info(f"Inserted metadata incrementally for image: {image_url}")
            inserted_images.append(image_url)

        logger.info(f"Scraping complete for URL: {url}. Total images inserted: {len(inserted_images)}")
        return inserted_images
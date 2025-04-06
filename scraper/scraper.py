import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from time import sleep
import logging
from typing import List, Optional
import os
import openai
from utils.openai_utils import generate_gpt_structured_metadata_sync
from utils.db_utils import generate_embedding_sync, insert_metadata_to_supabase_sync, prepare_metadata_record

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

logger = logging.getLogger(__name__)

from typing import List, Optional
from config import MAX_RETRIES, SHEERLUXE_COOKIE
from .exceptions import ScrapingError

def scrape_page(url: str, max_retries: int = MAX_RETRIES) -> List[str]:
    """
    Scrapes images from a given URL with retry logic

    Args:
        url: The URL to scrape
        max_retries: Number of retry attempts

    Returns:
        List of scraped image URLs

    Raises:
        ScrapingError: If scraping fails after all retries
    """
    logger.info(f"Scraping URL: {url}")
    logger.info(f"Using headers with cookies: {SHEERLUXE_COOKIE}")

    for attempt in range(max_retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            resp = requests.get(url, timeout=60, headers=headers)
            resp.raise_for_status()
            break
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise ScrapingError(f"Failed to scrape after {max_retries} attempts: {str(e)}")
            logger.warning(f"Retry {attempt + 1}/{max_retries} after error: {str(e)}")
            sleep(2 ** attempt)  # Exponential backoff

    soup = BeautifulSoup(resp.text, "html.parser")
    images = soup.find_all("img")
    inserted_images = []

    from time import sleep

    for img in images:
        sleep(1)  # Rate limiting
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

        try:
            metadata = generate_gpt_structured_metadata_sync(context)
            if not metadata:
                logger.error(f"GPT metadata generation failed for {image_url}")
                continue
        except Exception as e:
            logger.error(f"Failed to generate metadata for {image_url}: {str(e)}")
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
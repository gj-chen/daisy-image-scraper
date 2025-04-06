import asyncio
import httpx
from bs4 import BeautifulSoup
from utils.openai_utils import generate_gpt_structured_metadata_async
from utils.db_utils import insert_metadata_to_supabase_async, generate_embedding_async, prepare_metadata_record
import logging

logger = logging.getLogger(__name__)

async def fetch_page(client, url):
    resp = await client.get(url, timeout=20)
    resp.raise_for_status()
    return resp.text

async def process_image(client, img, page_title, source_url):
    image_url = img.get("src")
    if not image_url:
        logger.warning("Image without src encountered, skipping.")
        return None

    context = {
        "image_url": image_url,
        "alt_text": img.get("alt", ""),
        "title": page_title,
        "surrounding_text": img.parent.get_text(strip=True) if img.parent else ""
    }

    structured_metadata = await generate_gpt_structured_metadata_async(context)
    if structured_metadata is None:
        logger.error(f"Skipping image due to GPT failure: {image_url}")
        return None

    embedding = await generate_embedding_async(structured_metadata)

    return prepare_metadata_record(
        image_url=image_url,
        source_url=source_url,
        title=context['title'],
        description=context['alt_text'],
        structured_metadata=structured_metadata,
        embedding=embedding
    )

async def scrape_page(url):
    async with httpx.AsyncClient() as client:
        html = await fetch_page(client, url)
        soup = BeautifulSoup(html, "html.parser")
        images = soup.find_all("img")
        tasks = [process_image(client, img, soup.title.string if soup.title else "", url) for img in images]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter successful results
        successful_records = [r for r in results if isinstance(r, dict)]
        if successful_records:
            await insert_metadata_to_supabase_async(successful_records)
            logger.info(f"Inserted {len(successful_records)} records from {url}")

        failures = [r for r in results if r is None or isinstance(r, Exception)]
        if failures:
            logger.warning(f"{len(failures)} images failed processing from {url}")

        return successful_records

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
from typing import List, Optional, Set
import os
from datetime import datetime, timedelta
import re
from .url_frontier import URLFrontier
from config import SCRAPER_CONCURRENCY_LIMIT
from utils.openai_utils import generate_gpt_structured_metadata_sync
from utils.db_utils import generate_embedding_sync, insert_metadata_to_supabase_sync, prepare_metadata_record

logger = logging.getLogger(__name__)

class AsyncScraper:
    def __init__(self, concurrency_limit: int = SCRAPER_CONCURRENCY_LIMIT):
        self.frontier = URLFrontier()
        self.sem = asyncio.Semaphore(concurrency_limit)
        self.session = None
        # Cache existing items
        from utils.db_utils import get_existing_urls_and_images
        self.existing_urls, self.existing_images = get_existing_urls_and_images()

    async def init_session(self):
        if not self.session:
            from utils.auth_utils import AuthSession
            auth = AuthSession()
            self.session = await auth.create_session()

    async def close(self):
        if self.session:
            await self.session.close()

    async def process_url(self, url: str, depth: int) -> List[str]:
        async with self.sem:
            try:
                async with self.session.get(url, timeout=30) as response:
                    if response.status == 403 or response.status == 401:
                        logger.error(f"Authentication required for {url}. Please check your SHEERLUXE_COOKIE environment variable.")
                        raise ScrapingError("Authentication failed - invalid or expired cookie")
                    elif response.status != 200:
                        return []

                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Extract links for crawling
                    links = soup.find_all("a", href=True)
                    for link in links:
                        new_url = urljoin(url, link["href"])
                        if ("sheerluxe.com" in new_url and 
                            self.frontier.is_valid_date(new_url) and 
                            new_url not in self.frontier.visited):
                            self.frontier.add_url(new_url, depth + 1)

                    # Process images
                    images = soup.find_all("img")
                    inserted_images = []

                    for img in images:
                        raw_src = img.get("src")
                        if not raw_src:
                            continue

                        image_url = urljoin(url, raw_src)
                        if image_url in self.existing_images:
                            continue


                        context = {
                            "image_url": image_url,
                            "alt_text": img.get("alt", ""),
                            "title": soup.title.string if soup.title else "",
                            "surrounding_text": img.parent.get_text(strip=True) if img.parent else ""
                        }

                        try:
                            metadata = generate_gpt_structured_metadata_sync(context)
                            if not metadata:
                                continue

                            embedding = generate_embedding_sync(metadata)
                            if not embedding:
                                continue

                            from utils.storage_utils import store_image
                            stored_image_url = store_image(image_url)
                            if not stored_image_url:
                                continue

                            metadata = generate_gpt_structured_metadata_sync(context)
                            if not metadata:
                                continue

                            embedding = generate_embedding_sync(metadata)
                            if not embedding:
                                continue
                            if stored_image_url:
                                record = prepare_metadata_record(
                                    image_url=image_url,
                                    source_url=url,
                                    title=context['title'],
                                    description=context['alt_text'],
                                    structured_metadata=metadata,
                                    embedding=embedding,
                                    stored_image_url=stored_image_url
                                )
                                insert_metadata_to_supabase_sync([record])
                                inserted_images.append(image_url)
                        except Exception as e:
                            logger.error(f"Failed processing image {image_url}: {str(e)}")
                            continue

                    return inserted_images

            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                return []

    async def crawl(self, seed_url: str) -> List[str]:
        await self.init_session()
        self.frontier.add_url(seed_url)
        all_processed_images = []
        pending_tasks = []

        async def process_url_batch():
            urls_to_process = []
            while self.frontier.has_urls and len(urls_to_process) < URL_BATCH_SIZE:
                url, depth = self.frontier.get_next_url()
                if url not in self.frontier.visited:
                    urls_to_process.append((url, depth))

            if urls_to_process:
                tasks = [self.process_url(url, depth) for url, depth in urls_to_process]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for url, result in zip([u for u, _ in urls_to_process], results):
                    if isinstance(result, list):
                        all_processed_images.extend(result)
                    self.frontier.mark_visited(url)

        try:
            while True:  # Run continuously
                if not self.frontier.has_urls:
                    logger.info("No URLs in frontier, waiting for new URLs...")
                    await asyncio.sleep(60)  # Wait before checking again
                    continue
                
                tasks = []
                for _ in range(min(5, self.frontier.url_count)):  # Process up to 5 URLs concurrently
                    if not self.frontier.has_urls:
                        break
                    current_url, depth = self.frontier.get_next_url()
                    if current_url not in self.frontier.visited:
                        tasks.append(self.process_url(current_url, depth))
                
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, list):
                            all_processed_images.extend(result)
                    
                    await asyncio.sleep(1)  # Rate limiting between batches

        except asyncio.CancelledError:
            logger.info("Crawling cancelled")
        finally:
            await self.close()

        return all_processed_images

def scrape_page(url: str) -> List[str]:
    scraper = AsyncScraper()
    return asyncio.run(scraper.crawl(url))
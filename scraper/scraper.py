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
                        if "sheerluxe.com" in new_url and self.frontier.is_valid_date(new_url):
                            self.frontier.add_url(new_url, depth + 1)

                    # Process images
                    images = soup.find_all("img")
                    inserted_images = []

                    for img in images:
                        raw_src = img.get("src")
                        if not raw_src:
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
                                continue

                            embedding = generate_embedding_sync(metadata)
                            if not embedding:
                                continue

                            record = prepare_metadata_record(
                                image_url=image_url,
                                source_url=url,
                                title=context['title'],
                                description=context['alt_text'],
                                structured_metadata=metadata,
                                embedding=embedding
                            )

                            insert_metadata_to_supabase_sync([record])
                            inserted_images.append(image_url)
                            logger.info(f"Processed image: {image_url}")

                        except Exception as e:
                            logger.error(f"Failed processing image {image_url}: {str(e)}")

                    return inserted_images

            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                return []

    async def crawl(self, seed_url: str) -> List[str]:
        await self.init_session()
        self.frontier.add_url(seed_url)
        all_processed_images = []

        try:
            while self.frontier.has_urls:
                current_url, depth = self.frontier.get_next_url()
                if current_url in self.frontier.visited:
                    continue

                processed_images = await self.process_url(current_url, depth)
                all_processed_images.extend(processed_images)
                self.frontier.mark_visited(current_url)

                await asyncio.sleep(1)  # Rate limiting

        finally:
            await self.close()

        return all_processed_images

def scrape_page(url: str) -> List[str]:
    scraper = AsyncScraper()
    return asyncio.run(scraper.crawl(url))
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
from config import SCRAPER_CONCURRENCY_LIMIT, SCRAPER_SEED_URLS, FASHION_SUBCATEGORIES, URL_BATCH_SIZE, SCRAPER_MAX_AGE_YEARS
from utils.openai_utils import generate_gpt_structured_metadata_sync
from utils.db_utils import generate_embedding_sync, insert_metadata_to_supabase_sync, prepare_metadata_record

logger = logging.getLogger(__name__)

class AsyncScraper:
    def __init__(self, concurrency_limit: int = SCRAPER_CONCURRENCY_LIMIT):
        self.frontier = URLFrontier()
        self.sem = asyncio.Semaphore(concurrency_limit)
        self.session = None
        self.url_cache = {}  # Cache URL responses
        self.processing_tasks = set()  # Track active tasks
        # Cache existing items
        from utils.db_utils import get_existing_urls_and_images
        self.existing_urls, self.existing_images = get_existing_urls_and_images()

    async def init_session(self):
        if not self.session:
            from utils.auth_utils import AuthSession
            auth = AuthSession()
            self.session = await auth.create_session()

    async def process_single_image(self, img, image_url: str, source_url: str, context: dict):
        if image_url in self.existing_images:
            return None

        try:
            metadata = generate_gpt_structured_metadata_sync(context)
            if not metadata:
                logger.info(f"Skipping image {image_url} - empty metadata")
                return None

            embedding = generate_embedding_sync(metadata)
            if not embedding:
                return None

            from utils.storage_utils import store_image
            stored_image_url = store_image(image_url, self.existing_images)
            if not stored_image_url:
                return None

            return {
                "image_url": image_url,
                "source_url": source_url,
                "metadata": metadata,
                "embedding": embedding,
                "stored_url": stored_image_url,
                "context": context
            }
        except Exception as e:
            logger.error(f"Failed processing single image {image_url}: {str(e)}")
            return None

    async def close(self):
        if self.session:
            await self.session.close()

    async def process_url(self, url: str, depth: int) -> List[str]:
        if url in self.frontier.visited or url in self.frontier.pending:
            return []

        self.frontier.pending.add(url)
        async with self.sem:
            try:
                if not url.startswith(('http://', 'https://')):
                    url = f'https://{url}'

                # Single attempt, no retries
                async with self.session.get(url, timeout=10) as response:
                    if response.status != 200:
                        logger.info(f"Skipping failed URL {url} with status {response.status}")
                        self.frontier.mark_visited(url)  # Mark as visited to prevent retries
                        return []
                    if response.status == 403 or response.status == 401:
                        logger.error(f"Authentication required for {url}. Please check your SHEERLUXE_COOKIE environment variable.")
                        raise ScrapingError("Authentication failed - invalid or expired cookie")
                    elif response.status != 200:
                        return []

                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")

                    # Handle year archives
                    current_year = datetime.now().year
                    for year in range(current_year - SCRAPER_MAX_AGE_YEARS, current_year + 1):
                        archive_url = f"https://sheerluxe.com/fashion/archive/{year}"
                        if archive_url not in self.frontier.visited:
                            self.frontier.add_url(archive_url, depth + 1)
                            logger.info(f"Added archive URL: {archive_url}")

                    # Extract links for crawling
                    links = soup.find_all("a", href=True)
                    for link in links:
                        new_url = urljoin(url, link["href"])
                        if ("sheerluxe.com/fashion" in new_url and 
                            not new_url.endswith(('.jpg', '.jpeg', '.png', '.gif'))):
                            # Check pagination
                            if "?page=" in new_url:
                                page_num = int(new_url.split("page=")[1])
                                # Allow up to page 100 to ensure we get everything
                                if page_num <= 100:
                                    if new_url not in self.frontier.visited:
                                        self.frontier.add_url(new_url, depth + 1)
                                        logger.info(f"Added pagination URL: {new_url}")
                            # Handle regular URLs
                            elif new_url not in self.frontier.visited:
                                self.frontier.add_url(new_url, depth + 1)
                                logger.info(f"Added new URL to queue: {new_url}")

                    # Process images in larger batches
                    images = soup.find_all("img")
                    inserted_images = []
                    batch_records = []
                    batch_size = 5  # Process 5 images at a time

                    valid_images = [
                        (img, urljoin(url, img.get("src")))
                        for img in images
                        if img.get("src") and img.get("src").startswith(('http://', 'https://'))
                    ]

                    async def process_image_batch(batch):
                        tasks = []
                        for img, image_url in batch:
                            if image_url in self.existing_images:
                                continue
                            tasks.append(self.process_single_image(img, image_url, url, context))
                        return await asyncio.gather(*tasks, return_exceptions=True)

                    for i in range(0, len(valid_images), batch_size):
                        batch = valid_images[i:i + batch_size]

                        # Filter out existing images first
                        filtered_batch = [(img, image_url) for img, image_url in batch if image_url not in self.existing_images]
                        if not filtered_batch:
                            continue

                        # Create contexts for filtered batch
                        contexts = [
                            {
                                "image_url": image_url,
                                "alt_text": img.get("alt", ""),
                                "title": soup.title.string if soup.title else "",
                                "surrounding_text": img.parent.get_text(strip=True) if img.parent else ""
                            }
                            for img, image_url in filtered_batch
                        ]

                        # Process all images in parallel
                        tasks = [
                            self.process_single_image(img, image_url, url, context)
                            for (img, image_url), context in zip(filtered_batch, contexts)
                        ]
                        results = await asyncio.gather(*tasks)
                        results = [r for r in results if r]  # Filter out None results

                        # Process valid results
                        for result in results:
                            metadata = generate_gpt_structured_metadata_sync(result['context'])
                            if not metadata:
                                logger.info(f"Skipping image {result['image_url']} - empty metadata")
                                continue

                            # Recursive function to check if nested dict has any non-empty values
                            def has_content(d):
                                if isinstance(d, dict):
                                    return any(has_content(v) for v in d.values())
                                elif isinstance(d, list):
                                    return len(d) > 0
                                elif isinstance(d, str):
                                    return bool(d.strip())
                                return False

                            if not has_content(metadata):
                                logger.info(f"Skipping image {result['image_url']} - empty metadata content")
                                continue

                            embedding = generate_embedding_sync(metadata)
                            if not embedding:
                                continue

                            from utils.storage_utils import store_image
                            stored_image_url = store_image(result['image_url'], self.existing_images)
                            if not stored_image_url:
                                continue

                            record = prepare_metadata_record(
                                image_url=result['image_url'],
                                source_url=url,
                                title=result['context']['title'],
                                description=result['context']['alt_text'],
                                structured_metadata=metadata,
                                embedding=embedding,
                                stored_image_url=stored_image_url
                            )
                            batch_records.append(record)
                            inserted_images.append(result['image_url'])

                            if len(batch_records) >= batch_size:
                                insert_metadata_to_supabase_sync(batch_records)
                                batch_records = []

                        # Insert any remaining records
                        if batch_records:
                            try:
                                insert_metadata_to_supabase_sync(batch_records)
                            except Exception as e:
                                logger.error(f"Failed to insert batch: {str(e)}")
                            finally:
                                batch_records = []

                    return inserted_images

            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                return []

    async def crawl(self, seed_url: str, worker_id: int = None) -> List[str]:
        await self.init_session()
        self.frontier.add_url(seed_url)
        all_processed_images = []
        pending_tasks = []
        processed_count = 0
        
        worker_info = f"Worker {worker_id}: " if worker_id is not None else ""
        logger.info(f"{worker_info}Starting crawl from seed URL: {seed_url}")

        logger.info(f"Starting crawl from seed URL: {seed_url}")

        try:
            while True:  # Run continuously
                if not self.frontier.has_urls:
                    logger.info("No URLs in frontier, waiting for new URLs...")
                    await asyncio.sleep(10)  # Reduced wait time
                    continue

                # Get larger batch of URLs to process
                current_batch = []
                while len(current_batch) < 20 and self.frontier.has_urls:  # Increased batch size
                    url, depth = self.frontier.get_next_url()
                    if url not in self.frontier.visited and url not in [u for u, _ in current_batch]:
                        logger.info(f"Processing URL in batch: {url}")
                        current_batch.append((url, depth))

                if not current_batch:
                    if not self.frontier.has_urls:
                        logger.info("Completed processing all URLs in frontier")
                        break
                    continue

                # Process batch
                tasks = [self.process_url(url, depth) for url, depth in current_batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Mark URLs as visited only after processing
                for (url, _), result in zip(current_batch, results):
                    if isinstance(result, list):
                        all_processed_images.extend(result)
                    self.frontier.mark_visited(url)
                    logger.info(f"Completed processing URL: {url}")

                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, list):
                            all_processed_images.extend(result)

                    # Rate limiting between batches
                    await asyncio.sleep(60 / SCRAPER_RATE_LIMIT)  # Evenly space requests

        except asyncio.CancelledError:
            logger.info("Crawling cancelled")
        finally:
            await self.close()

        return all_processed_images

def scrape_page(url: str) -> List[str]:
    scraper = AsyncScraper()
    # Add the main URL and ensure it's properly formatted
    main_url = url if url.startswith(('http://', 'https://')) else f'https://{url}'
    scraper.frontier.add_url(main_url, depth=0)

    # Add fashion subcategory URLs
    for subcat in FASHION_SUBCATEGORIES:
        subcat_url = f"https://sheerluxe.com/fashion/{subcat}"
        scraper.frontier.add_url(subcat_url, depth=0)

    return asyncio.run(scraper.crawl(main_url))
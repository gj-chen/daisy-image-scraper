from scraper.scraper import scrape_page
import asyncio
import logging
import os
import json
from datetime import datetime
from pathlib import Path
import config

from utils.storage_utils import clear_storage

# File to store the last scrape date
LAST_SCRAPE_FILE = "last_scrape.json"


from multiprocessing import Pool, cpu_count
from config import SCRAPER_SEED_URLS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def process_url(url, worker_id=None):
    try:
        processed_images = scrape_page(url, worker_id)
        print(f"Worker {worker_id}: Successfully processed {len(processed_images)} images from {url}")
        return processed_images
    except Exception as e:
        print(f"Worker {worker_id}: Error processing {url}: {str(e)}")
        return []

def chunk_urls(urls, num_chunks):
    """Split URLs into roughly equal chunks, ensuring proper URL formatting"""
    formatted_urls = [
        url if url.startswith(('http://', 'https://')) else f'https://{url}'
        for url in urls
    ]
    if not formatted_urls:
        return [[]]
    avg = max(1, len(formatted_urls) // num_chunks)
    chunks = [formatted_urls[i:i + avg] for i in range(0, len(formatted_urls), avg)]
    # Ensure we don't have more chunks than workers
    while len(chunks) > num_chunks:
        chunks[-2].extend(chunks[-1])
        chunks.pop()
    return chunks

def process_url_chunk(urls):
    if not urls:
        logging.warning("Empty URL chunk received")
        return []

    results = []
    total = len(urls)
    for idx, url in enumerate(urls, 1):
        try:
            # Ensure URL has proper format
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'
            logging.info(f"Processing URL {idx}/{total}: {url}")
            processed = scrape_page(url)
            logging.info(f"Successfully processed {len(processed)} images from {url}")
            results.extend(processed)
        except Exception as e:
            logging.error(f"Error processing {url}: {str(e)}", exc_info=True)
    return results

def main():
    # Clear storage and DB based on config - only do this for worker 1
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker-id', type=int, default=0)
    parser.add_argument('--total-workers', type=int, default=1)
    args = parser.parse_args()

    if args.worker_id == 1 and config.CLEAR_ON_RUN:
        from utils.storage_utils import clear_storage
        from utils.db_utils import clear_database
        clear_storage()
        clear_database()

    # Track scraping date
    current_date = datetime.now().strftime("%Y-%m-%d")
    scrape_data = {"last_scrape_date": current_date}
    with open(LAST_SCRAPE_FILE, 'w') as f:
        json.dump(scrape_data, f)

    from scraper.task_coordinator import TaskCoordinator
    coordinator = TaskCoordinator(chunk_size=20, total_workers=args.total_workers)
    coordinator.worker_id = args.worker_id

    # Use single seed URL
    seed_url = "https://sheerluxe.com/fashion"

    # Initialize with seed URL if it belongs to this worker
    async def init_coordinator():
        if coordinator.url_belongs_to_worker(seed_url, args.worker_id):
            await coordinator.add_urls([seed_url])

    asyncio.run(init_coordinator())

    # Calculate optimal number of workers based on CPU cores
    num_workers = max(1, cpu_count() - 1)
    chunk_size = len(SCRAPER_SEED_URLS) // num_workers + 1

    print(f"Starting distributed scraping with {num_workers} workers")

    try:
        # Filter seed URLs for each worker using consistent hashing
        def get_worker_urls(worker_id):
            coordinator = TaskCoordinator(total_workers=num_workers)
            coordinator.worker_id = worker_id
            # Only process URLs that belong to this worker
            worker_urls = [url for url in SCRAPER_SEED_URLS 
                         if coordinator.url_belongs_to_worker(url, worker_id)]
            return worker_urls

        with Pool(processes=num_workers) as pool:
            # Each worker only gets its designated URLs
            results = pool.map(process_url_chunk,
                [get_worker_urls(worker_id) for worker_id in range(num_workers)])

            # Combine results from all workers
            all_processed_images = [img for sublist in results if sublist for img in sublist]
            print(f"Successfully processed {len(all_processed_images)} total images from {len(SCRAPER_SEED_URLS)} subcategories")

    except Exception as e:
        print(f"Error during parallel processing: {str(e)}")

if __name__ == "__main__":
    main()
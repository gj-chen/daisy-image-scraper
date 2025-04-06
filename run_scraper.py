
from scraper.scraper import scrape_page
import logging

from utils.storage_utils import clear_storage


from multiprocessing import Pool, cpu_count
from config import SCRAPER_SEED_URLS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def process_url(url):
    try:
        processed_images = scrape_page(url)
        print(f"Successfully processed {len(processed_images)} images from {url}")
        return processed_images
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
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
    # Clear storage before starting
    clear_storage()
    num_workers = max(1, cpu_count() - 1)
    print(f"Starting distributed scraping with {num_workers} workers")
    
    try:
        # Split fashion subcategories among workers
        url_chunks = chunk_urls(SCRAPER_SEED_URLS, num_workers)
        
        with Pool(processes=num_workers) as pool:
            # Each worker processes its chunk of subcategories
            results = pool.map(process_url_chunk, url_chunks)
            
            # Combine results from all workers
            all_processed_images = [img for sublist in results if sublist for img in sublist]
            print(f"Successfully processed {len(all_processed_images)} total images from {len(SCRAPER_SEED_URLS)} subcategories")
            
    except Exception as e:
        print(f"Error during parallel processing: {str(e)}")

if __name__ == "__main__":
    main()

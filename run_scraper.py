
from scraper.scraper import scrape_page
import logging
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
    """Split URLs into roughly equal chunks"""
    avg = len(urls) // num_chunks
    remainder = len(urls) % num_chunks
    chunks = []
    start = 0
    for i in range(num_chunks):
        end = start + avg + (1 if i < remainder else 0)
        chunks.append(urls[start:end])
        start = end
    return chunks

def process_url_chunk(urls):
    results = []
    for url in urls:
        try:
            processed = scrape_page(url)
            print(f"Processed {len(processed)} images from {url}")
            results.extend(processed)
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
    return results

def main():
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

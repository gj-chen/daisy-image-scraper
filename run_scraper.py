
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

def main():
    # Use number of CPUs -1 to leave one core free for system tasks
    num_workers = max(1, cpu_count() - 1)
    print(f"Starting scraping with {num_workers} workers")
    
    try:
        with Pool(processes=num_workers) as pool:
            # Map URLs to worker processes
            results = pool.map(process_url, SCRAPER_SEED_URLS)
            
            # Flatten results
            all_processed_images = [img for sublist in results if sublist for img in sublist]
            print(f"Successfully processed {len(all_processed_images)} total images")
            
    except Exception as e:
        print(f"Error during parallel processing: {str(e)}")

if __name__ == "__main__":
    main()


from scraper.tasks import scrape_page
import os
import time

if __name__ == '__main__':
    seed_url = os.environ.get('SCRAPER_SEED_URLS', 'https://sheerluxe.com/fashion')
    scrape_page.delay(seed_url)
    print(f"[DISPATCH] Seed URL dispatched: {seed_url}")
    
    # Keep the dispatcher alive
    while True:
        time.sleep(60)


import signal
import sys
from scraper.tasks import scrape_page, redis_client
import os
import time

def signal_handler(sig, frame):
    print('Gracefully shutting down...')
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    seed_url = os.environ.get('SCRAPER_SEED_URLS', 'sheerluxe.com/fashion')
    if not seed_url.startswith('http'):
        seed_url = f'https://{seed_url}'
        
    print(f"[START] Dispatcher starting with seed URL: {seed_url}")
    scrape_page.delay(seed_url)
    print(f"[DISPATCH] Seed URL dispatched: {seed_url}")
    
    while True:
        try:
            # Report stats every 30 seconds
            processed_urls = redis_client.scard('processed_urls')
            processed_images = redis_client.scard('processed_images')
            print(f"[STATUS] Processed URLs: {processed_urls}, Images: {processed_images}")
            
            # Redispatch seed if no progress
            if processed_urls == 0:
                print("[REDISPATCH] No URLs processed, reseeding...")
                scrape_page.delay(seed_url)
            
            time.sleep(30)
        except Exception as e:
            print(f"[ERROR] Dispatcher error: {e}")
            time.sleep(5)

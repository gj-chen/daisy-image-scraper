
import signal
import sys
from scraper.tasks import scrape_page
import os
import time

def signal_handler(sig, frame):
    print('Gracefully shutting down...')
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    seed_url = os.environ.get('SCRAPER_SEED_URLS', 'https://sheerluxe.com/fashion')
    scrape_page.delay(seed_url)
    print(f"[DISPATCH] Seed URL dispatched: {seed_url}")
    
    while True:
        try:
            time.sleep(60)
        except Exception as e:
            print(f"Error in dispatcher: {e}")
            time.sleep(5)

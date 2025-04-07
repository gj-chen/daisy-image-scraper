
from scraper.tasks import scrape_page
from scraper.task_coordinator import TaskCoordinator
import sys

if __name__ == '__main__':
    # Get dispatcher ID from command line or default to 0
    dispatcher_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    total_dispatchers = 4  # We'll run 4 dispatchers

    coordinator = TaskCoordinator(total_workers=total_dispatchers)
    seed_url = 'https://sheerluxe.com/fashion'
    
    # Only dispatch if URL belongs to this dispatcher
    if coordinator.url_belongs_to_worker(seed_url, dispatcher_id):
        scrape_page.delay(seed_url)
        print(f"[DISPATCH {dispatcher_id}] Seed URL dispatched: {seed_url}")
    else:
        print(f"[DISPATCH {dispatcher_id}] Seed URL belongs to another dispatcher")

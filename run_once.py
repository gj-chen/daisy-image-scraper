
from flask import Flask
from scraper.celery_app import app
import scraper.tasks  # ✅ Required for registration
from scraper.tasks import scrape_page
import time

flask_app = Flask(__name__)

@flask_app.route('/')
def health():
    return "Sheerluxe Scraper Worker"

if __name__ == '__main__':
    # Start the scrape task
    seed_url = "https://sheerluxe.com/fashion"
    scrape_page.delay(seed_url)  # Dispatch the scraping task
    print(f"[DISPATCHED] {seed_url}")
    time.sleep(2)  # Allow time for task registration
    
    # Start Flask server in a thread
    import threading
    threading.Thread(target=lambda: flask_app.run(host='0.0.0.0', port=5000, threaded=True)).start()
    
    # Start Celery worker
    app.worker_main(argv=["worker", "--loglevel=info"])

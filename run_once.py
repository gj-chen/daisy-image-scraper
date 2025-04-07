
from flask import Flask
from scraper.celery_app import app
import scraper.tasks
from scraper.tasks import scrape_page
import threading
import time

flask_app = Flask(__name__)

@flask_app.route('/')
def health():
    return "Sheerluxe Scraper Worker is healthy", 200

@flask_app.route('/status')
def status():
    return {"status": "running", "service": "sheerluxe-scraper"}, 200

def run_celery_worker():
    app.worker_main(argv=["worker", "--loglevel=info"])

if __name__ == '__main__':
    # Start the scrape task
    seed_url = "https://sheerluxe.com/fashion"
    scrape_page.delay(seed_url)
    print(f"[DISPATCHED] {seed_url}")
    
    # Start Celery worker in a background thread
    worker_thread = threading.Thread(target=run_celery_worker)
    worker_thread.daemon = True
    worker_thread.start()
    
    # Start Flask server in main thread
    flask_app.run(host='0.0.0.0', port=5000)

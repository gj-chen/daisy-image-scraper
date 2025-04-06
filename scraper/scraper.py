import subprocess
import os
from playwright.sync_api import sync_playwright
from config import SHEERLUXE_COOKIE

# Safe function to install Chromium if missing (works gracefully on Railway & Replit)
def install_chromium():
    chromium_path = os.path.expanduser("~/.cache/ms-playwright/chromium")
    if not os.path.exists(chromium_path):
        try:
            subprocess.run(["playwright", "install", "chromium", "--with-deps"], check=True)
        except Exception as e:
            print(f"Could not install Chromium: {e}")

# Call installation explicitly once at import time (safe and idempotent)
install_chromium()

class SheerLuxeScraper:
    def __init__(self):
        self.cookie = SHEERLUXE_COOKIE

    def scrape_page(self, url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies([{
                'name': 'auth_cookie',
                'value': self.cookie,
                'domain': 'sheerluxe.com',
                'path': '/'
            }])

            page = context.new_page()
            page.goto(url)

            images = page.query_selector_all('img')
            scraped_data = []
            for img in images:
                src = img.get_attribute('src')
                context_text = img.evaluate('''(node) => node.closest('article').innerText''')
                scraped_data.append({"image_url": src, "context": context_text})

            browser.close()
            return scraped_data

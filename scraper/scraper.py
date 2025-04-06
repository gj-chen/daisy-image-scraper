# scraper/scraper.py
from playwright.sync_api import sync_playwright
from config import SHEERLUXE_COOKIE

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

            # Scrape images and surrounding text context clearly
            images = page.query_selector_all('img')
            scraped_data = []
            for img in images:
                src = img.get_attribute('src')
                context_text = img.evaluate('''(node) => node.closest('article').innerText''')
                scraped_data.append({"image_url": src, "context": context_text})

            browser.close()
            return scraped_data

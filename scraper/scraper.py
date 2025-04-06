import requests
from bs4 import BeautifulSoup
from config import SHEERLUXE_COOKIE

class SheerLuxeScraper:
    def __init__(self):
        self.cookie = SHEERLUXE_COOKIE

    def scrape_page(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Cookie": f"auth_cookie={self.cookie}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch page: Status code {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        scraped_data = []
        articles = soup.find_all('article')

        for article in articles:
            images = article.find_all('img')
            context_text = article.get_text(separator=' ', strip=True)

            for img in images:
                src = img.get('src')
                if src:
                    scraped_data.append({
                        "image_url": src,
                        "context": context_text
                    })

        return scraped_data

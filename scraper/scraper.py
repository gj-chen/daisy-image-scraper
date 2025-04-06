import requests
from bs4 import BeautifulSoup
from utils.openai_utils import get_embedding, generate_gpt_structured_metadata
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
            raise Exception(f"Failed to fetch page: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # Scraping improvements
        page_title = soup.find('title').get_text(strip=True)

        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content', '').strip()
        else:
            first_para = soup.find('p')
            description = first_para.get_text(strip=True) if first_para else ''

        paragraphs = soup.find_all('p')
        content_summary = ' '.join(p.get_text(strip=True) for p in paragraphs[:3])

        articles = soup.find_all('article')
        scraped_data = []

        for article in articles:
            images = article.find_all('img')
            context_text = article.get_text(separator=' ', strip=True)

            for img in images:
                img_src = img.get('src')
                if not img_src:
                    continue

                # GPT-4 structured metadata generation
                structured_metadata = generate_gpt_structured_metadata({
                    "title": page_title,
                    "description": description,
                    "content_summary": content_summary,
                    "image_context": context_text
                })

                # Embedding generation from structured metadata summary
                embedding_vector = get_embedding(structured_metadata['style_context']['vibe_emotion'])

                # Complete data item
                scraped_item = {
                    "image_url": img_src,
                    "source_url": url,
                    "title": page_title,
                    "description": description,
                    "metadata": structured_metadata,
                    "embedding": embedding_vector
                }

                scraped_data.append(scraped_item)

        return scraped_data

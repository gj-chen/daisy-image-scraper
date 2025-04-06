from flask import Flask, request, jsonify
from scraper.scraper import SheerLuxeScraper
from utils.supabase_client import supabase
import logging
import os

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello Daisy Scraper"

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL parameter missing"}), 400

    logging.info(f"Scraping URL: {url}")

    try:
        # Instantiate the scraper and scrape the provided URL
        scraper = SheerLuxeScraper()
        scraped_data = scraper.scrape_page(url)

        images = [item['image_url'] for item in scraped_data]

        # Example metadata construction—customize as needed
        metadata = {
            "title": f"Scraped content from {url}",
            "description": f"{len(images)} images scraped from the page.",
            "embedding": None  # Replace if embeddings are calculated elsewhere
        }

        # Insert each scraped image into Supabase
        for item in scraped_data:
            img_url = item['image_url']
            context_text = item.get('context', 'No context provided.')

            response = supabase.table('moodboard_items').insert({
                'image_url': img_url,
                'source_url': url,
                'title': metadata['title'],
                'description': context_text,
                'metadata': metadata,
                'embedding': metadata['embedding']
            }).execute()

            if response.data:
                logging.info(f"Successfully stored image {img_url}")
            else:
                logging.error(f"Error storing image {img_url}: {response.error}")

        return jsonify({
            "images": images,
            "metadata": metadata,
            "status": "success"
        }), 200

    except Exception as e:
        logging.exception("An error occurred during scraping.")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
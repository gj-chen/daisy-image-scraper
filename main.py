from flask import Flask, request, jsonify
from scraper.scraper import scrape_page
from utils.supabase_client import supabase
import logging
import os

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL parameter missing"}), 400

    logging.info(f"Scraping URL: {url}")

    try:
        images, metadata = scrape_page(url)

        # Assuming scrape_page returns metadata structured as:
        # {"title": "title", "description": "...", "embedding": [float...]}
        embedding = metadata.pop("embedding", None)

        # Insert each scraped image as a moodboard item into Supabase
        for img_url in images:
            response = supabase.table('moodboard_items').insert({
                'image_url': img_url,
                'source_url': url,
                'title': metadata.get('title', 'No Title'),
                'description': metadata.get('description', 'No Description'),
                'metadata': metadata,
                'embedding': embedding
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
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 8080)))

from flask import Flask, request, jsonify
from scraper.scraper import scrape_page
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Scraper API", "endpoints": ["/scrape"]}), 200

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get('url')

    if not url:
        logging.error("No URL provided.")
        return jsonify({"error": "URL missing"}), 400

    try:
        inserted_images = scrape_page(url)
        count = len(inserted_images)
        logging.info(f"Inserted {count} images successfully.")
        return jsonify({
            "inserted": count,
            "images": inserted_images
        }), 200
    except Exception as e:
        logging.error(f"Critical scraping error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

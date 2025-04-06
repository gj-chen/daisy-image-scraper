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
    url = request.json.get('url')
    if not url:
        logging.error("Missing URL")
        return jsonify({"error": "URL required"}), 400

    images = scrape_page(url)
    return jsonify({"images": images, "inserted": len(images)}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

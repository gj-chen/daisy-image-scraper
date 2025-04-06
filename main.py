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
    try:
        url = request.json.get('url')
        if not url:
            logging.error("Missing URL")
            return jsonify({"error": "URL required"}), 400

        if not url.startswith(('http://', 'https://')):
            return jsonify({"error": "Invalid URL format"}), 400

        images = scrape_page(url)
        return jsonify({"images": images, "inserted": len(images)}), 200
    except requests.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
        return jsonify({"error": "Failed to fetch URL"}), 502
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

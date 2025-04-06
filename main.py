from flask import Flask, request, jsonify
from scraper.scraper import scrape_page
import logging
import requests
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Scraper API", "endpoints": ["/scrape", "/health"]}), 200

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

from typing import Dict, Any
from werkzeug.exceptions import BadRequest
from scraper.exceptions import ScrapingError

@app.route('/scrape', methods=['POST'])
def scrape() -> Dict[str, Any]:
    """
    Endpoint to scrape images from a URL
    
    Returns:
        JSON response with scraped images or error
        
    Raises:
        BadRequest: If URL is missing or invalid
    """
    try:
        if not request.is_json:
            raise BadRequest("Request must be JSON")
            
        url = request.json.get('url')
        if not url:
            logging.error("Missing URL")
            return jsonify({"error": "URL required"}), 400

        if not url.startswith(('http://', 'https://')):
            return jsonify({"error": "Invalid URL format"}), 400

        images = scrape_page(url)
        if not images:
            return jsonify({"error": "No images found"}), 404
            
        return jsonify({"images": images, "inserted": len(images)}), 200
    except requests.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
        return jsonify({"error": str(e), "type": "request_error"}), 502
    except ValueError as e:
        logging.error(f"Validation error: {str(e)}")
        return jsonify({"error": str(e), "type": "validation_error"}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error", "type": "server_error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

from flask import Flask, request, jsonify
from scraper.scraper import scrape_page
import asyncio

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Scraper API", "endpoints": ["/scrape"]}), 200

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL missing"}), 400

    results = asyncio.run(scrape_page(url))
    return jsonify({"inserted": len(results)}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

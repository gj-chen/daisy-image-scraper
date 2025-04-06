from flask import Flask, request, jsonify
from scraper.scraper import scrape_page
import asyncio

app = Flask(__name__)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL missing"}), 400

    results = asyncio.run(scrape_page(url))
    return jsonify({"inserted": len(results)}), 200

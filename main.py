# main.py
from scraper.scraper import SheerLuxeScraper
from scraper.metadata_generator import MetadataGenerator
from scraper.embeddings_generator import EmbeddingsGenerator
from scraper.uploader import Uploader
from utils.supabase_client import supabase
import json

def main(test_url):
    scraper = SheerLuxeScraper()
    scraped_items = scraper.scrape_page(test_url)

    for item in scraped_items:
        image_url = item["image_url"]
        context_text = item["context"]

        uploaded_image_url = Uploader.upload_image(image_url)
        metadata_json = MetadataGenerator.generate(uploaded_image_url, context_text)
        embeddings = EmbeddingsGenerator.generate(metadata_json)

        supabase.table('moodboard_items').insert({
            "image_url": uploaded_image_url,
            "source_url": image_url,
            "metadata": json.loads(metadata_json),
            "embedding": embeddings
        }).execute()

        print(f"Processed and uploaded: {uploaded_image_url}")

if __name__ == "__main__":
    test_url = "https://sheerluxe.com/fashion/designer/the-ralph-lauren-spring-2025-collection-is-perfect-for-the-season-ahead"  # Clearly replace with actual test URL
    main(test_url)

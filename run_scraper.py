
from scraper.scraper import scrape_page
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    seed_url = "https://sheerluxe.com"
    try:
        processed_images = scrape_page(seed_url)
        print(f"Successfully processed {len(processed_images)} images")
        for img in processed_images:
            print(f"- {img}")
    except Exception as e:
        print(f"Error during scraping: {str(e)}")

if __name__ == "__main__":
    main()

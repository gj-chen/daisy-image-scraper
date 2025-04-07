from scraper.tasks import scrape_page

if __name__ == '__main__':
    seed_url = 'https://sheerluxe.com/fashion'
    scrape_page.delay(seed_url)
    print(f"[DISPATCH] Seed URL dispatched: {seed_url}")

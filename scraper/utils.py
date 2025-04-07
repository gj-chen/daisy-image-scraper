import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

def fetch_and_extract_urls_and_images(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Only follow links from 2019–2025
    allowed_years = {'2019', '2020', '2021', '2022', '2023', '2024', '2025'}

    urls = {
        urljoin(url, a['href']) for a in soup.find_all('a', href=True)
        if any(year in a['href'] for year in allowed_years)
    }

    images = {
        urljoin(url, img['src']) for img in soup.find_all('img', src=True)
    }

    return urls, images

def download_image_file(image_url):
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"[ERROR] Failed to download image {image_url}: {e}")
        return None
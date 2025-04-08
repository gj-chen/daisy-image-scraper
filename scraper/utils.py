import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def fetch_and_extract_urls_and_images(base_url):
    try:
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        urls = set()
        images = set()

        # Extract and print all <a> links
        raw_links = soup.find_all("a", href=True)
        print(f"[PARSE] {base_url} → Found {len(raw_links)} raw <a> tags")

        for a in raw_links:
            href = a['href']
            full_url = urljoin(base_url, href)
            print(f"  ↳ [LINK] {full_url}")
            if "sheerluxe.com/fashion" in full_url:
                urls.add(full_url)

        raw_imgs = soup.find_all("img", src=True)
        print(f"[PARSE] {base_url} → Found {len(raw_imgs)} raw <img> tags")

        for img in raw_imgs:
            src = img['src']
            full_img_url = urljoin(base_url, src)
            print(f"  🖼️ [IMAGE] {full_img_url}")
            if "sheerluxe.com" in full_img_url:
                images.add(full_img_url)

        print(f"[RESULT] {base_url} → {len(urls)} valid URLs, {len(images)} valid images")
        return urls, images

    except Exception as e:
        print(f"[ERROR] Failed to parse {base_url}: {e}")
        return set(), set()

def download_image_file(image_url):
    import requests
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"[ERROR] Failed to download image {image_url}: {e}")
        return None


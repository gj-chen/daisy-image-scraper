# scraper/uploader.py
import requests
from config import UPLOAD_ENDPOINT

class Uploader:
    @staticmethod
    def upload_image(image_url):
        response = requests.get(image_url)
        file_bytes = response.content
        file_name = image_url.split("/")[-1]

        files = {'file': (file_name, file_bytes)}
        upload_response = requests.post(UPLOAD_ENDPOINT, files=files)

        if upload_response.status_code == 200:
            return upload_response.json()["image_url"]
        else:
            raise Exception(f"Upload failed: {upload_response.json()}")

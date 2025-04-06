
from utils.supabase_client import supabase
import requests
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def store_image(image_url: str, existing_images=None) -> str:
    try:
        # Check if image already exists in our known set
        if existing_images and image_url in existing_images:
            logger.info(f"Image already exists: {image_url}")
            return image_url
            
        response = requests.get(image_url)
        if response.status_code != 200:
            logger.error(f"Failed to fetch image {image_url}: HTTP {response.status_code}")
            return None
            
        # Clean filename - remove query parameters and special characters
        base_name = image_url.split('?')[0].split('/')[-1]
        safe_name = re.sub(r'[^a-zA-Z0-9.-]', '_', base_name)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}"
        
        # Upload to Supabase Storage with upsert option
        result = supabase.storage.from_('sheerluxe-images').upload(
            filename,
            response.content,
            file_options={
                "contentType": response.headers.get("content-type", "image/jpeg")
            }
        )
        
        # Get public URL
        public_url = supabase.storage.from_('sheerluxe-images').get_public_url(filename)
        logger.info(f"Stored image: {filename}")
        return public_url
    except Exception as e:
        logger.error(f"Failed to store image {image_url}: {str(e)}")
        return None

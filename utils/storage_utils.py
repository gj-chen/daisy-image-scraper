
from utils.supabase_client import supabase_client

def clear_storage():
    try:
        items = supabase_client.storage.from_('sheerluxe-images').list()
        for item in items:
            supabase_client.storage.from_('sheerluxe-images').remove([item['name']])
        logger.info("Cleared storage bucket")
        return True
    except Exception as e:
        logger.error(f"Failed to clear storage: {str(e)}")
        return False


import requests
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def store_image(image_url: str, existing_images=None) -> str:
    try:
        # Check both original URL and processed URL for duplicates
        if existing_images:
            # Check original URL
            if image_url in existing_images:
                logger.info(f"Image exists in DB: {image_url}")
                return image_url
                
            # Check processed URL format 
            base_name = image_url.split('?')[0].split('/')[-1]
            safe_name = re.sub(r'[^a-zA-Z0-9.-]', '_', base_name)
            processed_url = f"https://kepdfmsdvrlsloyilqsw.supabase.co/storage/v1/object/sheerluxe-images/{safe_name}"
            
            if processed_url in existing_images:
                logger.info(f"Image exists in DB with processed URL: {processed_url}")
                return processed_url
        
        # Only check storage if not in DB
        storage_cache = getattr(store_image, '_storage_cache', None)
        if storage_cache is None:
            try:
                storage_cache = {item['name'] for item in supabase_client.storage.from_('sheerluxe-images').list()}
                store_image._storage_cache = storage_cache
            except Exception as e:
                logger.warning(f"Storage cache init failed: {str(e)}")
                storage_cache = set()
        
        if any(item.endswith(safe_name) for item in storage_cache):
            logger.info(f"Image exists in storage: {image_url}")
            return f"https://kepdfmsdvrlsloyilqsw.supabase.co/storage/v1/object/sheerluxe-images/{safe_name}"
            
        response = requests.get(image_url)
        if response.status_code != 200:
            logger.error(f"Failed to fetch image {image_url}: HTTP {response.status_code}")
            return None
            
        # Clean filename - remove query parameters and special characters
        base_name = image_url.split('?')[0].split('/')[-1]
        safe_name = re.sub(r'[^a-zA-Z0-9.-]', '_', base_name)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}"
        
        try:
            # Upload to Supabase Storage
            result = supabase_client.storage.from_('sheerluxe-images').upload(
                filename,
                response.content,
                file_options={
                    "contentType": response.headers.get("content-type", "image/jpeg")
                }
            )
            # Get public URL for new upload
            public_url = supabase_client.storage.from_('sheerluxe-images').get_public_url(filename)
            logger.info(f"Stored image: {filename}")
            return public_url
        except Exception as upload_error:
            if "'statusCode': 409" in str(upload_error):  # Duplicate file
                # If duplicate, return URL of existing file
                public_url = supabase_client.storage.from_('sheerluxe-images').get_public_url(filename)
                logger.info(f"Using existing image: {filename}")
                return public_url
            raise  # Re-raise other errors
    except Exception as e:
        logger.error(f"Failed to store image {image_url}: {str(e)}")
        return None

from supabase import create_client
from openai import OpenAI
import os, logging
from datetime import datetime
import json
from config import BATCH_SIZE

logger = logging.getLogger(__name__)

supabase_client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def insert_metadata_to_supabase_sync(metadata_list, batch_size=5000):
    try:
        logger.info(f"Starting DB flush for {len(metadata_list)} records")
        # Pre-process and deduplicate records
        seen_urls = set()
        processed_records = []
        failed_records = []
        
        for record in metadata_list:
            if record['image_url'] not in seen_urls:
                seen_urls.add(record['image_url'])
                # Remove None values and empty strings
                cleaned_record = {k: v for k, v in record.items() 
                                if v is not None and v != ""}
                processed_records.append(cleaned_record)
        
        if not processed_records:
            return
            
        # Split into smaller batches
        batches = [processed_records[i:i + batch_size] 
                  for i in range(0, len(processed_records), batch_size)]
        
        # Use regular insert with error handling per batch
        for batch in batches:
            try:
                logger.info(f"========== STARTING DB FLUSH: {len(batch)} records ==========")
                supabase_client.table('moodboard_items')\
                    .insert(batch)\
                    .execute()
                logger.info(f"========== COMPLETED DB FLUSH: {len(batch)} records ==========")
            except Exception as e:
                logger.error(f"Failed to insert batch: {str(e)}")
                failed_records.extend(batch)
                continue
                
        # Retry failed records individually
        for record in failed_records:
            try:
                supabase_client.table('moodboard_items')\
                    .insert([record])\
                    .execute()
                logger.info("Recovered failed record")
            except Exception as e:
                logger.error(f"Failed to recover record {record['image_url']}: {str(e)}")
            
    except Exception as e:
        logger.error(f"Supabase Error: {e}")
        # Log failed batch for retry
        logger.error(f"Failed batch size: {len(metadata_list)}")
        raise

def generate_embedding_sync(metadata):
    try:
        response = client.embeddings.create(
            input=json.dumps(metadata),
            model="text-embedding-ada-002"
        )
        embedding_vector = response.data[0].embedding
        return embedding_vector
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        return []


def check_url_exists(url: str) -> bool:
    try:
        result = supabase_client.table('moodboard_items').select('id').eq('source_url', url).limit(1).execute()
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Failed to check URL existence: {e}")
        return False

def check_image_exists(image_url: str) -> bool:
    try:
        result = supabase_client.table('moodboard_items').select('id').eq('image_url', image_url).limit(1).execute()
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Failed to check image existence: {e}")
        return False

def get_existing_urls_and_images():
    try:
        result = supabase_client.table('moodboard_items').select('source_url,image_url').execute()
        urls = {item['source_url'] for item in result.data if item['source_url']}
        images = {item['image_url'] for item in result.data if item['image_url']}
        return urls, images
    except Exception as e:
        logger.error(f"Failed to fetch existing URLs and images: {e}")
        return set(), set()

def prepare_metadata_record(image_url, source_url, title, description, structured_metadata, embedding, stored_image_url=None):
    return {
        "image_url": image_url,
        "stored_image_url": stored_image_url,
        "source_url": source_url,
        "title": title,
        "description": description,
        "metadata": structured_metadata,
        "embedding": embedding,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
def clear_database():
    """Clear all records from the database"""
    from utils.supabase_client import supabase_client
    # Delete all records using a filter that matches everything
    supabase_client.table('moodboard_items').delete().filter('id', 'not.is', 'null').execute()
    logger.info("Cleared database")

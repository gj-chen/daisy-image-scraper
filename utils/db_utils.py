from supabase import create_client
from openai import OpenAI
import os, logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

supabase_client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def insert_metadata_to_supabase_sync(metadata_list, batch_size=BATCH_SIZE):
    try:
        batches = [metadata_list[i:i + batch_size] for i in range(0, len(metadata_list), batch_size)]
        for batch in batches:
            supabase_client.table('moodboard_items').insert(batch).execute()
            logger.info(f"Inserted batch of {len(batch)} records.")
    except Exception as e:
        logger.error(f"Supabase Error: {e}")
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

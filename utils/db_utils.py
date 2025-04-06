import openai
from supabase import create_client
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not openai.api_key:
    logger.critical("Missing environment variables!")
    raise ValueError("Required environment variables missing!")

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_metadata_to_supabase_sync(metadata_list):
    try:
        supabase_client.table('moodboard_items').insert(metadata_list).execute()
        logger.info(f"Inserted {len(metadata_list)} records into Supabase.")
    except Exception as e:
        logger.error(f"Supabase insertion error: {str(e)}")

def generate_embedding_sync(metadata):
    try:
        response = openai.Embedding.create(
            input=json.dumps(metadata),
            model="text-embedding-ada-002"
        )
        return response['data'][0]['embedding']
    except Exception as e:
        logger.error(f"Embedding error: {str(e)}")
        return []

def prepare_metadata_record(image_url, source_url, title, description, structured_metadata, embedding):
    return {
        "image_url": image_url,
        "source_url": source_url,
        "title": title,
        "description": description,
        "metadata": structured_metadata,
        "embedding": embedding,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

from supabase import create_client
import logging
import os
from openai import OpenAI
from datetime import datetime

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not OPENAI_API_KEY:
    logger.critical("Supabase or OpenAI credentials missing! Check environment variables.")
    raise ValueError("Required environment variables missing!")

client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def insert_metadata_to_supabase(metadata_list):
    try:
        response = client.table('moodboard_items').insert(metadata_list).execute()
        if response:
            logger.info(f"Inserted {len(metadata_list)} metadata records successfully.")
        else:
            logger.error("No response received from Supabase insertion.")
    except Exception as e:
        logger.error(f"Supabase insertion error: {str(e)}")

def generate_embedding(metadata):
    try:
        text_content = str(metadata)
        response = openai_client.embeddings.create(
            input=text_content,
            model="text-embedding-ada-002"
        )
        embedding_vector = response.data[0].embedding
        logger.info("Embedding generated successfully.")
        return embedding_vector
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
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

from supabase import create_client
from openai import AsyncOpenAI
import logging
import os
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not OPENAI_API_KEY:
    logger.critical("Supabase or OpenAI credentials missing! Check environment variables.")
    raise ValueError("Required environment variables missing!")

# Synchronous Supabase client
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Async OpenAI client
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Async-friendly wrapper for sync Supabase insert
async def insert_metadata_to_supabase_async(metadata_list):
    loop = asyncio.get_running_loop()
    try:
        response = await loop.run_in_executor(None, lambda: supabase_client.table('moodboard_items').insert(metadata_list).execute())
        logger.info(f"Inserted {len(metadata_list)} records into Supabase.")
        return response
    except Exception as e:
        logger.error(f"Supabase insertion failed: {str(e)}")

# OpenAI Embedding (Async)
async def generate_embedding_async(metadata):
    try:
        response = await openai_client.embeddings.create(
            input=str(metadata),
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        return []

# Prepare record (Sync)
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

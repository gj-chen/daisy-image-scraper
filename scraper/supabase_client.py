import os
from supabase import create_client
from uuid import uuid4
import mimetypes

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'sheerluxe-images')
SUPABASE_TABLE = os.environ.get('SUPABASE_TABLE', 'moodboard_items')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_image_to_supabase(image_url, image_bytes):
    filename = f"{uuid4()}.jpg"
    content_type = mimetypes.guess_type(image_url)[0] or "image/jpeg"

    try:
        supabase.storage.from_(SUPABASE_BUCKET).upload(filename, image_bytes, {
            "content-type": content_type
        })

        stored_image_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
        print(f"[UPLOAD] Image stored: {filename}")
        return stored_image_url
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        return None

def store_analysis_result(
    image_url,
    metadata,
    embedding=None,
    stored_image_url=None,
    source_url=None,
    title=None,
    description=None
):
    try:
        data = {
            "image_url": image_url,
            "metadata": metadata
        }

        if embedding:
            data["embedding"] = embedding
        if stored_image_url:
            data["stored_image_url"] = stored_image_url
        if source_url:
            data["source_url"] = source_url
        if title:
            data["title"] = title
        if description:
            data["description"] = description

        supabase.table("moodboard_items").insert(data).execute()
        print(f"[✅ DB] Saved metadata for: {image_url}")

    except Exception as e:
        print(f"[ERROR] DB insert failed: {e}")



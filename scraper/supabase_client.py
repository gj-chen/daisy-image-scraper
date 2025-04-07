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
        supabase.storage.from_(SUPABASE_BUCKET).upload(filename, image_bytes, {"content-type": content_type})
        print(f"[UPLOAD] Image stored: {filename}")
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")

def store_analysis_result(image_url, analysis):
    try:
        supabase.table(SUPABASE_TABLE).insert({
            "image_url": image_url,
            "analysis": analysis
        }).execute()
        print(f"[DB] Metadata stored for {image_url}")
    except Exception as e:
        print(f"[ERROR] DB insert failed: {e}")


from supabase import create_client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase URL or Key environment variables.")

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

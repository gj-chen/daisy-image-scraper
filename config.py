# config.py
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UPLOAD_ENDPOINT = os.getenv("UPLOAD_ENDPOINT")

SHEERLUXE_COOKIE = os.getenv("SHEERLUXE_COOKIE")
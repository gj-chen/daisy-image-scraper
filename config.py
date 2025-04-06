# config.py
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

def get_required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value

def get_optional_env(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(key, default)

# Required configs
SUPABASE_URL = get_required_env("SUPABASE_URL")
SUPABASE_KEY = get_required_env("SUPABASE_KEY") 
OPENAI_API_KEY = get_required_env("OPENAI_API_KEY")

# Optional configs
UPLOAD_ENDPOINT = get_optional_env("UPLOAD_ENDPOINT", "default_endpoint")
SHEERLUXE_COOKIE = get_optional_env("SHEERLUXE_COOKIE")

# Constants
DEFAULT_BATCH_SIZE = 50
MAX_RETRIES = 3
REQUEST_TIMEOUT = 120
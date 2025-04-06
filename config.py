
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

def get_required_env(key: str) -> str:
    value: Optional[str] = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value

def get_optional_env(key: str, default: Optional[str] = None) -> Optional[str]:
    value: Optional[str] = os.getenv(key, default)
    return value

# Required configs - critical for core functionality
SUPABASE_URL = get_required_env("SUPABASE_URL")
SUPABASE_KEY = get_required_env("SUPABASE_KEY") 
OPENAI_API_KEY = get_required_env("OPENAI_API_KEY")

# Optional configs - can have defaults
UPLOAD_ENDPOINT = get_optional_env("UPLOAD_ENDPOINT", "https://default-upload-endpoint.com")
SHEERLUXE_COOKIE = get_optional_env("SHEERLUXE_COOKIE", "")

# Constants
MAX_RETRIES = 3
SCRAPER_CONCURRENCY_LIMIT = 10  # Increased concurrency
SCRAPER_MAX_AGE_YEARS = 3
SCRAPER_MAX_DEPTH = 3
BATCH_SIZE = 50  # For batch DB operations
URL_BATCH_SIZE = 100  # For URL frontier processing
SCRAPER_SEED_URL = "https://sheerluxe.com"  # Seed URL for crawling

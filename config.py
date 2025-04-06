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
SCRAPER_CONCURRENCY_LIMIT = 50  # Higher concurrency for more parallel processing
SCRAPER_MAX_AGE_YEARS = 3
SCRAPER_MAX_DEPTH = 3
BATCH_SIZE = 500  # Larger batch size for DB operations
URL_BATCH_SIZE = 500  # Process more URLs at once
IMAGE_BATCH_SIZE = 10  # Double image batch size while keeping OpenAI rate limits in mind
# Get seed URLs from environment variable, fallback to default if not set
# Multiple entry points for parallel processing
FASHION_SUBCATEGORIES = [
    "designer", "how-to-wear", "interviews", "shopping", "high-street",
    "inspiration", "shoots", "conscious-edit", "denim", "trends",
    "dresses", "tops", "knits", "accessories", "jewellery",
    "shoes", "activewear", "bags", "holiday", "lounge-nightwear",
    "occasion", "skirts-trousers", "workwear"
]

DEFAULT_SEEDS = [f"https://sheerluxe.com/fashion/{cat}" for cat in FASHION_SUBCATEGORIES]
# Ensure all seed URLs are properly formatted
SCRAPER_SEED_URLS = [
    url if url.startswith(('http://', 'https://')) else f'https://{url}'
    for url in get_optional_env("SCRAPER_SEED_URLS", ",".join(DEFAULT_SEEDS)).split(",")
]
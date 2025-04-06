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
CLEAR_ON_RUN = True  # Clear storage and DB on new runs
MAX_RETRIES = 3
SCRAPER_CONCURRENCY_LIMIT = 400  # Increased for better throughput while maintaining rate limits
SCRAPER_MAX_AGE_YEARS = 6  # Keep 6 years as requested
SCRAPER_MAX_DEPTH = 10  # Keep depth the same
BATCH_SIZE = 10000  # Increased for better DB performance
URL_BATCH_SIZE = 10000  # Increased for better throughput
IMAGE_BATCH_SIZE = 500  # Increased for better parallel processing
# Rate limiting
OPENAI_RATE_LIMIT = 50  # Requests per minute per worker
STORAGE_RATE_LIMIT = 30  # Uploads per minute per worker
SCRAPER_RATE_LIMIT = 20  # Requests per minute per worker

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
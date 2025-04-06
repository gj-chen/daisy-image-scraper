
import aiohttp
import logging
from config import SHEERLUXE_COOKIE

logger = logging.getLogger(__name__)

class AuthSession:
    def __init__(self):
        self.cookies = {}
        if SHEERLUXE_COOKIE:
            try:
                # Parse cookie string into dict
                cookie_pairs = SHEERLUXE_COOKIE.split(';')
                for pair in cookie_pairs:
                    key, value = pair.strip().split('=', 1)
                    self.cookies[key] = value
            except Exception as e:
                logger.error(f"Failed to parse cookie: {e}")

    def get_headers(self):
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cookie': SHEERLUXE_COOKIE if SHEERLUXE_COOKIE else ''
        }

    async def create_session(self):
        return aiohttp.ClientSession(headers=self.get_headers())

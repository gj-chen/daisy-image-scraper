
import aiohttp
import logging
from config import SHEERLUXE_COOKIE

logger = logging.getLogger(__name__)

class AuthSession:
    def __init__(self):
        self.cookies = {}
        if not SHEERLUXE_COOKIE:
            logger.warning("No SHEERLUXE_COOKIE provided - authentication may fail")
            return
            
        try:
            # Parse cookie string into dict
            cookie_pairs = SHEERLUXE_COOKIE.split(';')
            for pair in cookie_pairs:
                if '=' in pair:
                    parts = pair.strip().split('=')
                    key = parts[0]
                    value = '='.join(parts[1:])  # Join back parts in case value contains =
                    self.cookies[key] = value
            logger.info("Successfully initialized auth session with cookies")
        except Exception as e:
            logger.error(f"Failed to parse cookie: {e}")

    def get_headers(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        if SHEERLUXE_COOKIE:
            headers['Cookie'] = SHEERLUXE_COOKIE
            
        return headers

    async def create_session(self):
        return aiohttp.ClientSession(headers=self.get_headers())

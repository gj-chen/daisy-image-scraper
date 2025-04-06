
from collections import deque
from datetime import datetime, timedelta
import logging
from typing import Set, Optional
import re

logger = logging.getLogger(__name__)

class URLFrontier:
    def __init__(self, max_depth: int = SCRAPER_MAX_DEPTH, max_age_years: int = SCRAPER_MAX_AGE_YEARS):
        self.queue = deque()
        self.visited = set()
        self.max_depth = max_depth
        self.max_age_years = max_age_years
        
    def add_url(self, url: str, depth: int = 0):
        if url not in self.visited and depth <= self.max_depth:
            self.queue.append((url, depth))
            
    def get_next_url(self) -> Optional[tuple[str, int]]:
        return self.queue.popleft() if self.queue else None
        
    def mark_visited(self, url: str):
        self.visited.add(url)
        
    def is_valid_date(self, url: str) -> bool:
        # Extract date from URL pattern like /2025/04/
        date_match = re.search(r'/(\d{4})/(\d{2})/', url)
        if not date_match:
            return False
            
        article_date = datetime(int(date_match.group(1)), int(date_match.group(2)), 1)
        cutoff_date = datetime.now() - timedelta(days=365 * self.max_age_years)
        return article_date >= cutoff_date

    @property
    def has_urls(self) -> bool:
        return len(self.queue) > 0

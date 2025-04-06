
import asyncio
from typing import List, Set
import logging
from collections import deque

logger = logging.getLogger(__name__)

from utils.supabase_client import supabase_client
import time

class TaskCoordinator:
    def __init__(self, chunk_size: int = 50):  # Increased chunk size
        self.pending_urls: deque = deque(maxlen=100000)  # Set max length to prevent memory issues
        self.processing_urls: Set[str] = set()
        self.completed_urls: Set[str] = set()
        self.chunk_size = chunk_size
        self.worker_id = None
        
    def acquire_lock(self, url: str) -> bool:
        try:
            result = supabase_client.table('url_locks').insert({
                'url': url,
                'worker_id': self.worker_id,
                'locked_at': int(time.time())
            }).execute()
            return len(result.data) > 0
        except:
            return False
        
    def add_urls(self, urls: List[str]) -> None:
        for url in urls:
            if url not in self.completed_urls and url not in self.processing_urls:
                self.pending_urls.append(url)
                
    def get_next_batch(self) -> List[str]:
        batch = []
        while len(batch) < self.chunk_size and self.pending_urls:
            url = self.pending_urls.popleft()
            if url not in self.processing_urls and url not in self.completed_urls:
                batch.append(url)
                self.processing_urls.add(url)
        return batch
        
    def mark_completed(self, urls: List[str]) -> None:
        for url in urls:
            if url in self.processing_urls:
                self.processing_urls.remove(url)
            self.completed_urls.add(url)

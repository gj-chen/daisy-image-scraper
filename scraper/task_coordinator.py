
import asyncio
from typing import List, Set
import logging
from collections import deque
import hashlib

logger = logging.getLogger(__name__)

from utils.supabase_client import supabase_client
import time

class TaskCoordinator:
    def __init__(self, chunk_size: int = 50, total_workers: int = 8):
        self.pending_urls: deque = deque(maxlen=100000)
        self.processing_urls: Set[str] = set()
        self.completed_urls: Set[str] = set()
        self.chunk_size = chunk_size
        self.worker_id = None
        self.total_workers = total_workers
        
    def url_belongs_to_worker(self, url: str, worker_id: int) -> bool:
        """Determine if URL should be processed by this worker using consistent hashing"""
        url_hash = int(hashlib.md5(url.encode()).hexdigest(), 16)
        return url_hash % self.total_workers == worker_id
        
    def add_urls(self, urls: List[str]) -> None:
        """Only add URLs that belong to this worker"""
        for url in urls:
            if (url not in self.completed_urls and 
                url not in self.processing_urls and
                self.url_belongs_to_worker(url, self.worker_id)):
                self.pending_urls.append(url)
                
    def get_next_batch(self) -> List[str]:
        batch = []
        while len(batch) < self.chunk_size and self.pending_urls:
            url = self.pending_urls.popleft()
            if url not in self.processing_urls and url not in self.completed_urls:
                batch.append(url)
                self.processing_urls.add(url)
        return batch
        
    async def mark_url_visited(self, url: str) -> None:
        """Mark URL as visited in shared state"""
        try:
            await supabase_client.table('visited_urls').insert({
                'url': url,
                'worker_id': self.worker_id,
                'visited_at': int(time.time())
            }).execute()
        except Exception as e:
            logger.error(f"Failed to mark URL visited: {str(e)}")
            
    def mark_completed(self, urls: List[str]) -> None:
        for url in urls:
            if url in self.processing_urls:
                self.processing_urls.remove(url)
            self.completed_urls.add(url)
            asyncio.create_task(self.mark_url_visited(url))

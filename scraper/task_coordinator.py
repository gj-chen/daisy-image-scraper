
import asyncio
from typing import List, Set
import logging
from collections import deque

logger = logging.getLogger(__name__)

class TaskCoordinator:
    def __init__(self, chunk_size: int = 20):
        self.pending_urls: deque = deque()
        self.processing_urls: Set[str] = set()
        self.completed_urls: Set[str] = set()
        self.chunk_size = chunk_size
        
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

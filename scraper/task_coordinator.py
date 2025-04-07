
import asyncio
from typing import List, Set
import logging
import hashlib
import time
import redis
import json
from utils.supabase_client import supabase_client

logger = logging.getLogger(__name__)

class TaskCoordinator:
    def __init__(self, chunk_size: int = 50, total_workers: int = 8):
        self.chunk_size = chunk_size
        self.worker_id = None
        self.total_workers = total_workers
        self.redis = redis.Redis(host='0.0.0.0', port=6379, decode_responses=True)
        
    def url_belongs_to_worker(self, url: str, worker_id: int) -> bool:
        url_hash = int(hashlib.md5(url.encode()).hexdigest(), 16)
        return url_hash % self.total_workers == worker_id

    async def get_next_batch(self) -> List[str]:
        """Get next batch of URLs from Redis queue"""
        try:
            # Atomic operation to get and mark URLs as processing
            urls = []
            pipe = self.redis.pipeline()
            for _ in range(self.chunk_size):
                url = self.redis.rpoplpush('pending_urls', f'processing_urls:{self.worker_id}')
                if url:
                    urls.append(url)
            pipe.execute()
            return urls
        except Exception as e:
            logger.error(f"Failed to get next batch: {str(e)}")
            return []

    async def add_urls(self, urls: List[str]) -> None:
        """Add new URLs to Redis queue"""
        try:
            pipe = self.redis.pipeline()
            for url in urls:
                if self.url_belongs_to_worker(url, self.worker_id):
                    # Only add if not already processed
                    if not self.redis.sismember('completed_urls', url):
                        pipe.lpush('pending_urls', url)
            pipe.execute()
        except Exception as e:
            logger.error(f"Failed to add URLs: {str(e)}")

    async def mark_completed(self, urls: List[str]) -> None:
        """Mark URLs as completed in Redis"""
        try:
            pipe = self.redis.pipeline()
            for url in urls:
                # Remove from processing and add to completed
                pipe.lrem(f'processing_urls:{self.worker_id}', 0, url)
                pipe.sadd('completed_urls', url)
            pipe.execute()
        except Exception as e:
            logger.error(f"Failed to mark URLs completed: {str(e)}")

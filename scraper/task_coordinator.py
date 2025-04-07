
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
        self.redis = redis.Redis(
            host=os.environ['REDIS_HOST'],
            port=int(os.environ['REDIS_PORT']),
            password=os.environ['REDIS_PASSWORD'],
            ssl=True,
            ssl_cert_reqs=None,
            decode_responses=True
        )
        
    def url_belongs_to_worker(self, url: str, worker_id: int) -> bool:
        url_hash = int(hashlib.md5(url.encode()).hexdigest(), 16)
        return url_hash % self.total_workers == worker_id

    async def get_next_batch(self) -> List[str]:
        """Get next batch of URLs from Redis queue"""
        try:
            # Atomic operation to get and mark URLs as processing
            urls = []
            pipe = self.redis.pipeline()
            # Get all pending URLs and filter for this worker
            pending = self.redis.lrange('pending_urls', 0, -1) or []
            for url in pending:
                if self.url_belongs_to_worker(url, self.worker_id):
                    pipe.lrem('pending_urls', 1, url)
                    pipe.rpush(f'processing_urls:{self.worker_id}', url)
                    urls.append(url)
                if len(urls) >= self.chunk_size:
                    break
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
                    # Check completed, pending and processing queues
                    if not (self.redis.sismember('completed_urls', url) or
                           self.redis.lpos('pending_urls', url) or
                           any(self.redis.lpos(f'processing_urls:{i}', url)
                               for i in range(self.total_workers))):
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

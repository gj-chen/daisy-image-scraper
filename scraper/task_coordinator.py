import asyncio
from typing import List, Set
import logging
import hashlib
import time
import os
import redis
import json
from scraper.supabase_client import supabase

logger = logging.getLogger(__name__)

class TaskCoordinator:
    def __init__(self):
        self.redis = redis.Redis.from_url(
            f"rediss://:{os.environ.get('REDIS_PASSWORD', '')}@{os.environ.get('REDIS_HOST', '0.0.0.0')}:{os.environ.get('REDIS_PORT', '6379')}/0?ssl_cert_reqs=none",
            decode_responses=True
        )

    async def get_next_batch(self) -> List[str]:
        """Get next batch of URLs from Redis queue"""
        try:
            # Atomic operation to get and mark URLs as processing
            urls = self.redis.rpop('pending_urls', self.chunk_size) or []
            if urls:
                for url in urls:
                    self.redis.rpush('processing_urls', url)
            return urls
        except Exception as e:
            logger.error(f"Failed to get next batch: {str(e)}")
            return []

    async def add_urls(self, urls: List[str]) -> None:
        """Add new URLs to Redis queue"""
        try:
            pipe = self.redis.pipeline()
            for url in urls:
                #Check if the url is already in the queue
                if not self.redis.sismember('completed_urls', url) and not self.redis.lpos('pending_urls',url) and not self.redis.lpos('processing_urls', url):
                    pipe.lpush('pending_urls', url)
            pipe.execute()
        except Exception as e:
            logger.error(f"Failed to add URLs: {str(e)}")

    async def mark_completed(self, urls: List[str]) -> None:
        """Mark URLs as completed in Redis"""
        try:
            pipe = self.redis.pipeline()
            for url in urls:
                pipe.lrem('processing_urls', 1, url) #remove from processing
                pipe.sadd('completed_urls', url) #add to completed
            pipe.execute()
        except Exception as e:
            logger.error(f"Failed to mark URLs completed: {str(e)}")
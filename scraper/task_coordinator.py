
import asyncio
from typing import List, Set
import logging
import hashlib
import time
from collections import deque
from utils.supabase_client import supabase_client

logger = logging.getLogger(__name__)

class TaskCoordinator:
    def __init__(self, chunk_size: int = 50, total_workers: int = 8):
        self.chunk_size = chunk_size
        self.worker_id = None
        self.total_workers = total_workers
        
    def url_belongs_to_worker(self, url: str, worker_id: int) -> bool:
        """Determine if URL should be processed by this worker using consistent hashing"""
        url_hash = int(hashlib.md5(url.encode()).hexdigest(), 16)
        return url_hash % self.total_workers == worker_id

    async def get_next_batch(self) -> List[str]:
        """Get next batch of URLs from shared queue"""
        try:
            response = await supabase_client.table('url_queue')\
                .select('url')\
                .eq('status', 'pending')\
                .limit(self.chunk_size)\
                .execute()
            
            urls = [r['url'] for r in response.data]
            if urls:
                # Mark URLs as processing
                await supabase_client.table('url_queue')\
                    .update({'status': 'processing', 'worker_id': self.worker_id})\
                    .in_('url', urls)\
                    .execute()
            return urls
        except Exception as e:
            logger.error(f"Failed to get next batch: {str(e)}")
            return []

    async def add_urls(self, urls: List[str]) -> None:
        """Add new URLs to shared queue"""
        try:
            # Filter URLs that belong to this worker
            worker_urls = [
                {'url': url, 'status': 'pending', 'created_at': int(time.time())}
                for url in urls
                if self.url_belongs_to_worker(url, self.worker_id)
            ]
            if worker_urls:
                await supabase_client.table('url_queue').upsert(worker_urls).execute()
        except Exception as e:
            logger.error(f"Failed to add URLs: {str(e)}")

    async def mark_completed(self, urls: List[str]) -> None:
        """Mark URLs as completed in shared queue"""
        try:
            await supabase_client.table('url_queue')\
                .update({'status': 'completed', 'completed_at': int(time.time())})\
                .in_('url', urls)\
                .execute()
        except Exception as e:
            logger.error(f"Failed to mark URLs completed: {str(e)}")

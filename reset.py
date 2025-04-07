import redis
import os

redis_client = redis.Redis(
    host=os.environ['REDIS_HOST'],
    port=os.environ['REDIS_PORT'],
    password=os.environ['REDIS_PASSWORD'],
    ssl=True,
    decode_responses=True
)

redis_client.delete('processed_urls')
redis_client.delete('processed_images')
print("✅ Cleared Redis sets.")

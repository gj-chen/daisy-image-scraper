import redis
import json
import os

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    ssl=True,
    decode_responses=True
)

queue_name = 'url_queue'
queue_length = redis_client.llen(queue_name)

print(f"\n[redis] Queue '{queue_name}' has {queue_length} item(s)\n")

if queue_length > 0:
    for i in range(queue_length):
        item = redis_client.lindex(queue_name, i)
        try:
            decoded = json.loads(item)
            print(f"  {i+1}. {decoded}")
        except:
            print(f"  {i+1}. {item}")
else:
    print("Queue is empty.")
from scraper.celery_app import app
import uuid
import socket
import time
import threading
import os
import redis

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    password=os.getenv("REDIS_PASSWORD"),
    ssl=True,
    decode_responses=True
)

def monitor_and_shutdown():
    while True:
        queue_len = redis_client.llen('url_queue')
        active_threads = threading.active_count() - 1

        print(f"[monitor] Queue length: {queue_len}, Active threads: {active_threads}")

        if queue_len == 0 and active_threads == 0:
            print("[monitor] All tasks done. Shutting down worker.")
            os._exit(0)

        time.sleep(15)

threading.Thread(target=monitor_and_shutdown, daemon=True).start()

if __name__ == '__main__':
    # Generate unique worker name using UUID and hostname
    unique_id = str(uuid.uuid4())[:8]
    hostname = socket.gethostname()
    worker_name = f"celery@worker-{unique_id}-{hostname}"

    app.worker_main(argv=[
        "worker",
        f"-n={worker_name}",
        "--loglevel=info",
        "--concurrency=4"
    ])
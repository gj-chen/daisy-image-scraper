import os
import hashlib
import json
import openai
import redis

# Redis setup for deduplication cache
redis_client = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=os.environ["REDIS_PORT"],
    password=os.environ["REDIS_PASSWORD"],
    ssl=True,
    decode_responses=True
)

def get_cached_openai_response(prompt: str, model="gpt-4-0125-preview") -> dict:
    prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
    cache_key = f"openai_cache:{prompt_hash}"

    cached = redis_client.get(cache_key)
    if cached:
        print(f"[openai-cache] ✅ Cache hit for key {cache_key}")
        return json.loads(cached)

    print(f"[openai-cache] ❌ Cache miss. Calling OpenAI.")
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You're a fashion stylist analyzing this page. Give a brief high-level style summary for the content below."},
            {"role": "user", "content": prompt}
        ]
    )

    redis_client.set(cache_key, json.dumps(response), ex=86400)  # cache for 1 day
    return response

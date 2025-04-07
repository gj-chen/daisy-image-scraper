import os
import json
import time
import requests
import logging
from openai import OpenAI
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

def clean_image_url(image_url):
    parsed = urlparse(image_url)
    return urlunparse(parsed._replace(query=""))

def is_valid_image_url(image_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(image_url, headers=headers, timeout=10)
        return response.status_code == 200 and "image" in response.headers.get("Content-Type", "")
    except Exception as e:
        logger.warning(f"[WARN] Error validating image URL: {image_url} — {str(e)}")
        return False

def build_prompt(image_context):
    return f"""
You are an expert AI assistant specialized in fashion product metadata extraction.
Your task is to produce detailed structured fashion metadata specific to exactly one image provided, based solely on explicitly given image context.

CRITICAL RULES:
- DO NOT REPEAT OR COPY METADATA FROM OTHER IMAGES.
- Clearly list all attributes explicitly visible or inferable from the provided context.
- Freely use accurate, natural fashion terms (e.g., linen, cotton, suede) without constraining yourself to given examples.
- Explicitly return empty values ("", []) if unable to determine attributes clearly from provided context.

Provided Image Context:
- Image URL: {image_context['image_url']}
- ALT Text: {image_context['alt_text']}
- Page/Product Title: {image_context['title']}
- Surrounding Text Snippet: {image_context['surrounding_text']}

Respond exactly following this JSON schema:
{{
  "product_info": {{
    "brand": "",
    "brand_tier": "",
    "price_range": "",
    "availability": "",
    "shopping_url": ""
  }},
  "fashion_attributes": {{
    "item_category": "",
    "clothing_subtype": [],
    "fabric_material": [],
    "texture": [],
    "fit": [],
    "silhouette": [],
    "pattern": [],
    "length": [],
    "sleeve_type": []
  }},
  "style_context": {{
    "celebrity_inspo": [],
    "style_archetype": [],
    "vibe_emotion": []
  }},
  "occasion_context": {{
    "event_type": [],
    "seasonality": [],
    "climate": []
  }},
  "body_fit": {{
    "body_shape_suitability": [],
    "body_feature_focus": []
  }}
}}

Double-check carefully BEFORE responding:
- Only provided context explicitly considered.
- No generalized or inferred assumptions made.
- Multiple relevant attributes explicitly included if applicable.
"""

def generate_gpt_structured_metadata_sync(image_context, retries=3, timeout=60):
    raw_url = image_context["image_url"]
    cleaned_url = clean_image_url(raw_url)

    if not is_valid_image_url(cleaned_url):
        logger.warning(f"[SKIP] Invalid or inaccessible image URL for OpenAI: {cleaned_url}")
        return None

    prompt = build_prompt({**image_context, "image_url": cleaned_url})

    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": cleaned_url}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                max_tokens=800,
                response_format="json",
                timeout=timeout
            )

            structured_metadata = response.choices[0].message.content
            logger.info(f"[✅ GPT] Metadata success for: {cleaned_url}")
            return json.loads(structured_metadata)

        except (requests.Timeout, requests.ConnectionError) as e:
            logger.warning(f"[RETRY {attempt}/{retries}] Temporary network error: {str(e)}")
            if attempt < retries:
                time.sleep(attempt * 2)  # exponential backoff
                continue
        except Exception as e:
            logger.error(f"[❌ GPT ERROR] {str(e)} — for image: {cleaned_url}")
            break

    return None

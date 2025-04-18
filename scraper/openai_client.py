import os
import json
import time
import base64
import logging
import mimetypes
from openai import OpenAI

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


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


def image_bytes_to_data_url(image_bytes, original_url):
    mime_type = mimetypes.guess_type(original_url)[0] or "image/jpeg"
    base64_data = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{base64_data}"


def is_meaningful_metadata(metadata: dict) -> bool:
    if not metadata:
        return False

    def has_value(obj):
        if isinstance(obj, dict):
            return any(has_value(v) for v in obj.values())
        if isinstance(obj, list):
            return any(bool(v.strip() if isinstance(v, str) else v) for v in obj)
        if isinstance(obj, str):
            return bool(obj.strip())
        return bool(obj)

    return has_value(metadata)


def generate_gpt_structured_metadata_sync(image_context, image_bytes, retries=3, timeout=60):
    try:
        prompt = build_prompt(image_context)
        data_url = image_bytes_to_data_url(image_bytes, image_context["image_url"])

        for attempt in range(1, retries + 1):
            try:
                response = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": data_url}},
                                {"type": "text", "text": prompt}
                            ]
                        }
                    ],
                    max_tokens=800,
                    timeout=timeout
                )

                structured_metadata = response.choices[0].message.content
                
                if not structured_metadata.strip().startswith("{"):
                    logger.warning(f"[SKIP] GPT returned non-JSON content for: {image_context['image_url']}")
                    return None
                    
                logger.info(f"[✅ GPT] Metadata success for: {image_context['image_url']}")
                return json.loads(structured_metadata)

            except Exception as e:
                logger.warning(f"[RETRY {attempt}/{retries}] GPT error for image {image_context['image_url']}: {str(e)}")
                if attempt < retries:
                    time.sleep(attempt * 2)
                    continue
                break

    except Exception as e:
        logger.error(f"[❌ GPT ERROR] {str(e)} for image: {image_context['image_url']}")

    return None


def summarize_metadata_for_embedding(metadata: dict) -> str:
    """Converts structured metadata into a natural language summary."""
    try:
        parts = []

        brand = metadata["product_info"].get("brand")
        if brand:
            parts.append(f"from {brand}")

        category = metadata["fashion_attributes"].get("item_category")
        subtype = metadata["fashion_attributes"].get("clothing_subtype", [])
        if category:
            subtypes = ", ".join(subtype) if subtype else ""
            parts.append(f"{category} {subtypes}".strip())

        materials = metadata["fashion_attributes"].get("fabric_material", [])
        if materials:
            parts.append(f"made of {', '.join(materials)}")

        pattern = metadata["fashion_attributes"].get("pattern", [])
        if pattern:
            parts.append(f"with {', '.join(pattern)} pattern")

        vibe = metadata["style_context"].get("vibe_emotion", [])
        if vibe:
            parts.append(f"evoking a {', '.join(vibe)} vibe")

        occasions = metadata["occasion_context"].get("event_type", [])
        if occasions:
            parts.append(f"suitable for {', '.join(occasions)}")

        return " ".join(parts).strip()
    except Exception:
        return ""


def generate_embedding_from_text(text: str):
    if not text:
        return None

    try:
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"[❌ EMBEDDING ERROR] Failed to generate embedding: {e}")
        return None

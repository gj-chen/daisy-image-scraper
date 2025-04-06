from openai import OpenAI
import json
import logging
import os

logger = logging.getLogger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_gpt_structured_metadata_sync(image_context, retries=3, timeout=60):
    prompt = build_prompt(image_context)

    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                response_format={"type": "json_object"},
                messages=[{"role": "system", "content": prompt}],
                timeout=120,  # Increased timeout
                request_timeout=120  # Increased request timeout
            )
            structured_metadata = response.choices[0].message.content
            logger.info(f"GPT metadata success for: {image_context['image_url']}")
            return json.loads(structured_metadata)
        except (openai.APITimeoutError, openai.APIConnectionError) as e:
            logger.warning(f"Temporary error (attempt {attempt}/{retries}): {str(e)}")
            if attempt < retries:
                import time
                time.sleep(attempt * 2)  # Exponential backoff
                continue
        except Exception as e:
            logger.error(f"GPT metadata error: {str(e)}")
            break
    
    logger.error(f"All attempts failed for image: {image_context['image_url']}")
    return None

def generate_embedding_sync(metadata):
    try:
        response = client.embeddings.create(
            input=json.dumps(metadata),
            model="text-embedding-ada-002"
        )
        embedding_vector = response.data[0].embedding
        logger.info("Embedding generated successfully.")
        return embedding_vector
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        return []

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

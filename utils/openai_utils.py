import openai
import json
import logging
import time

logger = logging.getLogger(__name__)

def generate_gpt_structured_metadata(image_context, retries=3, timeout=30):
    prompt = build_prompt(image_context)

    for attempt in range(1, retries + 1):
        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": prompt}
                ],
                timeout=timeout
            )
            structured_metadata = response.choices[0].message.content
            parsed_metadata = json.loads(structured_metadata)
            logger.info(f"Structured metadata generated successfully for image: {image_context['image_url']}")
            return parsed_metadata
        except Exception as e:
            logger.error(f"GPT metadata generation error (attempt {attempt}/{retries}) for {image_context['image_url']}: {str(e)}")
            if attempt < retries:
                time.sleep(2 ** attempt)  # exponential backoff
            else:
                logger.error(f"All retries exhausted for GPT call on image: {image_context['image_url']}")
    return None

def build_prompt(image_context):
    return f"""
You are an expert AI assistant specialized in fashion product metadata extraction.  
Your task is to produce detailed structured fashion metadata specific to exactly one image provided, based solely on explicitly given image context.

CRITICAL RULES:
- DO NOT REPEAT OR COPY METADATA FROM OTHER IMAGES.
- Multiple attributes can apply simultaneously.
- Use natural, precise descriptive terms freely; do not constrain yourself to examples.
- If uncertain or unable to determine from context, return empty values ("", []).

Provided Image Context:
- URL: {image_context['image_url']}
- ALT Text: {image_context['alt_text']}
- Page/Product Title: {image_context['title']}
- Surrounding Text Snippet: {image_context['surrounding_text']}

Respond with this JSON structure exactly:
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

Double-check accuracy before submitting:
- Metadata is strictly derived from provided context only.
- No generalized assumptions made.
- Multiple correct attributes explicitly included if relevant.
"""

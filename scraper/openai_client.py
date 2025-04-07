from openai import OpenAI
import os

# Initialize OpenAI client (v1.3+ style)
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

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

def analyze_image_with_openai(image_context):
    try:
        prompt = build_prompt(image_context)
        image_url = image_context["image_url"]

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": prompt}
                    ]
                }
            ],
            max_tokens=800
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"[ERROR] OpenAI failed: {e}")
        return None

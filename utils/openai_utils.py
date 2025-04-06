import json
import logging
import re
from openai import OpenAI
from config import OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)
client = OpenAI(api_key=OPENAI_API_KEY)

def clean_gpt_response(raw_text):
    # Remove Markdown code block
    cleaned = re.sub(r'```(?:json)?', '', raw_text).strip()

    # Remove semicolons and ensure proper commas
    cleaned = cleaned.replace(';', ',')

    # Remove potential trailing commas (before } or ])
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)

    return cleaned

def generate_gpt_structured_metadata(scraped_content):
    prompt = f"""
    You are an expert fashion stylist AI. Given the following scraped content from a fashion website:

    Title: {scraped_content['title']}
    Description: {scraped_content['description']}
    Content Summary: {scraped_content['content_summary']}
    Image Context: {scraped_content['image_context']}

    Generate structured JSON metadata describing the product, fashion attributes, style context, occasion context, and body fit suitability, following exactly this schema:

    {{
      "product_info": {{
        "brand": "",
        "brand_tier": "",
        "price_range": "",
        "availability": "in_stock",
        "shopping_url": ""
      }},
      "fashion_attributes": {{
        "item_category": "",
        "clothing_subtype": "",
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

    Fill out all fields accurately and briefly, based on provided content. Respond ONLY with valid JSON object (no markdown, no extra text).
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )

    raw_content = response.choices[0].message.content.strip()

    logging.info(f"Raw GPT response before cleaning: {raw_content}")

    # Explicitly clean GPT response
    cleaned_response = clean_gpt_response(raw_content)

    logging.info(f"Cleaned GPT response: {cleaned_response}")

    try:
        structured_metadata = json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding error: {e}")
        logging.error(f"Cleaned GPT response: {cleaned_response}")
        raise Exception(f"Failed to parse cleaned JSON: {e}")

    return structured_metadata

def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

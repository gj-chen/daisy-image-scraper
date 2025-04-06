import json
import logging
from openai import OpenAI
from config import OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)
client = OpenAI(api_key=OPENAI_API_KEY)

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

    Fill out all fields accurately and briefly, based on provided content. Respond ONLY with the JSON object.
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )

    raw_content = response.choices[0].message.content.strip()

    # Explicit logging to debug response
    logging.info(f"GPT Response: {raw_content}")

    try:
        structured_metadata = json.loads(raw_content)
    except json.JSONDecodeError as e:
        logging.error(f"JSON decoding error: {e}")
        logging.error(f"Raw GPT response: {raw_content}")
        raise Exception(f"Failed to parse JSON from GPT response: {e}")

    return structured_metadata

def get_embedding(text):
    response = client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding
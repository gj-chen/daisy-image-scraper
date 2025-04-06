import openai
import json

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

    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )

    structured_metadata = json.loads(response.choices[0].message.content)
    return structured_metadata

# Your existing embedding function (unchanged)
def get_embedding(text):
    response = openai.Embedding.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return response["data"][0]["embedding"]

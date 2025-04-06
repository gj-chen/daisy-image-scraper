# scraper/metadata_generator.py
from openai import OpenAI
from config import OPENAI_API_KEY

openai = OpenAI(api_key=OPENAI_API_KEY)

PROMPT = """
You are a highly experienced fashion stylist analyzing the provided fashion image and the accompanying context (captions, paragraphs, article titles). 

Your task is to carefully analyze and thoughtfully describe this fashion item as if you're recommending it to a fashion-conscious client. Provide a detailed, rich, and nuanced description of the fashion item, including the following dimensions clearly and naturally embedded within your response:

- Clearly identify the clothing type and describe its key characteristics.
- Analyze the visual details, describing the style, silhouette, fit, textures, and materials intuitively. Mention distinctive or notable aspects explicitly.
- Describe the color palette naturally, highlighting prominent colors and their aesthetic impact.
- Discuss the intended vibe, mood, and stylistic impression of the item (e.g., romantic elegance, edgy confidence, minimalist chic).
- Clearly mention suitable occasions, events, or contexts where this fashion item would be most appropriate.
- Naturally suggest the type of wearer this piece would flatter, mentioning body shapes or specific body features if clearly relevant.
- If the item resonates clearly with a celebrity or well-known stylist's signature style, explicitly mention these stylistic inspirations and briefly explain why.
- Suggest ideal seasonal or climate conditions for wearing this item comfortably.

Please avoid forcing attributes into categories if they aren't clearly applicable. Instead, focus on providing intuitive, authentic, and rich stylistic insight.

After your thoughtful analysis, clearly summarize your insights into the following structured JSON format. If a certain field is not clearly applicable, simply leave it as an empty array ([]):

{
  "clothing_type": "...",
  "style_description": "...",  // Natural description
  "item_details": {
    "fabric_material": ["..."], // if identifiable
    "texture": ["..."], // if clearly relevant
    "fit": ["..."], // intuitive description if relevant
    "silhouette": ["..."], // naturally inferred
    "pattern": ["..."], // notable patterns if present
    "length": ["..."], // clearly visible
    "sleeve_type": ["..."] // if applicable
  },
  "color_palette": ["..."], // dominant, clearly described colors
  "occasion_suitability": ["..."], // clearly suggested contexts
  "seasonality_climate": ["..."], // clearly intuitive suggestions
  "style_emotion_vibe": ["..."], // stylistically rich descriptions
  "celebrity_inspiration": ["..."], // naturally mentioned, if applicable
  "body_shape_suitability": ["..."], // intuitive recommendation
  "body_feature_focus": ["..."] // clearly recommended focus points
}

Your analysis should be precise, insightful, nuanced, and stylistically authoritative, as if genuinely advising a client.

"""

class MetadataGenerator:
    @staticmethod
    def has_text_overlay(image_url):
        response = openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user", 
                "content": [
                    {"type": "text", "text": "Does this image have any text overlaid on it? Answer only 'yes' or 'no'."},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }],
            max_tokens=10,
            temperature=0
        )
        return 'yes' in response.choices[0].message.content.lower()

    @staticmethod
    def generate(image_url, context_text):
        # First check for text overlay
        if MetadataGenerator.has_text_overlay(image_url):
            logger.info(f"Skipping image with text overlay: {image_url}")
            return None
            
        response = openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT + "\n\nContext:\n" + context_text},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }],
            max_tokens=800,
            temperature=0.2,
        )
        metadata = response.choices[0].message.content
        return metadata  # JSON string clearly structured

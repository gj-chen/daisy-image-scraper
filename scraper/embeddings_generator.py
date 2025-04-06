# scraper/embeddings_generator.py
from openai import OpenAI
from config import OPENAI_API_KEY
import json

openai = OpenAI(api_key=OPENAI_API_KEY)

class EmbeddingsGenerator:
    @staticmethod
    def generate(metadata_json):
        metadata_dict = json.loads(metadata_json)
        metadata_str = ', '.join([
            metadata_dict.get("clothing_type", ""),
            ', '.join(sum(metadata_dict.get("item_details", {}).values(), [])),
            ', '.join(metadata_dict.get("color_palette", [])),
            ', '.join(metadata_dict.get("occasion_suitability", [])),
            ', '.join(metadata_dict.get("style_emotion_vibe", [])),
            ', '.join(metadata_dict.get("celebrity_inspiration", [])),
            ', '.join(metadata_dict.get("body_shape_suitability", [])),
        ])

        response = openai.embeddings.create(
            input=metadata_str,
            model="text-embedding-3-small"
        )

        return response.data[0].embedding

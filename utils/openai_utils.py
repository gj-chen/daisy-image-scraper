import openai
import os
import json
import logging

logger = logging.getLogger(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_gpt_structured_metadata_sync(image_context):
    prompt = build_prompt(image_context)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": prompt}],
            timeout=20
        )
        structured_metadata = response.choices[0].message.content
        return json.loads(structured_metadata)
    except Exception as e:
        logger.error(f"GPT metadata error: {str(e)}")
        return None

def build_prompt(image_context):
    return f"""
You are an expert AI assistant specialized in fashion product metadata extraction.  
Produce structured fashion metadata specific to the provided image context.

Provided Image Context:
- URL: {image_context['image_url']}
- ALT Text: {image_context['alt_text']}
- Title: {image_context['title']}
- Surrounding Text: {image_context['surrounding_text']}

Respond using the exact JSON structure provided previously.
"""

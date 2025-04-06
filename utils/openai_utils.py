from openai import AsyncOpenAI
import json
import logging

logger = logging.getLogger(__name__)
openai_client = AsyncOpenAI()

async def generate_gpt_structured_metadata_async(image_context, retries=3):
    prompt = build_prompt(image_context)
    for attempt in range(retries):
        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4-turbo",
                response_format={"type": "json_object"},
                messages=[{"role": "system", "content": prompt}],
                timeout=20
            )
            structured_metadata = response.choices[0].message.content
            logger.info(f"GPT metadata generated for: {image_context['image_url']}")
            return json.loads(structured_metadata)
        except Exception as e:
            logger.error(f"GPT metadata attempt {attempt+1}/{retries} failed: {str(e)}")
    return None

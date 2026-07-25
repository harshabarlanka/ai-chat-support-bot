import json
import logging
import time

from google import genai
from google.genai.errors import ClientError, ServerError

from app.config import settings

logger = logging.getLogger(__name__)

_client = genai.Client(api_key=settings.gemini_api_key)

EXTRACTION_SYSTEM_INSTRUCTION = (
    "You extract entities and relationships from text for a knowledge graph. "
    "Respond ONLY with valid JSON, no markdown formatting, no explanation. "
    'Format: {"entities": [{"name": "...", "type": "..."}], '
    '"relationships": [{"source": "...", "target": "...", "type": "..."}]}. '
    "Entity types should be simple nouns (Person, Organization, Concept, Product, "
    "Location, etc). Relationship types should be short verb phrases (WORKS_FOR, "
    "MANAGES, DEPENDS_ON, LOCATED_IN, etc). If no clear entities exist, return "
    'empty lists: {"entities": [], "relationships": []}.'
)

MAX_RETRIES = 3
RETRYABLE_STATUS_CODES = {429, 503}


RETRYABLE_STATUSES = {"RESOURCE_EXHAUSTED", "UNAVAILABLE"}


def extract_entities_and_relationships(text: str) -> dict:
    response = None

    for attempt in range(MAX_RETRIES):
        try:
            response = _client.models.generate_content(
                model=settings.gemini_chat_model,
                contents=text,
                config={"system_instruction": EXTRACTION_SYSTEM_INSTRUCTION},
            )
            break
        except (ClientError, ServerError) as e:
            status = getattr(e, "status", None)
            is_retryable = status in RETRYABLE_STATUSES
            logger.warning("Gemini extraction attempt %d failed (status=%s): %s", attempt + 1, status, e)
            if is_retryable and attempt < MAX_RETRIES - 1:
                time.sleep(15)
                continue
            logger.error("Gemini extraction gave up after %d attempts", attempt + 1)
            return {"entities": [], "relationships": []}

    if response is None:
        return {"entities": [], "relationships": []}

    try:
        cleaned = response.text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(cleaned)
        result = {
            "entities": data.get("entities", []),
            "relationships": data.get("relationships", []),
        }
        logger.info("Extracted %d entities, %d relationships", len(result["entities"]), len(result["relationships"]))
        return result
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error("Failed to parse extraction JSON: %s | raw response: %s", e, response.text[:200])
        return {"entities": [], "relationships": []}
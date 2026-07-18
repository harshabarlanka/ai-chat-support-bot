from google import genai
from google.genai import types

from app.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)

EMBEDDING_DIMENSIONS = 768


def generate_embedding(text: str) -> list[float]:
    """Generate a 768-dimension embedding vector for a piece of text using Gemini."""
    response = _client.models.embed_content(
        model=settings.gemini_embedding_model,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
    )
    return response.embeddings[0].values
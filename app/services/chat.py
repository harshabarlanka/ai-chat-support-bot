from google import genai

from app.config import settings
from app.models.chunk import Chunk

_client = genai.Client(api_key=settings.gemini_api_key)
 
SYSTEM_INSTRUCTION = (
    "You are a helpful assistant that answers questions based only on the "
    "provided document excerpts. If the answer isn't contained in the "
    "excerpts, say you don't have enough information to answer — do not "
    "make up an answer."
)

def build_prompt(question: str, chunks: list[Chunk]) -> str:
    if not chunks:
        context = "No relevant document excerpts were found."
    else:
        context = "\n\n".join(
            f"[Excerpt {i+1}]\n{chunk.content}" for i, chunk in enumerate(chunks)
        )
    
    return (
        f"Document excerpts:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer the question using only the excerpts above."
    )

def generate_answer(question: str, chunks: list[Chunk]) -> str:
    prompt = build_prompt(question,chunks)
    response = _client.models.generate_content(
        model=settings.gemini_chat_model,
        contents=prompt,
        config={"system_instruction": SYSTEM_INSTRUCTION},
    )
    return response.text

def generate_answer_stream(question: str, chunks: list[Chunk]):
    prompt = build_prompt(question, chunks)
    stream = _client.models._generate_content_stream(
        model = settings.gemini_chat_model,
        contents=prompt,
        config={"system_instruction": SYSTEM_INSTRUCTION}
    )
    for event in stream:
        if event.text:
            yield event.text
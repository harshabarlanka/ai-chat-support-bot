from google import genai

from app.config import settings
from app.models.chat_message import ChatMessage

_client = genai.Client(api_key=settings.gemini_api_key)

REWRITE_SYSTEM_INSTRUCTION = (
    "You rewrite a user's latest chat message into a fully standalone question, "
    "using the conversation history for context. If the latest message is already "
    "standalone and doesn't depend on prior context, return it unchanged. "
    "Output only the rewritten question, nothing else — no explanation, no quotes."
)

MAX_HISTORY_MESSAGES = 6


def format_history(messages: list[ChatMessage]) -> str:
    """Render recent messages as plain text, oldest first, for use in a prompt."""
    recent = messages[-MAX_HISTORY_MESSAGES:]
    lines = [f"{msg.role}: {msg.content}" for msg in recent]
    return "\n".join(lines)


def rewrite_query(question: str, history: list[ChatMessage]) -> str:
    """
    Rewrite a possibly context-dependent question into a standalone one,
    using recent conversation history. Falls back to the original question
    if there's no history yet (first message in a session).
    """
    if not history:
        return question

    history_text = format_history(history)
    prompt = (
        f"Conversation so far:\n{history_text}\n\n"
        f"Latest message: {question}\n\n"
        "Rewrite the latest message as a standalone question."
    )

    response = _client.models.generate_content(
        model=settings.gemini_chat_model,
        contents=prompt,
        config={"system_instruction": REWRITE_SYSTEM_INSTRUCTION},
    )
    return response.text.strip()
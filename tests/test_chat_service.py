from app.models.chunk import Chunk
from app.services.chat import build_prompt


def make_chunk(content: str, index: int = 0):
    return Chunk(chunk_index=index, content=content)


def test_build_prompt_includes_all_chunks():
    chunks = [make_chunk("First excerpt content"), make_chunk("Second excerpt content", 1)]
    prompt = build_prompt("What is this about?", chunks)

    assert "First excerpt content" in prompt
    assert "Second excerpt content" in prompt
    assert "What is this about?" in prompt


def test_build_prompt_handles_no_chunks():
    prompt = build_prompt("Any question", [])

    assert "No relevant document excerpts were found" in prompt
    assert "Any question" in prompt
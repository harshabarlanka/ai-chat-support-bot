import pytest

from app.services.chunking import chunk_text


def test_chunk_text_basic_splitting():
    text = "a" * 2500
    chunks = chunk_text(text, chunk_size=1000, overlap=150)

    assert len(chunks) == 3
    assert all(len(c) <= 1000 for c in chunks)


def test_chunk_text_overlap_is_correct():
    text = "0123456789" * 250  # 2500 chars
    chunks = chunk_text(text, chunk_size=1000, overlap=150)

    # last 150 chars of chunk 1 should match first 150 chars of chunk 2
    assert chunks[0][-150:] == chunks[1][:150]


def test_chunk_text_empty_string_returns_empty_list():
    assert chunk_text("") == []


def test_chunk_text_shorter_than_chunk_size_returns_one_chunk():
    text = "short text"
    chunks = chunk_text(text, chunk_size=1000, overlap=150)

    assert len(chunks) == 1
    assert chunks[0] == "short text"


def test_chunk_text_overlap_larger_than_chunk_size_raises():
    with pytest.raises(ValueError):
        chunk_text("some text", chunk_size=100, overlap=150)


def test_chunk_text_whitespace_only_returns_empty_list():
    assert chunk_text("   \n\n   ") == []
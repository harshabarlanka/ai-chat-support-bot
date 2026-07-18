def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    """
    Split text into overlapping chunks by character count.

    Each chunk is `chunk_size` characters, and consecutive chunks overlap
    by `overlap` characters so that context isn't lost at chunk boundaries.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks
import io

from pypdf import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract all text from a PDF's raw bytes, page by page, in order."""
    reader = PdfReader(io.BytesIO(file_bytes))

    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)

    return "\n".join(pages_text)
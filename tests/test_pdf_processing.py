from pathlib import Path

from app.services.pdf_processing import extract_text_from_pdf

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_extract_text_from_pdf_with_real_text():
    pdf_bytes = (FIXTURES_DIR / "sample.pdf").read_bytes()
    text = extract_text_from_pdf(pdf_bytes)

    assert "This is a test PDF document." in text
    assert "multiple lines of real text" in text


def test_extract_text_from_blank_pdf_returns_empty_string():
    pdf_bytes = (FIXTURES_DIR / "blank.pdf").read_bytes()
    text = extract_text_from_pdf(pdf_bytes)

    assert text == ""
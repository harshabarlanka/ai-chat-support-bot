import uuid
from unittest.mock import patch

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.user import User
from app.security import hash_password
from app.services.document_processing import process_document
from tests.conftest import TestingSessionLocal


def make_test_user_and_document(db):
    user = User(id=uuid.uuid4(), email=f"{uuid.uuid4()}@example.com", hashed_password=hash_password("pw"))
    db.add(user)
    db.commit()

    document = Document(
        id=uuid.uuid4(),
        owner_id=user.id,
        filename="test.pdf",
        s3_key="documents/test/test.pdf",
        status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@patch("app.services.document_processing.generate_embedding")
@patch("app.services.document_processing.extract_text_from_pdf")
@patch("app.services.document_processing.download_file_from_s3")
def test_process_document_success(mock_download, mock_extract, mock_embed, db_session):
    document = make_test_user_and_document(db_session)

    mock_download.return_value = b"%PDF-1.4 fake bytes"
    mock_extract.return_value = "a" * 2500  # long enough to produce multiple chunks
    mock_embed.return_value = [0.1] * 768

    process_document(document.id, session_factory=TestingSessionLocal)

    db_session.refresh(document)
    assert document.status == "ready"

    chunks = db_session.query(Chunk).filter(Chunk.document_id == document.id).all()
    assert len(chunks) == 3
    mock_embed.assert_called()


@patch("app.services.document_processing.download_file_from_s3")
def test_process_document_marks_failed_on_error(mock_download, db_session):
    document = make_test_user_and_document(db_session)

    mock_download.side_effect = Exception("S3 is down")

    process_document(document.id, session_factory=TestingSessionLocal)

    db_session.refresh(document)
    assert document.status == "failed"
import logging
import uuid

from sqlalchemy.orm import Session, sessionmaker

from app.database import SessionLocal
from app.models.chunk import Chunk
from app.models.document import Document
from app.services.chunking import chunk_text
from app.services.embeddings import generate_embedding
from app.services.pdf_processing import extract_text_from_pdf
from app.storage import download_file_from_s3

logger = logging.getLogger(__name__)


def process_document(document_id: uuid.UUID, session_factory: sessionmaker = SessionLocal) -> None:
    """
    Background task: download the PDF from S3, extract text, chunk it,
    generate an embedding per chunk, and store everything. Updates the
    document's status to 'ready' on success or 'failed' on any error.

    `session_factory` defaults to the app's real SessionLocal, but can be
    overridden in tests to point at the test database instead.
    """
    db: Session = session_factory()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if document is None:
            logger.error("Document %s not found for processing", document_id)
            return

        document.status = "processing"
        db.commit()

        file_bytes = download_file_from_s3(document.s3_key)
        text = extract_text_from_pdf(file_bytes)
        chunks = chunk_text(text)

        for index, chunk_content in enumerate(chunks):
            embedding = generate_embedding(chunk_content)
            db.add(
                Chunk(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk_content,
                    embedding=embedding,
                )
            )

        document.status = "ready"
        db.commit()
        logger.info("Document %s processed successfully: %d chunks", document_id, len(chunks))

    except Exception:
        logger.exception("Failed to process document %s", document_id)
        db.rollback()
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = "failed"
            db.commit()

    finally:
        db.close()
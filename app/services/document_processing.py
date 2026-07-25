import logging
import time
import uuid

from sqlalchemy.orm import Session, sessionmaker

from app.database import SessionLocal
from app.graph_database import get_graph_driver
from app.models.chunk import Chunk
from app.models.document import Document
from app.services.chunking import chunk_text
from app.services.embeddings import generate_embedding
from app.services.graph_extraction import extract_entities_and_relationships
from app.services.graph_store import store_chunk_graph
from app.services.pdf_processing import extract_text_from_pdf
from app.storage import download_file_from_s3

logger = logging.getLogger(__name__)


def process_document(document_id: uuid.UUID, session_factory: sessionmaker = SessionLocal) -> None:
    """
    Background task: download the PDF from S3, extract text, chunk it,
    generate an embedding per chunk, store everything in Postgres, and
    additionally extract entities/relationships per chunk into Neo4j for
    graph-based retrieval. Updates the document's status to 'ready' on
    success or 'failed' on any error.

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

        graph_driver = get_graph_driver()

        for index, chunk_content in enumerate(chunks):
            embedding = generate_embedding(chunk_content)
            chunk_id = uuid.uuid4()

            db.add(
                Chunk(
                    id=chunk_id,
                    document_id=document.id,
                    chunk_index=index,
                    content=chunk_content,
                    embedding=embedding,
                )
            )

            extraction = extract_entities_and_relationships(chunk_content)
            store_chunk_graph(graph_driver, document.id, chunk_id, extraction)
            time.sleep(5)  # was 2 — give more breathing room given observed 429s and 503s

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
import uuid
from sqlalchemy.orm import Session
from app.models.chunk import Chunk
from app.models.document import Document
from app.services.embeddings import generate_embedding

DEFAULT_TOP_K = 5

def retrieve_relevant_chunks(
        db: Session, user_id: uuid.UUID, query: str, top_k: int = DEFAULT_TOP_K
) -> list[Chunk]:
    query_embedding = generate_embedding(query)

    return (
        db.query(Chunk)
        .join(Document, Chunk.document_id == Document.id)
        .filter(Document.owner_id == user_id)
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
        .all()
    )
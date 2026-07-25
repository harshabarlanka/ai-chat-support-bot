import uuid

from neo4j import Driver
from sqlalchemy.orm import Session

from app.graph_database import get_graph_driver
from app.models.chunk import Chunk
from app.models.document import Document


def find_related_chunk_ids(driver: Driver, question: str, max_hops: int = 2) -> list[str]:
    """
    Naive entity matching: find any Entity whose name appears as a substring
    of the question, then traverse up to max_hops relationships outward,
    collecting every Chunk connected to any entity found along the way.
    """
    with driver.session() as session:
        result = session.run(
            """
            MATCH (e:Entity)
            WHERE toLower($question) CONTAINS toLower(e.name)
            MATCH (e)-[:RELATES_TO*0..%d]-(related:Entity)
            MATCH (related)-[:MENTIONED_IN]->(c:Chunk)
            RETURN DISTINCT c.id AS chunk_id
            """
            % max_hops,
            question=question,
        )
        return [record["chunk_id"] for record in result]


def retrieve_relevant_chunks_via_graph(
    db: Session, user_id: uuid.UUID, question: str
) -> list[Chunk]:
    """
    Graph-based retrieval: find entities mentioned in the question, traverse
    their relationships, and return the actual Chunk rows (from Postgres)
    those connected entities were mentioned in — scoped to the user's own
    documents, same as the vector retrieval path.
    """
    driver = get_graph_driver()
    chunk_ids = find_related_chunk_ids(driver, question)

    if not chunk_ids:
        return []

    return (
        db.query(Chunk)
        .join(Document, Chunk.document_id == Document.id)
        .filter(Document.owner_id == user_id, Chunk.id.in_([uuid.UUID(cid) for cid in chunk_ids]))
        .all()
    )
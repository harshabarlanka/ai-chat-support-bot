import uuid
from unittest.mock import patch

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.user import User
from app.security import hash_password
from app.services.retrieval import retrieve_relevant_chunks


def make_user(db, email):
    user = User(id=uuid.uuid4(), email=email, hashed_password=hash_password("pw"))
    db.add(user)
    db.commit()
    return user


def make_document_with_chunk(db, owner_id, content, embedding):
    document = Document(
        id=uuid.uuid4(),
        owner_id=owner_id,
        filename="test.pdf",
        s3_key=f"documents/test/{uuid.uuid4()}.pdf",
        status="ready",
    )
    db.add(document)
    db.commit()

    chunk = Chunk(
        id=uuid.uuid4(),
        document_id=document.id,
        chunk_index=0,
        content=content,
        embedding=embedding,
    )
    db.add(chunk)
    db.commit()
    return document, chunk


@patch("app.services.retrieval.generate_embedding")
def test_retrieve_returns_only_own_documents(mock_embed, db_session):
    user_a = make_user(db_session, "usera@example.com")
    user_b = make_user(db_session, "userb@example.com")

    _, chunk_a = make_document_with_chunk(
        db_session, user_a.id, "Content belonging to user A", [0.1] * 768
    )
    make_document_with_chunk(db_session, user_b.id, "Content belonging to user B", [0.9] * 768)

    mock_embed.return_value = [0.1] * 768  # closest to chunk_a's embedding

    results = retrieve_relevant_chunks(db=db_session, user_id=user_a.id, query="anything")

    assert len(results) == 1
    assert results[0].id == chunk_a.id


@patch("app.services.retrieval.generate_embedding")
def test_retrieve_respects_top_k(mock_embed, db_session):
    user = make_user(db_session, "topk@example.com")

    for i in range(10):
        make_document_with_chunk(db_session, user.id, f"Chunk number {i}", [float(i)] * 768)

    mock_embed.return_value = [0.0] * 768

    results = retrieve_relevant_chunks(db=db_session, user_id=user.id, query="anything", top_k=3)

    assert len(results) == 3
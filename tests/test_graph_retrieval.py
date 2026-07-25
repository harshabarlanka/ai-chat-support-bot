import uuid
from unittest.mock import MagicMock, patch

from app.models.document import Document
from app.models.chunk import Chunk
from app.models.user import User
from app.security import hash_password
from app.services.graph_retrieval import retrieve_relevant_chunks_via_graph


@patch("app.services.graph_retrieval.get_graph_driver")
def test_retrieve_via_graph_returns_matching_chunks(mock_get_driver, db_session):
    user = User(id=uuid.uuid4(), email="graph@example.com", hashed_password=hash_password("pw"))
    db_session.add(user)
    db_session.commit()

    document = Document(
        id=uuid.uuid4(), owner_id=user.id, filename="test.pdf",
        s3_key="documents/test/test.pdf", status="ready",
    )
    db_session.add(document)
    db_session.commit()

    chunk = Chunk(
        id=uuid.uuid4(), document_id=document.id, chunk_index=0,
        content="Relevant chunk content", embedding=[0.1] * 768,
    )
    db_session.add(chunk)
    db_session.commit()

    mock_session = MagicMock()
    mock_session.run.return_value = [{"chunk_id": str(chunk.id)}]
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_get_driver.return_value = mock_driver

    results = retrieve_relevant_chunks_via_graph(db=db_session, user_id=user.id, question="anything")

    assert len(results) == 1
    assert results[0].id == chunk.id


@patch("app.services.graph_retrieval.get_graph_driver")
def test_retrieve_via_graph_returns_empty_when_no_matches(mock_get_driver, db_session):
    mock_session = MagicMock()
    mock_session.run.return_value = []
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_get_driver.return_value = mock_driver

    results = retrieve_relevant_chunks_via_graph(db=db_session, user_id=uuid.uuid4(), question="anything")

    assert results == []
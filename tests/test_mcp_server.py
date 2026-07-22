import uuid
from unittest.mock import patch

import pytest

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.user import User
from app.security import hash_password


@pytest.fixture()
def mcp_test_user(db_session, monkeypatch):
    user = User(id=uuid.uuid4(), email="mcptest@example.com", hashed_password=hash_password("pw"))
    db_session.add(user)
    db_session.commit()
    monkeypatch.setenv("MCP_USER_EMAIL", "mcptest@example.com")
    return user


def test_list_documents_returns_only_own_documents(mcp_test_user, db_session, monkeypatch):
    from mcp_server import server

    monkeypatch.setattr(server, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)

    document = Document(
        id=uuid.uuid4(),
        owner_id=mcp_test_user.id,
        filename="test.pdf",
        s3_key="documents/test/test.pdf",
        status="ready",
    )
    db_session.add(document)
    db_session.commit()

    result = server.list_documents()

    assert len(result) == 1
    assert result[0]["filename"] == "test.pdf"


@patch("mcp_server.server.retrieve_relevant_chunks")
def test_search_documents_calls_retrieval(mock_retrieve, mcp_test_user, db_session, monkeypatch):
    from mcp_server import server

    monkeypatch.setattr(server, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)

    mock_retrieve.return_value = [
        Chunk(id=uuid.uuid4(), document_id=uuid.uuid4(), chunk_index=0, content="Matched content")
    ]

    result = server.search_documents(query="anything")

    assert len(result) == 1
    assert result[0]["content"] == "Matched content"
    mock_retrieve.assert_called_once()
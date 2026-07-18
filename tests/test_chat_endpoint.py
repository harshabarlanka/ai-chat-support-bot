import uuid
from unittest.mock import patch

from app.models.chunk import Chunk
from app.models.document import Document


def signup_and_login(client, email="chat@example.com", password="strongpassword123"):
    client.post("/auth/signup", json={"email": email, "password": password})
    response = client.post("/auth/login", data={"username": email, "password": password})
    return response.json()["access_token"]


@patch("app.routers.chat.generate_answer")
@patch("app.routers.chat.retrieve_relevant_chunks")
def test_chat_endpoint_returns_answer_and_sources(mock_retrieve, mock_generate, client, db_session):
    token = signup_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    fake_chunk = Chunk(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        chunk_index=0,
        content="Some relevant content",
    )
    mock_retrieve.return_value = [fake_chunk]
    mock_generate.return_value = "This is the generated answer."

    response = client.post("/chat/", headers=headers, json={"question": "What is this about?"})

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This is the generated answer."
    assert len(data["sources"]) == 1
    assert data["sources"][0]["content"] == "Some relevant content"


def test_chat_endpoint_requires_auth(client):
    response = client.post("/chat/", json={"question": "anything"})
    assert response.status_code == 401
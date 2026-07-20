from unittest.mock import patch

from app.models.chunk import Chunk


def signup_and_login(client, email="wschat@example.com", password="strongpassword123"):
    client.post("/auth/signup", json={"email": email, "password": password})
    response = client.post("/auth/login", data={"username": email, "password": password})
    return response.json()["access_token"]


@patch("app.routers.chat.generate_answer_stream")
@patch("app.routers.chat.retrieve_relevant_chunks")
def test_websocket_streams_answer(mock_retrieve, mock_stream, client):
    token = signup_and_login(client)

    mock_retrieve.return_value = [
        Chunk(id=None, document_id=None, chunk_index=0, content="Some content")
    ]
    mock_stream.return_value = iter(["Hello", " ", "world"])

    with client.websocket_connect(f"/chat/ws?token={token}") as websocket:
        websocket.receive_json()  # session confirmation
        websocket.send_text("What is this about?")

        messages = []
        while True:
            message = websocket.receive_json()
            messages.append(message)
            if message["type"] == "done":
                break

    token_messages = [m for m in messages if m["type"] == "token"]
    assert [m["content"] for m in token_messages] == ["Hello", " ", "world"]
    assert messages[-1]["type"] == "done"


def test_websocket_rejects_invalid_token(client):
    try:
        with client.websocket_connect("/chat/ws?token=not-a-real-token"):
            assert False, "Connection should have been rejected"
    except Exception:
        pass


@patch("app.routers.chat.generate_answer_stream")
@patch("app.routers.chat.rewrite_query")
@patch("app.routers.chat.retrieve_relevant_chunks")
def test_websocket_persists_and_reuses_history(mock_retrieve, mock_rewrite, mock_stream, client):
    token = signup_and_login(client, email="wsmemory@example.com")

    mock_retrieve.return_value = [Chunk(id=None, document_id=None, chunk_index=0, content="content")]
    mock_rewrite.side_effect = lambda question, history: question
    mock_stream.return_value = iter(["An answer."])

    with client.websocket_connect(f"/chat/ws?token={token}") as websocket:
        session_msg = websocket.receive_json()
        assert session_msg["type"] == "session"
        session_id = session_msg["session_id"]

        websocket.send_text("First question")
        while websocket.receive_json()["type"] != "done":
            pass

    # Reconnect with the same session_id and confirm rewrite_query receives real history
    mock_stream.return_value = iter(["Second answer."])
    with client.websocket_connect(f"/chat/ws?token={token}&session_id={session_id}") as websocket:
        websocket.receive_json()  # session confirmation
        websocket.send_text("Second question")
        while websocket.receive_json()["type"] != "done":
            pass

    # rewrite_query's second call should have received non-empty history
    second_call_history = mock_rewrite.call_args_list[1].args[1]
    assert len(second_call_history) == 2  # first user question + first assistant answer

    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/chat/sessions/{session_id}/messages", headers=headers)
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 4  # 2 user + 2 assistant messages across both turns
from unittest.mock import MagicMock, patch

from app.services.conversation import rewrite_query


def test_rewrite_query_returns_original_when_no_history():
    result = rewrite_query("What is this about?", history=[])
    assert result == "What is this about?"


@patch("app.services.conversation._client")
def test_rewrite_query_calls_gemini_when_history_exists(mock_client, db_session):
    from app.models.chat_message import ChatMessage
    import uuid

    history = [
        ChatMessage(id=uuid.uuid4(), session_id=uuid.uuid4(), role="user", content="Tell me about revenue"),
        ChatMessage(id=uuid.uuid4(), session_id=uuid.uuid4(), role="assistant", content="Revenue was $5M"),
    ]

    mock_response = MagicMock()
    mock_response.text = "What was last year's revenue?"
    mock_client.models.generate_content.return_value = mock_response

    result = rewrite_query("what about last year's?", history)

    assert result == "What was last year's revenue?"
    mock_client.models.generate_content.assert_called_once()
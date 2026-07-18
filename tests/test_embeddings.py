from unittest.mock import MagicMock, patch


@patch("app.services.embeddings._client")
def test_generate_embedding_returns_vector(mock_client):
    mock_embedding = MagicMock()
    mock_embedding.values = [0.1] * 768
    mock_response = MagicMock()
    mock_response.embeddings = [mock_embedding]
    mock_client.models.embed_content.return_value = mock_response

    from app.services.embeddings import generate_embedding

    result = generate_embedding("some text")

    assert len(result) == 768
    mock_client.models.embed_content.assert_called_once()
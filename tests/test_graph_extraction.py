from unittest.mock import MagicMock, patch

from app.services.graph_extraction import extract_entities_and_relationships


@patch("app.services.graph_extraction._client")
def test_extract_entities_parses_valid_json(mock_client):
    mock_response = MagicMock()
    mock_response.text = '{"entities": [{"name": "Harsha", "type": "Person"}], "relationships": []}'
    mock_client.models.generate_content.return_value = mock_response

    result = extract_entities_and_relationships("Harsha built this project.")

    assert result["entities"] == [{"name": "Harsha", "type": "Person"}]
    assert result["relationships"] == []


@patch("app.services.graph_extraction._client")
def test_extract_entities_handles_markdown_fenced_json(mock_client):
    mock_response = MagicMock()
    mock_response.text = '```json\n{"entities": [], "relationships": []}\n```'
    mock_client.models.generate_content.return_value = mock_response

    result = extract_entities_and_relationships("Some text.")

    assert result == {"entities": [], "relationships": []}


@patch("app.services.graph_extraction._client")
def test_extract_entities_returns_empty_on_invalid_json(mock_client):
    mock_response = MagicMock()
    mock_response.text = "not valid json at all"
    mock_client.models.generate_content.return_value = mock_response

    result = extract_entities_and_relationships("Some text.")

    assert result == {"entities": [], "relationships": []}
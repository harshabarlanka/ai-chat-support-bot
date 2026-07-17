import io
from unittest.mock import patch


def signup_and_login(client, email="docs@example.com", password="strongpassword123"):
    client.post("/auth/signup", json={"email": email, "password": password})
    response = client.post("/auth/login", data={"username": email, "password": password})
    return response.json()["access_token"]


def auth_headers(client):
    token = signup_and_login(client)
    return {"Authorization": f"Bearer {token}"}


@patch("app.routers.documents.upload_file_to_s3")
def test_upload_pdf_success(mock_upload, client):
    headers = auth_headers(client)
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content")

    response = client.post(
        "/documents/upload",
        headers=headers,
        files={"file": ("test.pdf", fake_pdf, "application/pdf")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["status"] == "uploaded"
    mock_upload.assert_called_once()


@patch("app.routers.documents.upload_file_to_s3")
def test_upload_rejects_non_pdf(mock_upload, client):
    headers = auth_headers(client)
    fake_txt = io.BytesIO(b"just some text")

    response = client.post(
        "/documents/upload",
        headers=headers,
        files={"file": ("test.txt", fake_txt, "text/plain")},
    )

    assert response.status_code == 400
    mock_upload.assert_not_called()


def test_upload_requires_auth(client):
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content")
    response = client.post(
        "/documents/upload", files={"file": ("test.pdf", fake_pdf, "application/pdf")}
    )
    assert response.status_code == 401
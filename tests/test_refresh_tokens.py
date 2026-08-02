def signup(client, email="refresh@example.com", password="strongpassword123"):
    client.post("/auth/signup", json={"email": email, "password": password})


def login(client, email="refresh@example.com", password="strongpassword123"):
    response = client.post("/auth/login", data={"username": email, "password": password})
    return response.json()


def test_login_returns_token_pair(client):
    signup(client)
    tokens = login(client)

    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


def test_refresh_issues_new_pair(client):
    signup(client)
    tokens = login(client)

    response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


def test_refresh_token_cannot_be_reused_after_rotation(client):
    signup(client)
    tokens = login(client)

    client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    second_attempt = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert second_attempt.status_code == 401


def test_logout_revokes_refresh_token(client):
    signup(client)
    tokens = login(client)

    logout_response = client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert logout_response.status_code == 204

    refresh_attempt = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_attempt.status_code == 401


def test_refresh_with_garbage_token_fails(client):
    response = client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert response.status_code == 401
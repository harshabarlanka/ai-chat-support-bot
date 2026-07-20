def signup_and_login(client, email="me@example.com", password="strongpassword123"):
    client.post("/auth/signup", json={"email": email, "password": password})
    response = client.post("/auth/login", data={"username": email, "password": password})
    return response.json()["access_token"]


def test_get_current_user_success(client):
    token = signup_and_login(client)
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_get_current_user_no_token_fails(client):
    response = client.get("/users/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token_fails(client):
    response = client.get("/users/me", headers={"Authorization": "Bearer not.a.valid.token"})
    assert response.status_code == 401
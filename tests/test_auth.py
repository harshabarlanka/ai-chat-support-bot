def test_signup_creates_user(client):
    response = client.post(
        "/auth/signup", json={"email": "test@example.com", "password": "strongpassword123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "hashed_password" not in data


def test_signup_duplicate_email_fails(client):
    client.post(
        "/auth/signup", json={"email": "dupe@example.com", "password": "strongpassword123"}
    )
    response = client.post(
        "/auth/signup", json={"email": "dupe@example.com", "password": "anotherpassword"}
    )
    assert response.status_code == 400


def test_login_success(client):
    client.post(
        "/auth/signup", json={"email": "login@example.com", "password": "strongpassword123"}
    )
    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "strongpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_fails(client):
    client.post(
        "/auth/signup", json={"email": "wrongpw@example.com", "password": "correctpassword"}
    )
    response = client.post(
        "/auth/login",
        data={"username": "wrongpw@example.com", "password": "incorrectpassword"},
    )
    assert response.status_code == 401
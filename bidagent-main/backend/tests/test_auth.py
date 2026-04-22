def test_signup_success(client):
    resp = client.post("/api/v1/auth/signup", json={
        "email": "new@example.com",
        "password": "password123",
        "name": "New User",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["email"] == "new@example.com"
    assert data["user"]["name"] == "New User"


def test_signup_duplicate_email(client):
    client.post("/api/v1/auth/signup", json={
        "email": "dup@example.com", "password": "pass", "name": "User1",
    })
    resp = client.post("/api/v1/auth/signup", json={
        "email": "dup@example.com", "password": "pass", "name": "User2",
    })
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_login_success(client):
    client.post("/api/v1/auth/signup", json={
        "email": "login@example.com", "password": "mypass", "name": "Login User",
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "login@example.com", "password": "mypass",
    })
    assert resp.status_code == 200
    assert "token" in resp.json()


def test_login_wrong_password(client):
    client.post("/api/v1/auth/signup", json={
        "email": "wrong@example.com", "password": "correct", "name": "User",
    })
    resp = client.post("/api/v1/auth/login", json={
        "email": "wrong@example.com", "password": "incorrect",
    })
    assert resp.status_code == 401


def test_login_nonexistent_email(client):
    resp = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com", "password": "pass",
    })
    assert resp.status_code == 401


def test_protected_route_no_token(client):
    resp = client.post("/api/v1/go-no-go")
    assert resp.status_code == 403


def test_protected_route_invalid_token(client):
    resp = client.post("/api/v1/go-no-go", headers={"Authorization": "Bearer invalidtoken"})
    assert resp.status_code == 401

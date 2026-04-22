def test_create_session(client, auth_headers):
    resp = client.post("/api/v1/sessions", json={
        "tender_name": "Test Tender",
        "tender_doc_id": "doc123",
        "sections": [{"id": "s1", "title": "Section 1"}],
        "drafts": {},
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["session"]["tender_name"] == "Test Tender"
    assert data["session"]["id"] is not None


def test_list_sessions(client, auth_headers):
    # Create two sessions
    client.post("/api/v1/sessions", json={"tender_name": "Bid A"}, headers=auth_headers)
    client.post("/api/v1/sessions", json={"tender_name": "Bid B"}, headers=auth_headers)

    resp = client.get("/api/v1/sessions", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["sessions"]) == 2


def test_get_session(client, auth_headers):
    create = client.post("/api/v1/sessions", json={
        "tender_name": "My Bid",
        "sections": [{"id": "s1", "title": "S1"}],
        "drafts": {"s1": {"text": "Draft text", "wordCount": 2}},
    }, headers=auth_headers)
    sid = create.json()["session"]["id"]

    resp = client.get(f"/api/v1/sessions/{sid}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["session"]["drafts"]["s1"]["text"] == "Draft text"


def test_update_session_drafts(client, auth_headers):
    create = client.post("/api/v1/sessions", json={"tender_name": "Bid"}, headers=auth_headers)
    sid = create.json()["session"]["id"]

    resp = client.put(f"/api/v1/sessions/{sid}", json={
        "drafts": {"s1": {"text": "Updated draft", "wordCount": 2}},
    }, headers=auth_headers)
    assert resp.status_code == 200

    get = client.get(f"/api/v1/sessions/{sid}", headers=auth_headers)
    assert get.json()["session"]["drafts"]["s1"]["text"] == "Updated draft"


def test_delete_session(client, auth_headers):
    create = client.post("/api/v1/sessions", json={"tender_name": "Delete Me"}, headers=auth_headers)
    sid = create.json()["session"]["id"]

    resp = client.delete(f"/api/v1/sessions/{sid}", headers=auth_headers)
    assert resp.status_code == 200

    get = client.get(f"/api/v1/sessions/{sid}", headers=auth_headers)
    assert get.status_code == 404


def test_session_isolation(client):
    """Sessions are scoped to the user — user B can't see user A's sessions."""
    # Create user A
    a = client.post("/api/v1/auth/signup", json={
        "email": "a@test.com", "password": "pass", "name": "A",
    })
    headers_a = {"Authorization": f"Bearer {a.json()['token']}"}

    # Create user B
    b = client.post("/api/v1/auth/signup", json={
        "email": "b@test.com", "password": "pass", "name": "B",
    })
    headers_b = {"Authorization": f"Bearer {b.json()['token']}"}

    # A creates a session
    client.post("/api/v1/sessions", json={"tender_name": "A's Bid"}, headers=headers_a)

    # B should see no sessions
    resp = client.get("/api/v1/sessions", headers=headers_b)
    assert len(resp.json()["sessions"]) == 0

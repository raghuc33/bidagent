def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


def test_api_root(client):
    resp = client.get("/api/v1/")
    assert resp.status_code == 200
    assert resp.json() == {"message": "BidAgent API"}

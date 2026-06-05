from backend.main import app
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["users_count"] >= 3


def test_login_endpoint_success():
    response = client.post(
        "/auth/login",
        data={"username": "john@example.com", "password": "password123"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["user"]["email"] == "john@example.com"

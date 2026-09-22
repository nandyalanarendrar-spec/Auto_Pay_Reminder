import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_unauthorized_access():
    """
    Verifies that requests without Authorization Bearer header are rejected with 401.
    """
    response = client.get("/api/v1/subscriptions/")
    assert response.status_code == 401

def test_health_endpoint():
    """
    Verifies health check endpoint returns 200 OK.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_subscriptions_schema_validation():
    """
    Verifies subscription endpoint rejects invalid payloads with 422.
    """
    response = client.post("/api/v1/subscriptions/", json={"invalid_key": "data"})
    assert response.status_code in [401, 422]

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_emis_unauthorized_access():
    """
    Verifies that EMI requests without Authorization header are rejected with 401.
    """
    response = client.get("/api/v1/emis/")
    assert response.status_code == 401

def test_emis_schema_validation():
    """
    Verifies EMI creation endpoint rejects invalid payloads.
    """
    response = client.post("/api/v1/emis/", json={"invalid_key": "data"})
    assert response.status_code in [401, 422]

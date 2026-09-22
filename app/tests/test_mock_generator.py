import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_mock_generator_unauthorized():
    """
    Verifies mock data generator requires authentication header.
    """
    response = client.post("/api/v1/mock/generate-transactions", json={"months": 6})
    assert response.status_code == 401

def test_mock_get_transactions_unauthorized():
    """
    Verifies GET transactions requires authorization header.
    """
    response = client.get("/api/v1/mock/transactions")
    assert response.status_code == 401

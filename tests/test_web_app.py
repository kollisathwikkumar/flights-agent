"""Unit tests for Web App endpoints."""

import pytest
from fastapi.testclient import TestClient
from web_app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_web_app_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "T10 Flight Option Finder" in response.text


def test_web_app_api_search(client):
    response = client.post("/api/search", json={"query": "Delhi to Mumbai on September 24 under ₹8,000"})
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "trace" in data
    assert "formatted_response" in data
    assert len(data["trace"]) > 0

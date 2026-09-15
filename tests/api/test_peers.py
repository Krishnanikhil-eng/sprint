"""
Unit Tests for Peers API Endpoints.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_get_peer_groups():
    response = client.get("/api/v1/peers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_peer_group_members():
    response = client.get("/api/v1/peers/IT%20Services")
    assert response.status_code == 200
    data = response.json()
    assert data["peer_group_name"] == "IT Services"
    assert "members" in data
    assert len(data["members"]) > 0


def test_compare_company_peers():
    response = client.get("/api/v1/companies/TCS/peers/compare")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "TCS"
    assert "percentiles" in data

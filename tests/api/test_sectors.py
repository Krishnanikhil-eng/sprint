"""
Unit Tests for Sectors API Endpoints.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_get_sectors():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "sector" in first
    assert "company_count" in first


def test_get_sector_companies():
    response = client.get("/api/v1/sectors/Financials/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_get_sector_companies_404():
    response = client.get("/api/v1/sectors/NonExistentSector123/companies")
    assert response.status_code == 404

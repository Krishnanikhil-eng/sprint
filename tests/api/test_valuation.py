"""
Unit Tests for Valuation, Portfolio, and Documents API Endpoints.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_get_company_valuation():
    response = client.get("/api/v1/market-cap/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "TCS"
    assert "history" in data


def test_get_portfolio_stats():
    response = client.get("/api/v1/portfolio/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_companies"] == 92
    assert "sector_allocation" in data


def test_get_company_documents():
    response = client.get("/api/v1/companies/ABB/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "ABB"
    assert "documents" in data

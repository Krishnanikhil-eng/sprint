"""
Unit Tests for Screener API Endpoint.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_screener_default():
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_screener_filtered_roe_and_sector():
    response = client.get("/api/v1/screener?min_roe=15.0&sector=Financial Services")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for company in data:
        assert company["return_on_equity_pct"] >= 15.0
        assert (
            "FINANCIAL" in company["sector"].upper()
            or "BANK" in company["sector"].upper()
        )


def test_screener_invalid_negative_de():
    response = client.get("/api/v1/screener?max_de=-1.5")
    assert response.status_code == 400
    assert "max_de cannot be negative" in response.json()["detail"]

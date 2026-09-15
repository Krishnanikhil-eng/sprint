"""
Unit tests for Day 38 FastAPI Health Endpoint and Database Helper.
"""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["health"] == "/api/v1/health"


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], (int, float))

    db_counts = data["db_row_counts"]
    assert isinstance(db_counts, dict)

    # Verify key project tables are present
    required_tables = [
        "companies",
        "profitandloss",
        "balancesheet",
        "cashflow",
        "financial_ratios",
        "sectors",
        "market_cap",
    ]
    for t in required_tables:
        assert t in db_counts
        assert db_counts[t] > 0

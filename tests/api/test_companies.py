"""
Unit tests for Day 39 Company Data API Endpoints.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_get_companies_list():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 92
    assert set(data[0].keys()).issuperset(
        {"id", "company_name", "broad_sector", "roe_pct", "roce_pct"}
    )


def test_get_companies_filter_and_search():
    # Filter by sector
    res_tech = client.get("/api/v1/companies?sector=Information%20Technology")
    assert res_tech.status_code == 200
    data_tech = res_tech.json()
    assert len(data_tech) > 0
    assert all("Technology" in item["broad_sector"] for item in data_tech)

    # Search by ticker
    res_tcs = client.get("/api/v1/companies?search=TCS")
    assert res_tcs.status_code == 200
    data_tcs = res_tcs.json()
    assert len(data_tcs) >= 1
    assert data_tcs[0]["id"] == "TCS"


def test_get_company_detail_valid_and_invalid():
    res_tcs = client.get("/api/v1/companies/TCS")
    assert res_tcs.status_code == 200
    data = res_tcs.json()
    assert data["company_id"] == "TCS"
    assert "return_on_equity_pct" in data

    # Unknown ticker
    res_inv = client.get("/api/v1/companies/NONEXISTENT_TICKER")
    assert res_inv.status_code == 404


def test_get_company_statements_history():
    # P&L
    res_pl = client.get("/api/v1/companies/TCS/pl?from_year=2020&to_year=2024")
    assert res_pl.status_code == 200
    data_pl = res_pl.json()
    assert len(data_pl) > 0
    assert all(2020 <= item["year"] <= 2024 for item in data_pl)

    # Balance Sheet
    res_bs = client.get("/api/v1/companies/TCS/bs")
    assert res_bs.status_code == 200

    # Cash Flow
    res_cf = client.get("/api/v1/companies/TCS/cashflow")
    assert res_cf.status_code == 200

    # Ratios
    res_ratios = client.get("/api/v1/companies/TCS/ratios?year=2024")
    assert res_ratios.status_code == 200
    assert len(res_ratios.json()) == 1


def test_get_company_tearsheet_pdf_endpoint():
    res_pdf = client.get("/api/v1/companies/TCS/tearsheet")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert len(res_pdf.content) > 30 * 1024

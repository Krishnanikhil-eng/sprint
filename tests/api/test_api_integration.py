"""
Comprehensive Multi-Step REST API Integration Flow Tests (Day 42).
Validates end-to-end user workflows through FastAPI endpoints.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_api_full_analyst_workflow():
    # Step 1: Health check
    h_res = client.get("/api/v1/health")
    assert h_res.status_code == 200
    assert h_res.json()["status"] == "ok"

    # Step 2: Screen high ROE companies
    s_res = client.get("/api/v1/screener?min_roe=15.0")
    assert s_res.status_code == 200
    screener_results = s_res.json()
    assert len(screener_results) > 0

    first_company = screener_results[0]
    ticker = first_company["ticker"]

    # Step 3: Fetch company profile & financial statements
    c_res = client.get(f"/api/v1/companies/{ticker}")
    assert c_res.status_code == 200
    assert c_res.json()["company_id"] == ticker

    pl_res = client.get(f"/api/v1/companies/{ticker}/pl")
    assert pl_res.status_code == 200

    # Step 4: Compare company against peer group
    peer_res = client.get(f"/api/v1/companies/{ticker}/peers/compare")
    assert peer_res.status_code == 200

    # Step 5: Check company documents
    doc_res = client.get(f"/api/v1/companies/{ticker}/documents")
    assert doc_res.status_code == 200

    # Step 6: Stream tearsheet PDF
    pdf_res = client.get(f"/api/v1/companies/{ticker}/tearsheet")
    assert pdf_res.status_code in (200, 404)


def test_api_sector_exploration_workflow():
    # Step 1: Get sector list
    sec_res = client.get("/api/v1/sectors")
    assert sec_res.status_code == 200
    sectors = sec_res.json()
    assert len(sectors) > 0

    sector_name = sectors[0]["sector"]

    # Step 2: Get companies in sector
    comp_res = client.get(f"/api/v1/sectors/{sector_name}/companies")
    assert comp_res.status_code == 200
    companies = comp_res.json()
    assert len(companies) > 0


def test_api_portfolio_stats_workflow():
    p_res = client.get("/api/v1/portfolio/stats")
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert p_data["total_companies"] == 92
    assert "sector_allocation" in p_data

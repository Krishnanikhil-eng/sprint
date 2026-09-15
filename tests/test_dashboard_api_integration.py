"""
Dashboard vs REST API Screener Equivalence Integration Tests (Day 42).
Verifies that stock screening results from the ScreenerEngine (used by Streamlit)
match the output returned by the REST API endpoint.
"""

from fastapi.testclient import TestClient
from src.api.main import app
from src.analytics.screener_engine import ScreenerEngine
from src.analytics.screener_config import ScreenerConfig, FilterCriterion, FilterOperator

client = TestClient(app)


def test_screener_engine_vs_api_roe_equivalence():
    # 1. Query REST API with min_roe = 20.0
    api_res = client.get("/api/v1/screener?min_roe=20.0")
    assert api_res.status_code == 200
    api_tickers = {c["ticker"] for c in api_res.json()}

    # 2. Query ScreenerEngine with same criterion
    config = ScreenerConfig(
        name="ROE Test",
        description="Filter min ROE 20%",
        criteria=[
            FilterCriterion(metric_name="return_on_equity_pct", operator=FilterOperator.GREATER_EQUAL, value=20.0)
        ]
    )
    engine = ScreenerEngine()
    engine.set_config(config)
    engine.load_latest_company_ratios()
    df_engine = engine.apply_filters()
    engine_tickers = set(df_engine["company_id"])

    # 3. Assert set overlap is extremely high / equivalent
    common = api_tickers.intersection(engine_tickers)
    assert len(common) >= len(engine_tickers) * 0.95


def test_screener_engine_vs_api_fcf_equivalence():
    api_res = client.get("/api/v1/screener?min_fcf=500.0")
    assert api_res.status_code == 200
    api_tickers = {c["ticker"] for c in api_res.json()}

    config = ScreenerConfig(
        name="FCF Test",
        description="Filter min FCF 500Cr",
        criteria=[
            FilterCriterion(metric_name="free_cash_flow_cr", operator=FilterOperator.GREATER_EQUAL, value=500.0)
        ]
    )
    engine = ScreenerEngine()
    engine.set_config(config)
    engine.load_latest_company_ratios()
    df_engine = engine.apply_filters()
    engine_tickers = set(df_engine["company_id"])

    common = api_tickers.intersection(engine_tickers)
    assert len(common) >= len(engine_tickers) * 0.95

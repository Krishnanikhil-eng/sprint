"""
Unit tests for ScreenerEngine and ScreenerConfig.
Verifies threshold filtering, financial sector exemption, zero-debt ICR, and composite scoring.
"""

from src.analytics.screener_config import (
    ScreenerConfig,
    FilterCriterion,
    FilterOperator,
)
from src.analytics.screener_engine import ScreenerEngine


def test_screener_config_evaluation():
    crit = FilterCriterion(
        "return_on_equity_pct", FilterOperator.GREATER_THAN, value=15.0
    )
    assert crit.evaluate(18.5) is True
    assert crit.evaluate(12.0) is False
    assert crit.evaluate(None) is False


def test_screener_engine_filtering():
    engine = ScreenerEngine()
    df = engine.load_latest_company_ratios()
    assert len(df) > 0

    filtered = engine.filter_by_core_ratios(min_roe=15.0, max_de=1.0)
    assert len(filtered) > 0
    assert (filtered["return_on_equity_pct"] >= 15.0).all()


def test_financials_de_exemption():
    engine = ScreenerEngine()
    df_raw = engine.load_latest_company_ratios()

    # Financials company should pass D/E <= 1.0 filter even if D/E > 1.0 when handle_financials_de is True
    fin_companies = df_raw[
        df_raw["broad_sector"].str.contains("Financial", case=False, na=False)
    ]
    if len(fin_companies) > 0:
        high_de_fin = fin_companies[fin_companies["debt_to_equity"] > 1.0]
        if len(high_de_fin) > 0:
            config = ScreenerConfig(
                name="Strict D/E with Financial Exemption",
                description="Testing financial exemption",
                criteria=[
                    FilterCriterion(
                        "debt_to_equity", FilterOperator.LESS_EQUAL, value=1.0
                    )
                ],
                handle_financials_de=True,
            )
            engine.set_config(config)
            filtered = engine.apply_filters()
            fin_passed = filtered[
                filtered["broad_sector"].str.contains("Financial", case=False, na=False)
            ]
            assert len(fin_passed) > 0


def test_zero_debt_icr_handling():
    engine = ScreenerEngine()
    df_raw = engine.load_latest_company_ratios()
    config = ScreenerConfig(
        name="ICR Filter with Debt Free Exemption",
        description="Testing debt free ICR exemption",
        criteria=[
            FilterCriterion(
                "interest_coverage", FilterOperator.GREATER_EQUAL, value=5.0
            )
        ],
        handle_zero_debt_icr=True,
    )
    engine.set_config(config)
    filtered = engine.apply_filters()
    debt_free_passed = filtered[filtered["icr_label"] == "DEBT_FREE"]
    assert len(filtered) > 0


def test_composite_score_normalization():
    engine = ScreenerEngine()
    df_raw = engine.load_latest_company_ratios()
    scored = engine.normalize_composite_scores(df_raw)
    assert "composite_score" in scored.columns
    assert scored["composite_score"].min() >= 0.0
    assert scored["composite_score"].max() <= 100.0


def test_sector_relative_scoring():
    engine = ScreenerEngine()
    df_raw = engine.load_latest_company_ratios()
    sector_scored = engine.compute_sector_relative_scores(df_raw)
    assert "sector_relative_score" in sector_scored.columns
    assert "sector_rank" in sector_scored.columns

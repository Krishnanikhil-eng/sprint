"""
Unit tests validating all 6 stock screening presets.
Executes each preset against Nifty 100 database and verifies result integrity and count.
"""

import pytest
from src.analytics.screener_engine import ScreenerEngine
from src.analytics.presets import ALL_PRESETS

@pytest.fixture
def engine():
    eng = ScreenerEngine()
    eng.load_latest_company_ratios()
    return eng

def test_all_six_presets_execution(engine):
    assert len(ALL_PRESETS) == 6
    preset_names = ["quality_compounder", "value_pick", "growth_accelerator", "dividend_champion", "debt_free_bluechip", "turnaround_watch"]
    
    for p_name in preset_names:
        assert p_name in ALL_PRESETS
        config = ALL_PRESETS[p_name]
        engine.set_config(config)
        filtered = engine.apply_filters()
        scored = engine.compute_sector_relative_scores(filtered)
        
        assert len(scored) > 0, f"Preset {p_name} returned 0 companies"
        assert "composite_score" in scored.columns
        assert "sector_rank" in scored.columns

def test_quality_compounder_preset_integrity(engine):
    config = ALL_PRESETS["quality_compounder"]
    engine.set_config(config)
    df = engine.apply_filters()
    
    non_fin = df[~df["broad_sector"].str.contains("Financial|Bank", case=False, na=False)]
    if len(non_fin) > 0:
        assert (non_fin["debt_to_equity"] <= 0.5).all()
    assert (df["return_on_equity_pct"] >= 15.0).all()
    assert (df["roce_pct"] >= 15.0).all()

def test_debt_free_bluechip_preset_integrity(engine):
    config = ALL_PRESETS["debt_free_bluechip"]
    engine.set_config(config)
    df = engine.apply_filters()
    
    non_fin = df[~df["broad_sector"].str.contains("Financial|Bank", case=False, na=False)]
    if len(non_fin) > 0:
        assert (non_fin["debt_to_equity"] <= 0.1).all()

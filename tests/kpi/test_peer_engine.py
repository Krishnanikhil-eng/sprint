"""
Unit tests for PeerEngine, PeerExporter, and RadarChart generator.
Verifies percentile calculations, inverse debt ranks, SQLite persistence, and exports.
"""

import os
import pytest
import sqlite3

from src.analytics.peer_engine import PeerEngine
from src.analytics.peer_exporter import PeerExporter
from src.analytics.radar_chart import generate_peer_radar_chart


@pytest.fixture
def peer_engine():
    engine = PeerEngine()
    engine.load_peer_data()
    return engine


def test_peer_group_loading(peer_engine):
    assert peer_engine.ratios_df is not None
    assert len(peer_engine.ratios_df) > 0
    assert "effective_peer_group" in peer_engine.ratios_df.columns


def test_peer_percentiles_calculation(peer_engine):
    df_pct = peer_engine.compute_peer_percentiles()
    assert "return_on_equity_pct_percentile" in df_pct.columns
    assert df_pct["return_on_equity_pct_percentile"].min() >= 0.0
    assert df_pct["return_on_equity_pct_percentile"].max() <= 100.0


def test_inverse_debt_percentile_logic(peer_engine):
    df_inv = peer_engine.compute_inverse_debt_percentiles()
    assert "debt_to_equity_percentile" in df_inv.columns

    # In peer group with multiple companies, lower D/E company must have higher or equal D/E percentile
    grp = df_inv.groupby("effective_peer_group").filter(lambda g: len(g) >= 2)
    if len(grp) > 0:
        sample_grp = grp.groupby("effective_peer_group").get_group(
            grp["effective_peer_group"].iloc[0]
        )
        sorted_by_de = sample_grp.sort_values(by="debt_to_equity", ascending=True)
        # Company with lowest D/E should have highest D/E percentile
        lowest_de = sorted_by_de.iloc[0]
        highest_de = sorted_by_de.iloc[-1]
        assert (
            lowest_de["debt_to_equity_percentile"]
            >= highest_de["debt_to_equity_percentile"]
        )


def test_sqlite_peer_percentiles_persistence(peer_engine):
    peer_engine.save_peer_percentiles_to_db()

    conn = sqlite3.connect("nifty100.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM peer_percentiles;")
    count = cursor.fetchone()[0]
    conn.close()

    assert count > 0


def test_radar_chart_generation():
    chart_path = generate_peer_radar_chart(
        company_name="Test Company",
        categories=["ROE", "ROCE", "Low Debt", "NPM", "OPM", "FCF"],
        company_values=[80, 75, 90, 60, 70, 85],
        output_path="output/charts/test_radar.png",
    )
    assert os.path.exists(chart_path)


def test_peer_exporter_run():
    exporter = PeerExporter()
    out_file = exporter.export_peer_report("test_peer_report.xlsx")
    assert os.path.exists(out_file)

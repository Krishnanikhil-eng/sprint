"""
Unit tests for Day 37 Cluster Profiling, Correlation Heatmap, Outlier Detection, and Portfolio Stats.
"""

import os

from src.analytics.cluster_profiler import (
    ClusterProfiler,
    PORTFOLIO_10_KPIS,
)


def test_cluster_profiler_outputs(tmp_path):
    output_dir = str(tmp_path / "output")
    reports_dir = str(tmp_path / "reports")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    labels_csv = str(tmp_path / "output" / "cluster_labels.csv")
    corr_plot = str(tmp_path / "reports" / "correlation_heatmap.png")
    outlier_csv = str(tmp_path / "output" / "outlier_report.csv")
    port_stats_csv = str(tmp_path / "output" / "portfolio_stats.csv")

    profiler = ClusterProfiler(
        db_path="nifty100.db", labels_csv="output/cluster_labels.csv"
    )

    # 1. Profile Clusters
    df_prof = profiler.profile_clusters()
    assert len(df_prof) == 5
    assert "return_on_equity_pct_mean" in df_prof.columns

    # 2. Correlation Heatmap
    corr_matrix = profiler.generate_correlation_heatmap(output_path=corr_plot)
    assert os.path.exists(corr_plot)
    assert corr_matrix.shape == (10, 10)

    # 3. Outlier Detection
    df_outliers = profiler.detect_outliers(output_csv=outlier_csv)
    assert os.path.exists(outlier_csv)
    assert set(df_outliers.columns).issuperset(
        {"company_id", "broad_sector", "metric", "z_score"}
    )

    # 4. Portfolio Stats
    df_stats = profiler.calculate_portfolio_stats(output_csv=port_stats_csv)
    assert os.path.exists(port_stats_csv)
    assert len(df_stats) == len(PORTFOLIO_10_KPIS)
    assert set(df_stats.columns).issuperset(
        {"metric", "count", "mean", "std", "p10", "p50", "p90"}
    )

    profiler.close()

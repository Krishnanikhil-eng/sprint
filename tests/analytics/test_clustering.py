"""
Unit tests for Day 36 KMeans Financial Archetype Clustering module.
"""

import os
import sqlite3

from src.analytics.clustering import (
    FinancialClusteringEngine,
    run_clustering,
    CLUSTERING_FEATURES,
)


def test_prepare_features_imputation(tmp_path):
    db_file = str(tmp_path / "test_cluster.db")
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    cur.execute(
        "CREATE TABLE companies (company_id TEXT PRIMARY KEY, company_name TEXT);"
    )
    cur.execute("CREATE TABLE sectors (company_id TEXT, broad_sector TEXT);")
    cur.execute(
        "CREATE TABLE profitandloss (company_id TEXT, year INT, sales REAL, net_profit REAL, opm_percentage REAL);"
    )
    cur.execute(
        "CREATE TABLE financial_ratios (company_id TEXT, year INT, return_on_equity_pct REAL, roce_pct REAL, debt_to_equity REAL, interest_coverage REAL, revenue_cagr_5yr REAL, fcf_cagr_5yr REAL, operating_profit_margin_pct REAL);"
    )

    # Company 1 (complete data)
    cur.execute("INSERT INTO companies VALUES ('C1', 'Company 1');")
    cur.execute("INSERT INTO sectors VALUES ('C1', 'Tech');")
    cur.execute("INSERT INTO profitandloss VALUES ('C1', 2024, 1000.0, 200.0, 20.0);")
    cur.execute(
        "INSERT INTO financial_ratios VALUES ('C1', 2024, 25.0, 20.0, 0.1, 15.0, 15.0, 10.0, 20.0);"
    )

    # Company 2 (missing ROE & FCF CAGR - should be imputed from sector/global median)
    cur.execute("INSERT INTO companies VALUES ('C2', 'Company 2');")
    cur.execute("INSERT INTO sectors VALUES ('C2', 'Tech');")
    cur.execute("INSERT INTO profitandloss VALUES ('C2', 2024, 800.0, 150.0, 18.0);")
    cur.execute(
        "INSERT INTO financial_ratios VALUES ('C2', 2024, NULL, 16.0, 0.2, 10.0, 12.0, NULL, 18.0);"
    )

    conn.commit()
    conn.close()

    engine = FinancialClusteringEngine(db_path=db_file)
    df_imp, stats = engine.prepare_features()
    engine.close()

    assert len(df_imp) == 2
    assert df_imp[CLUSTERING_FEATURES].isna().sum().sum() == 0
    assert (
        df_imp.loc[df_imp["company_id"] == "C2", "return_on_equity_pct"].iloc[0] == 25.0
    )  # Imputed from C1 sector median


def test_kmeans_clustering_and_elbow_plot(tmp_path):
    output_csv = str(tmp_path / "cluster_labels.csv")
    elbow_path = str(tmp_path / "elbow_plot.png")

    df_labels = run_clustering(
        db_path="nifty100.db", output_csv=output_csv, elbow_path=elbow_path
    )

    # 1. Exactly 92 companies
    assert len(df_labels) == 92

    # 2. No duplicate company IDs
    assert df_labels["company_id"].nunique() == 92

    # 3. Valid cluster IDs 0-4 only
    assert set(df_labels["cluster_id"].unique()).issubset({0, 1, 2, 3, 4})

    # 4. Distance from centroid is numeric and positive
    assert (df_labels["distance_from_centroid"] >= 0).all()
    assert not df_labels["distance_from_centroid"].isna().any()

    # 5. File outputs exist
    assert os.path.exists(output_csv)
    assert os.path.exists(elbow_path)
    assert os.path.getsize(elbow_path) > 5 * 1024

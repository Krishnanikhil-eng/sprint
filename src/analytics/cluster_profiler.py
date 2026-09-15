"""
Cluster Profiling, Correlation Heatmap, Outlier Detection, and Portfolio Statistics Module (Day 37).
Performs cluster financial profiling, Pearson correlation matrix generation, sector Z-score outlier detection,
and 92-company portfolio percentile statistics.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from src.analytics.clustering import FinancialClusteringEngine, CLUSTERING_FEATURES

DB_PATH_DEFAULT = "nifty100.db"
LABELS_CSV_DEFAULT = "output/cluster_labels.csv"
OUTLIER_CSV_DEFAULT = "output/outlier_report.csv"
PORTFOLIO_STATS_CSV_DEFAULT = "output/portfolio_stats.csv"
CORRELATION_PLOT_DEFAULT = "reports/correlation_heatmap.png"

PORTFOLIO_10_KPIS = [
    "return_on_equity_pct",
    "roce_pct",
    "debt_to_equity",
    "interest_coverage",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "asset_turnover",
    "free_cash_flow_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
]


class ClusterProfiler:
    def __init__(
        self, db_path: str = DB_PATH_DEFAULT, labels_csv: str = LABELS_CSV_DEFAULT
    ):
        self.db_path = db_path
        self.labels_csv = labels_csv
        self.conn = sqlite3.connect(db_path)
        self._load_data()

    def _load_data(self):
        """Loads master tables."""
        self.companies = pd.read_sql_query(
            "SELECT company_id, company_name FROM companies ORDER BY company_id",
            self.conn,
        )
        self.sectors = pd.read_sql_query(
            "SELECT company_id, broad_sector FROM sectors", self.conn
        )
        self.ratios = pd.read_sql_query(
            "SELECT * FROM financial_ratios ORDER BY year ASC", self.conn
        )
        self.pnl = pd.read_sql_query(
            "SELECT company_id, year, sales, net_profit, opm_percentage FROM profitandloss ORDER BY year ASC",
            self.conn,
        )

    def close(self):
        if self.conn:
            self.conn.close()

    def profile_clusters(self) -> pd.DataFrame:
        """
        Calculates MEAN and MEDIAN for the 5 clustering features per cluster.
        Returns cluster profiles DataFrame.
        """
        engine = FinancialClusteringEngine(db_path=self.db_path)
        df_features, _ = engine.prepare_features()
        engine.close()

        if not os.path.exists(self.labels_csv):
            engine = FinancialClusteringEngine(db_path=self.db_path)
            engine.run_kmeans(output_csv=self.labels_csv)
            engine.close()

        df_labels = pd.read_csv(self.labels_csv)
        df_merged = pd.merge(
            df_features,
            df_labels[["company_id", "cluster_id", "cluster_name"]],
            on="company_id",
        )

        profiles = []
        for cid, group in df_merged.groupby("cluster_id"):
            c_name = group["cluster_name"].iloc[0]
            rec = {
                "cluster_id": int(cid),
                "cluster_name": c_name,
                "company_count": len(group),
            }
            for col in CLUSTERING_FEATURES:
                rec[f"{col}_mean"] = round(float(group[col].mean()), 2)
                rec[f"{col}_median"] = round(float(group[col].median()), 2)
            profiles.append(rec)

        df_profiles = (
            pd.DataFrame(profiles).sort_values("cluster_id").reset_index(drop=True)
        )
        print("=== Cluster Financial Profiles ===")
        print(
            df_profiles[
                [
                    "cluster_id",
                    "cluster_name",
                    "company_count",
                    "return_on_equity_pct_mean",
                    "debt_to_equity_mean",
                ]
            ]
        )
        return df_profiles

    def generate_correlation_heatmap(
        self, output_path: str = CORRELATION_PLOT_DEFAULT
    ) -> pd.DataFrame:
        """
        Calculates Pearson correlation matrix for 10 KPIs across all 92 companies
        and saves reports/correlation_heatmap.png.
        """
        records = []
        for cid in self.companies["company_id"].unique():
            c_rat = self.ratios[self.ratios["company_id"] == cid].sort_values("year")
            l_rat = c_rat.iloc[-1] if not c_rat.empty else {}
            rec = {"company_id": cid}
            for col in PORTFOLIO_10_KPIS:
                rec[col] = l_rat.get(col)
            records.append(rec)

        df_kpis = pd.DataFrame(records)[PORTFOLIO_10_KPIS].astype(float)
        corr_matrix = df_kpis.corr(method="pearson")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        fig, ax = plt.subplots(figsize=(9, 7), dpi=200)

        sns.heatmap(
            corr_matrix,
            annot=True,
            fmt=".2f",
            cmap="vlag",
            cbar=True,
            square=True,
            linewidths=0.5,
            ax=ax,
            annot_kws={"size": 7},
        )

        ax.set_title(
            "Pearson Correlation Heatmap (10 Financial KPIs)",
            fontsize=11,
            fontweight="bold",
            color="#1A2B4C",
            pad=10,
        )
        plt.xticks(rotation=45, ha="right", fontsize=7.5)
        plt.yticks(rotation=0, fontsize=7.5)
        fig.tight_layout()

        plt.savefig(output_path, bbox_inches="tight")
        plt.close(fig)

        print(f"Saved Pearson Correlation Heatmap -> {output_path}")
        return corr_matrix

    def detect_outliers(self, output_csv: str = OUTLIER_CSV_DEFAULT) -> pd.DataFrame:
        """
        Calculates Z-score within broad_sector for 10 KPIs.
        Flags companies where |Z| > 3.
        Generates output/outlier_report.csv.
        """
        sec_map = dict(zip(self.sectors["company_id"], self.sectors["broad_sector"]))
        records = []

        for cid in self.companies["company_id"].unique():
            broad_sec = sec_map.get(cid, "Unknown")
            c_rat = self.ratios[self.ratios["company_id"] == cid].sort_values("year")
            l_rat = c_rat.iloc[-1] if not c_rat.empty else {}
            rec = {"company_id": cid, "broad_sector": broad_sec}
            for col in PORTFOLIO_10_KPIS:
                rec[col] = l_rat.get(col)
            records.append(rec)

        df_master = pd.DataFrame(records)
        outlier_rows = []

        for col in PORTFOLIO_10_KPIS:
            for sec, group in df_master.groupby("broad_sector"):
                vals = group[col].dropna()
                if len(vals) < 3:  # Need at least 3 samples for meaningful std
                    continue
                mean_v = vals.mean()
                std_v = vals.std()
                if std_v == 0 or pd.isna(std_v):
                    continue

                for idx, row in group.iterrows():
                    val = row[col]
                    if pd.notna(val):
                        z_score = (val - mean_v) / std_v
                        if abs(z_score) > 3.0:
                            outlier_rows.append(
                                {
                                    "company_id": row["company_id"],
                                    "broad_sector": sec,
                                    "metric": col,
                                    "metric_value": round(float(val), 2),
                                    "z_score": round(float(z_score), 2),
                                    "outlier_flag": True,
                                }
                            )

        df_outliers = pd.DataFrame(
            outlier_rows,
            columns=[
                "company_id",
                "broad_sector",
                "metric",
                "metric_value",
                "z_score",
                "outlier_flag",
            ],
        )

        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df_outliers.to_csv(output_csv, index=False)

        print("=== Outlier Detection Summary ===")
        print(f"Total Outliers Flagged (|Z| > 3): {len(df_outliers)}")
        print(f"Saved outlier report -> {output_csv}")

        return df_outliers

    def calculate_portfolio_stats(
        self, output_csv: str = PORTFOLIO_STATS_CSV_DEFAULT
    ) -> pd.DataFrame:
        """
        Calculates P10, P25, P50, P75, P90, Mean, Std for 10 KPIs across all 92 companies.
        Generates output/portfolio_stats.csv.
        """
        records = []
        for cid in self.companies["company_id"].unique():
            c_rat = self.ratios[self.ratios["company_id"] == cid].sort_values("year")
            l_rat = c_rat.iloc[-1] if not c_rat.empty else {}
            rec = {"company_id": cid}
            for col in PORTFOLIO_10_KPIS:
                rec[col] = l_rat.get(col)
            records.append(rec)

        df_master = pd.DataFrame(records)
        stats_rows = []

        for col in PORTFOLIO_10_KPIS:
            series = df_master[col].dropna().astype(float)
            if not series.empty:
                stats_rows.append(
                    {
                        "metric": col,
                        "count": len(series),
                        "mean": round(float(series.mean()), 2),
                        "std": round(float(series.std()), 2),
                        "p10": round(float(np.percentile(series, 10)), 2),
                        "p25": round(float(np.percentile(series, 25)), 2),
                        "p50": round(float(np.percentile(series, 50)), 2),
                        "p75": round(float(np.percentile(series, 75)), 2),
                        "p90": round(float(np.percentile(series, 90)), 2),
                    }
                )

        df_stats = pd.DataFrame(stats_rows)
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df_stats.to_csv(output_csv, index=False)

        print("=== Portfolio Statistics Summary ===")
        print(df_stats[["metric", "mean", "p50", "p75", "p90"]])
        print(f"Saved portfolio statistics -> {output_csv}")

        return df_stats


def run_day37_analytics(db_path: str = DB_PATH_DEFAULT):
    profiler = ClusterProfiler(db_path=db_path)
    try:
        profiler.profile_clusters()
        profiler.generate_correlation_heatmap()
        profiler.detect_outliers()
        profiler.calculate_portfolio_stats()
        print("Day 37 Cluster Profiling & Portfolio Statistics Complete!")
    finally:
        profiler.close()


if __name__ == "__main__":
    run_day37_analytics()

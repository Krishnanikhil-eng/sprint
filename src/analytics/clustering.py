"""
KMeans Financial Archetype Clustering Module (Day 36).
Clusters all 92 companies into 5 financial archetypes using 5 canonical features:
- return_on_equity_pct
- debt_to_equity
- revenue_cagr_5yr
- fcf_cagr_5yr
- operating_profit_margin_pct
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Tuple, Dict, List, Any

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

DB_PATH_DEFAULT = "nifty100.db"
OUTPUT_CSV_DEFAULT = "output/cluster_labels.csv"
ELBOW_PLOT_DEFAULT = "reports/elbow_plot.png"

CLUSTERING_FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct"
]

# Initial cluster names (will be dynamically profiled in Day 37)
DEFAULT_CLUSTER_NAMES = {
    0: "High-Quality Compounders",
    1: "Defensive Dividend Payers",
    2: "Value Cyclicals",
    3: "Distressed or Turnaround",
    4: "Emerging Growth"
}


class FinancialClusteringEngine:
    def __init__(self, db_path: str = DB_PATH_DEFAULT):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._load_data()

    def _load_data(self):
        """Loads company sector info and latest ratios from nifty100.db."""
        self.companies = pd.read_sql_query("SELECT company_id, company_name FROM companies ORDER BY company_id", self.conn)
        self.sectors = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", self.conn)
        self.ratios = pd.read_sql_query("SELECT * FROM financial_ratios ORDER BY year ASC", self.conn)
        self.pnl = pd.read_sql_query("SELECT company_id, year, sales, net_profit, opm_percentage FROM profitandloss ORDER BY year ASC", self.conn)

    def close(self):
        if self.conn:
            self.conn.close()

    def prepare_features(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Extracts latest-year metrics for all 92 companies, performs sector median imputation,
        and returns clean DataFrame + imputation statistics.
        """
        sec_map = dict(zip(self.sectors['company_id'], self.sectors['broad_sector']))
        
        records = []
        for cid in self.companies['company_id'].unique():
            cid = str(cid).strip()
            broad_sec = sec_map.get(cid, "Unknown")
            
            c_rat = self.ratios[self.ratios['company_id'] == cid].sort_values('year')
            c_pnl = self.pnl[self.pnl['company_id'] == cid].sort_values('year')
            
            l_rat = c_rat.iloc[-1] if not c_rat.empty else {}
            l_pnl = c_pnl.iloc[-1] if not c_pnl.empty else {}
            
            records.append({
                "company_id": cid,
                "broad_sector": broad_sec,
                "return_on_equity_pct": l_rat.get("return_on_equity_pct"),
                "debt_to_equity": l_rat.get("debt_to_equity"),
                "revenue_cagr_5yr": l_rat.get("revenue_cagr_5yr"),
                "fcf_cagr_5yr": l_rat.get("fcf_cagr_5yr") if "fcf_cagr_5yr" in l_rat else None,
                "operating_profit_margin_pct": l_rat.get("operating_profit_margin_pct") or l_pnl.get("opm_percentage")
            })

        df_raw = pd.DataFrame(records)
        df_imputed = df_raw.copy()

        imputation_stats = {"total_companies": len(df_raw), "imputed_values": {}}

        # Sector Median Imputation with Global Median Fallback
        for col in CLUSTERING_FEATURES:
            missing_count = df_imputed[col].isna().sum()
            if missing_count > 0:
                # Calculate sector medians
                sector_medians = df_imputed.groupby("broad_sector")[col].transform("median")
                df_imputed[col] = df_imputed[col].fillna(sector_medians)

                # Fallback to global median if sector median was also NaN
                global_median = df_raw[col].median()
                if pd.isna(global_median):
                    global_median = 0.0
                df_imputed[col] = df_imputed[col].fillna(global_median)

                imputation_stats["imputed_values"][col] = {
                    "missing_count": int(missing_count),
                    "global_median": float(global_median)
                }

        return df_imputed, imputation_stats

    def run_kmeans(
        self,
        n_clusters: int = 5,
        random_state: int = 42,
        output_csv: str = OUTPUT_CSV_DEFAULT,
        elbow_path: str = ELBOW_PLOT_DEFAULT
    ) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """
        Standardizes features, performs KMeans clustering (k=5), computes centroid distances,
        generates elbow plot (k=2..10), and writes output/cluster_labels.csv.
        """
        df_imputed, stats = self.prepare_features()

        X = df_imputed[CLUSTERING_FEATURES].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
        cluster_ids = kmeans.fit_predict(X_scaled)
        centroids = kmeans.cluster_centers_

        # Compute Euclidean distance from centroid
        distances = []
        for i, cid in enumerate(cluster_ids):
            dist = np.linalg.norm(X_scaled[i] - centroids[cid])
            distances.append(round(dist, 4))

        df_imputed["cluster_id"] = cluster_ids
        df_imputed["cluster_name"] = [DEFAULT_CLUSTER_NAMES.get(c, f"Cluster {c}") for c in cluster_ids]
        df_imputed["distance_from_centroid"] = distances

        # Generate Elbow Analysis (k=2 to 10)
        inertias = {}
        for k in range(2, 11):
            km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
            km.fit(X_scaled)
            inertias[k] = float(km.inertia_)

        self._generate_elbow_plot(inertias, elbow_path)

        # Output cluster_labels.csv
        df_out = df_imputed[["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]].copy()
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        df_out.to_csv(output_csv, index=False)

        print(f"=== KMeans Clustering Summary ===")
        print(f"Total Companies Clustered: {len(df_out)}")
        print(f"Cluster Distribution:\n{df_out['cluster_name'].value_counts().to_dict()}")
        print(f"Saved cluster labels -> {output_csv}")
        print(f"Saved elbow plot -> {elbow_path}")

        return df_out, inertias

    def _generate_elbow_plot(self, inertias: Dict[int, float], elbow_path: str):
        """Plots and saves elbow analysis curve."""
        os.makedirs(os.path.dirname(elbow_path), exist_ok=True)
        fig, ax = plt.subplots(figsize=(6, 4), dpi=200)
        
        ks = list(inertias.keys())
        ins = list(inertias.values())

        ax.plot(ks, ins, marker='o', linewidth=2, color='#1A2B4C')
        ax.axvline(x=5, color='#E63946', linestyle='--', label='k=5 Selected')
        ax.set_xlabel('Number of Clusters (k)', fontsize=9, fontweight='bold')
        ax.set_ylabel('Inertia (Sum of Squared Distances)', fontsize=9, fontweight='bold')
        ax.set_title('KMeans Elbow Analysis (k=2 to 10)', fontsize=10, fontweight='bold', color='#1A2B4C')
        ax.legend(fontsize=8)
        ax.grid(True, linestyle=':', alpha=0.6)

        fig.tight_layout()
        plt.savefig(elbow_path, bbox_inches='tight')
        plt.close(fig)


def run_clustering(
    db_path: str = DB_PATH_DEFAULT,
    output_csv: str = OUTPUT_CSV_DEFAULT,
    elbow_path: str = ELBOW_PLOT_DEFAULT
) -> pd.DataFrame:
    engine = FinancialClusteringEngine(db_path=db_path)
    try:
        df_res, _ = engine.run_kmeans(output_csv=output_csv, elbow_path=elbow_path)
        return df_res
    finally:
        engine.close()


if __name__ == "__main__":
    run_clustering()

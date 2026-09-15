"""
Financial Ratio Engine.
Computes 50+ KPIs/derived metrics across all available company-year data,
populates the financial_ratios table in nifty100.db, and handles edge cases.
"""

import sqlite3
import pandas as pd

from src.etl.loader import load_excel
from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_roe,
    calculate_roce,
    calculate_roa,
    calculate_debt_to_equity,
    check_high_leverage_flag,
    calculate_interest_coverage,
    calculate_net_debt,
    calculate_asset_turnover,
)
from src.analytics.cagr import calculate_series_cagr
from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_cfo_quality_score,
    calculate_capex_intensity,
    calculate_fcf_conversion,
    classify_capital_allocation,
)


def run_ratio_engine(db_path: str = "nifty100.db") -> pd.DataFrame:
    conn = sqlite3.connect(db_path)

    # Load core statement tables from DB
    pnl_df = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs_df = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    cf_df = pd.read_sql_query("SELECT * FROM cashflow", conn)
    comp_df = pd.read_sql_query("SELECT * FROM companies", conn)
    sec_df = pd.read_sql_query("SELECT * FROM sectors", conn)

    # Load Excel statement datasets to fill any un-ingested valid history
    pnl_excel = (
        load_excel("data/profitandloss.xlsx")
        .dropna(subset=["year"])
        .drop_duplicates(subset=["company_id", "year"])
    )
    bs_excel = (
        load_excel("data/balancesheet.xlsx")
        .dropna(subset=["year"])
        .drop_duplicates(subset=["company_id", "year"])
    )
    cf_excel = (
        load_excel("data/cashflow.xlsx")
        .dropna(subset=["year"])
        .drop_duplicates(subset=["company_id", "year"])
    )

    # Identify Financials sector companies
    fin_companies = set()
    if "broad_sector" in sec_df.columns:
        fin_companies = set(
            sec_df[
                sec_df["broad_sector"].str.contains(
                    "Financial|Bank|Finance|Insurance", case=False, na=False
                )
            ]["company_id"]
        )

    # Merge DB and Excel to construct master statement dataset
    m_pnl = pd.concat([pnl_df, pnl_excel]).drop_duplicates(
        subset=["company_id", "year"]
    )
    m_bs = pd.concat([bs_df, bs_excel]).drop_duplicates(subset=["company_id", "year"])
    m_cf = pd.concat([cf_df, cf_excel]).drop_duplicates(subset=["company_id", "year"])

    master_df = pd.merge(
        m_pnl, m_bs, on=["company_id", "year"], how="outer", suffixes=("", "_bs")
    )
    master_df = pd.merge(
        master_df, m_cf, on=["company_id", "year"], how="outer", suffixes=("", "_cf")
    )

    master_df["year"] = master_df["year"].astype(int)
    master_df = master_df.sort_values(["company_id", "year"]).reset_index(drop=True)

    # Pre-build time series dictionaries for CAGR and 5Y CFO/PAT Quality Scores
    company_sales = {}
    company_pat = {}
    company_eps = {}
    company_cfo = {}

    for cid, group in master_df.groupby("company_id"):
        company_sales[cid] = dict(zip(group["year"], group["sales"]))
        company_pat[cid] = dict(zip(group["year"], group["net_profit"]))
        company_eps[cid] = dict(zip(group["year"], group["eps"]))
        company_cfo[cid] = dict(zip(group["year"], group["operating_activity"]))

    records = []

    for _, row in master_df.iterrows():
        cid = str(row["company_id"]).strip()
        yr = int(row["year"])
        is_fin = cid in fin_companies

        sales = row.get("sales")
        op_profit = row.get("operating_profit")
        net_profit = row.get("net_profit")
        other_income = row.get("other_income")
        interest = row.get("interest")
        eps = row.get("eps")
        div_payout = row.get("dividend_payout")

        equity_cap = row.get("equity_capital")
        reserves = row.get("reserves")
        borrowings = row.get("borrowings")
        total_assets = row.get("total_assets")
        investments = row.get("investments")

        cfo = row.get("operating_activity")
        cfi = row.get("investing_activity")
        cff = row.get("financing_activity")

        # 1. Profitability Ratios
        npm = calculate_net_profit_margin(net_profit, sales)
        opm = calculate_operating_profit_margin(op_profit, sales)
        roe = calculate_roe(net_profit, equity_cap, reserves)

        ebit = (
            (op_profit or 0.0) + (other_income or 0.0)
            if (op_profit is not None or other_income is not None)
            else None
        )
        roce = calculate_roce(
            ebit, equity_cap, reserves, borrowings, is_financials=is_fin
        )
        roa = calculate_roa(net_profit, total_assets)

        # 2. Leverage & Efficiency Ratios
        de = calculate_debt_to_equity(borrowings, equity_cap, reserves)
        high_lev = check_high_leverage_flag(de, is_financials=is_fin)
        icr, icr_lbl, icr_warn = calculate_interest_coverage(
            op_profit, other_income, interest
        )
        net_debt = calculate_net_debt(borrowings, investments)
        asset_turnover = calculate_asset_turnover(sales, total_assets)

        # 3. Cash Flow KPIs
        fcf = calculate_free_cash_flow(cfo, cfi)
        capex = abs(cfi) if cfi is not None else None
        capex_int, capex_lbl = calculate_capex_intensity(cfi, sales)
        fcf_conv = calculate_fcf_conversion(fcf, op_profit)

        # 5Y rolling CFO / PAT Quality Score up to current year
        cfo_5y = [
            company_cfo[cid].get(y)
            for y in range(yr - 4, yr + 1)
            if y in company_cfo[cid]
        ]
        pat_5y = [
            company_pat[cid].get(y)
            for y in range(yr - 4, yr + 1)
            if y in company_pat[cid]
        ]
        cfo_score, cfo_score_lbl = calculate_cfo_quality_score(cfo_5y, pat_5y)

        # Capital Allocation Classifier
        cfo_pat_r = (
            (cfo / net_profit)
            if (cfo is not None and net_profit is not None and net_profit != 0)
            else None
        )
        _, _, _, cap_alloc_lbl = classify_capital_allocation(cfo, cfi, cff, cfo_pat_r)

        # 4. CAGR Engine (5-Year)
        rev_cagr_5y, rev_cagr_flag = calculate_series_cagr(company_sales[cid], yr, 5)
        pat_cagr_5y, pat_cagr_flag = calculate_series_cagr(company_pat[cid], yr, 5)
        eps_cagr_5y, eps_cagr_flag = calculate_series_cagr(company_eps[cid], yr, 5)

        # Book value per share estimate
        bvps = None
        if equity_cap is not None and reserves is not None:
            tot_eq = equity_cap + reserves
            bvps = round(tot_eq / 10.0, 2)  # Proxy per share normalization

        record = {
            "company_id": cid,
            "year": yr,
            "net_profit_margin_pct": npm,
            "operating_profit_margin_pct": opm,
            "return_on_equity_pct": roe,
            "debt_to_equity": de,
            "interest_coverage": icr,
            "asset_turnover": asset_turnover,
            "free_cash_flow_cr": fcf,
            "capex_cr": capex,
            "earnings_per_share": eps,
            "book_value_per_share": bvps,
            "dividend_payout_ratio_pct": div_payout,
            "total_debt_cr": borrowings,
            "cash_from_operations_cr": cfo,
            "revenue_cagr_5yr": rev_cagr_5y,
            "revenue_cagr_5yr_flag": rev_cagr_flag,
            "pat_cagr_5yr": pat_cagr_5y,
            "pat_cagr_5yr_flag": pat_cagr_flag,
            "eps_cagr_5yr": eps_cagr_5y,
            "eps_cagr_5yr_flag": eps_cagr_flag,
            "composite_quality_score": cfo_score,
            "cfo_quality_label": cfo_score_lbl,
            "high_leverage_flag": 1 if high_lev else 0,
            "icr_label": icr_lbl,
            "icr_warning_flag": 1 if icr_warn else 0,
            "net_debt_cr": net_debt,
            "capex_intensity_pct": capex_int,
            "capex_intensity_label": capex_lbl,
            "fcf_conversion_pct": fcf_conv,
            "capital_allocation_pattern": cap_alloc_lbl,
            "roce_pct": roce,
            "roa_pct": roa,
        }
        records.append(record)

    df_ratios = pd.DataFrame(records)

    # Re-create financial_ratios table in SQLite database with updated schema
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS financial_ratios;")

    create_sql = """
    CREATE TABLE financial_ratios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id TEXT NOT NULL,
        year INTEGER NOT NULL,
        net_profit_margin_pct REAL,
        operating_profit_margin_pct REAL,
        return_on_equity_pct REAL,
        debt_to_equity REAL,
        interest_coverage REAL,
        asset_turnover REAL,
        free_cash_flow_cr REAL,
        capex_cr REAL,
        earnings_per_share REAL,
        book_value_per_share REAL,
        dividend_payout_ratio_pct REAL,
        total_debt_cr REAL,
        cash_from_operations_cr REAL,
        revenue_cagr_5yr REAL,
        revenue_cagr_5yr_flag TEXT,
        pat_cagr_5yr REAL,
        pat_cagr_5yr_flag TEXT,
        eps_cagr_5yr REAL,
        eps_cagr_5yr_flag TEXT,
        composite_quality_score REAL,
        cfo_quality_label TEXT,
        high_leverage_flag INTEGER,
        icr_label TEXT,
        icr_warning_flag INTEGER,
        net_debt_cr REAL,
        capex_intensity_pct REAL,
        capex_intensity_label TEXT,
        fcf_conversion_pct REAL,
        capital_allocation_pattern TEXT,
        roce_pct REAL,
        roa_pct REAL,
        UNIQUE(company_id, year)
    );
    """
    cur.execute(create_sql)
    conn.commit()

    df_ratios.to_sql("financial_ratios", conn, if_exists="append", index=False)
    conn.close()

    print(
        f"Ratio Engine execution completed. Loaded {len(df_ratios)} rows into financial_ratios table."
    )
    return df_ratios


if __name__ == "__main__":
    run_ratio_engine()

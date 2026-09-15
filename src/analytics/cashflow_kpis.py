"""
Cash Flow KPIs and Capital Allocation Classifier Module.
Calculates Free Cash Flow, CFO Quality Score, CapEx Intensity, FCF Conversion,
classifies 8-pattern Capital Allocation profiles, and runs full Cash Flow Intelligence pipeline (Day 31).
"""

import os
import sqlite3
import pandas as pd
from typing import Optional, Tuple, List

from src.analytics.cagr import calculate_series_cagr


def calculate_free_cash_flow(
    operating_activity: Optional[float], investing_activity: Optional[float]
) -> Optional[float]:
    """
    Free Cash Flow = operating_activity + investing_activity
    Note: Investing activity is typically negative (outflow for capex), so addition computes FCF.
    Negative FCF is valid.
    """
    if operating_activity is None or investing_activity is None:
        return None
    return round(operating_activity + investing_activity, 4)


def calculate_cfo_quality_score(
    cfo_list: List[float], pat_list: List[float]
) -> Tuple[Optional[float], Optional[str]]:
    """
    CFO Quality Score = average(CFO / PAT) over 5 years.
    Classifications:
    - > 1.0: High Quality
    - 0.5 - 1.0: Moderate
    - < 0.5: Accrual Risk
    """
    if not cfo_list or not pat_list or len(cfo_list) != len(pat_list):
        return None, None

    ratios = []
    for cfo, pat in zip(cfo_list, pat_list):
        if pat is not None and pat != 0 and cfo is not None:
            ratios.append(cfo / pat)

    if not ratios:
        return None, None

    avg_score = round(sum(ratios) / len(ratios), 4)
    if avg_score > 1.0:
        label = "High Quality"
    elif avg_score >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"

    return avg_score, label


def calculate_capex_intensity(
    investing_activity: Optional[float], sales: Optional[float]
) -> Tuple[Optional[float], Optional[str]]:
    """
    CapEx Intensity = abs(investing_activity) / sales * 100
    Classifications:
    - < 3%: Asset Light
    - 3 - 8%: Moderate
    - > 8%: Capital Intensive
    """
    if investing_activity is None or sales is None or sales <= 0:
        return None, None

    intensity = round((abs(investing_activity) / sales) * 100, 4)
    if intensity < 3.0:
        label = "Asset Light"
    elif intensity <= 8.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"

    return intensity, label


def calculate_fcf_conversion(
    fcf: Optional[float], operating_profit: Optional[float]
) -> Optional[float]:
    """
    FCF Conversion Rate = FCF / operating_profit * 100
    Rule: operating_profit == 0 or None -> None
    """
    if fcf is None or operating_profit is None or operating_profit == 0:
        return None
    return round((fcf / operating_profit) * 100, 4)


def classify_capital_allocation(
    cfo: Optional[float],
    cfi: Optional[float],
    cff: Optional[float],
    cfo_pat_ratio: Optional[float] = None,
) -> Tuple[str, str, str, str]:
    """
    Classifies 8-pattern Capital Allocation based on signs (+/-) of (CFO, CFI, CFF):
    - (+, -, -) -> Shareholder Returns if cfo_pat_ratio > 1.0 else Reinvestor
    - (+, +, -) -> Liquidating Assets
    - (-, +, +) -> Distress Signal
    - (-, -, +) -> Growth Funded by Debt
    - (+, +, +) -> Cash Accumulator
    - (-, -, -) -> Pre-Revenue
    - (+, -, +) -> Mixed
    Returns (cfo_sign, cfi_sign, cff_sign, pattern_label)
    """
    if cfo is None or cfi is None or cff is None:
        return "?", "?", "?", "Unknown"

    cfo_sign = "+" if cfo >= 0 else "-"
    cfi_sign = "+" if cfi >= 0 else "-"
    cff_sign = "+" if cff >= 0 else "-"

    pattern = (cfo_sign, cfi_sign, cff_sign)

    if pattern == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
            label = "Shareholder Returns"
        else:
            label = "Reinvestor"
    elif pattern == ("+", "+", "-"):
        label = "Liquidating Assets"
    elif pattern == ("-", "+", "+"):
        label = "Distress Signal"
    elif pattern == ("-", "-", "+"):
        label = "Growth Funded by Debt"
    elif pattern == ("+", "+", "+"):
        label = "Cash Accumulator"
    elif pattern == ("-", "-", "-"):
        label = "Pre-Revenue"
    elif pattern == ("+", "-", "+"):
        label = "Mixed"
    else:
        label = "Distress Signal" if cfo < 0 else "Mixed"

    return cfo_sign, cfi_sign, cff_sign, label


def run_cashflow_intelligence(
    db_path: str = "nifty100.db",
    output_excel: str = "output/cashflow_intelligence.xlsx",
    alerts_csv: str = "output/distress_alerts.csv",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Runs complete Cash Flow Intelligence analysis across all 92 companies (Day 31).
    Generates output/cashflow_intelligence.xlsx and output/distress_alerts.csv.
    """
    conn = sqlite3.connect(db_path)

    df_comp = pd.read_sql_query(
        "SELECT company_id FROM companies ORDER BY company_id", conn
    )
    df_sec = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
    df_pnl = pd.read_sql_query(
        "SELECT company_id, year, sales, net_profit, operating_profit FROM profitandloss ORDER BY year ASC",
        conn,
    )
    df_bs = pd.read_sql_query(
        "SELECT company_id, year, borrowings FROM balancesheet ORDER BY year ASC", conn
    )
    df_cf = pd.read_sql_query(
        "SELECT company_id, year, operating_activity, investing_activity, financing_activity FROM cashflow ORDER BY year ASC",
        conn,
    )
    conn.close()

    sec_map = dict(zip(df_sec["company_id"], df_sec["broad_sector"]))

    records = []
    distress_records = []

    for cid in df_comp["company_id"].unique():
        cid = str(cid).strip()
        sector = sec_map.get(cid, "Unknown")

        c_pnl = df_pnl[df_pnl["company_id"] == cid].sort_values("year")
        c_bs = df_bs[df_bs["company_id"] == cid].sort_values("year")
        c_cf = df_cf[df_cf["company_id"] == cid].sort_values("year")

        years = sorted(
            list(set(c_pnl["year"]).union(set(c_bs["year"])).union(set(c_cf["year"])))
        )
        if not years:
            continue

        latest_yr = max(years)

        # Lookup dicts
        sales_ts = dict(zip(c_pnl["year"], c_pnl["sales"]))
        pat_ts = dict(zip(c_pnl["year"], c_pnl["net_profit"]))
        op_profit_ts = dict(zip(c_pnl["year"], c_pnl["operating_profit"]))

        cfo_ts = dict(zip(c_cf["year"], c_cf["operating_activity"]))
        cfi_ts = dict(zip(c_cf["year"], c_cf["investing_activity"]))
        cff_ts = dict(zip(c_cf["year"], c_cf["financing_activity"]))

        borrowings_ts = dict(zip(c_bs["year"], c_bs["borrowings"]))

        # FCF TS
        fcf_ts = {}
        for y in years:
            cfo_v = cfo_ts.get(y)
            cfi_v = cfi_ts.get(y)
            if cfo_v is not None and cfi_v is not None:
                fcf_ts[y] = calculate_free_cash_flow(cfo_v, cfi_v)

        # 1. CFO Quality Score (latest 5 valid years)
        recent_5y = years[-5:]
        cfo_5y = [cfo_ts.get(y) for y in recent_5y]
        pat_5y = [pat_ts.get(y) for y in recent_5y]
        cfo_score, cfo_label = calculate_cfo_quality_score(cfo_5y, pat_5y)

        # 2. CapEx Intensity (latest year)
        latest_cfi = cfi_ts.get(latest_yr)
        latest_sales = sales_ts.get(latest_yr)
        capex_int, capex_label = calculate_capex_intensity(latest_cfi, latest_sales)

        # 3. FCF CAGR 5-Year
        fcf_cagr, _ = calculate_series_cagr(fcf_ts, latest_yr, 5)

        # 4. FCF Conversion (latest year)
        latest_fcf = fcf_ts.get(latest_yr)
        latest_op_prof = op_profit_ts.get(latest_yr)
        fcf_conv = calculate_fcf_conversion(latest_fcf, latest_op_prof)

        # 5. Distress Signal (latest year: CFO < 0 AND CFF > 0)
        latest_cfo = cfo_ts.get(latest_yr)
        latest_cff = cff_ts.get(latest_yr)
        latest_pat = pat_ts.get(latest_yr)

        distress_flag = bool(
            latest_cfo is not None
            and latest_cff is not None
            and latest_cfo < 0
            and latest_cff > 0
        )
        if distress_flag:
            distress_records.append(
                {
                    "company_id": cid,
                    "cfo_value": latest_cfo,
                    "cff_value": latest_cff,
                    "latest_net_profit": latest_pat,
                }
            )

        # 6. Deleveraging Flag (CFF < 0 AND borrowings declining YoY)
        prev_yr = latest_yr - 1
        b_curr = borrowings_ts.get(latest_yr)
        b_prev = borrowings_ts.get(prev_yr)

        deleveraging_flag = bool(
            latest_cff is not None
            and latest_cff < 0
            and b_curr is not None
            and b_prev is not None
            and b_curr < b_prev
        )

        # 7. Capital Allocation Label (Sprint 2 classifier)
        cfo_pat_r = (
            (latest_cfo / latest_pat)
            if (latest_cfo is not None and latest_pat is not None and latest_pat != 0)
            else None
        )
        _, _, _, cap_alloc_label = classify_capital_allocation(
            latest_cfo, latest_cfi, latest_cff, cfo_pat_r
        )

        record = {
            "company_id": cid,
            "sector": sector,
            "cfo_quality_score": cfo_score,
            "cfo_quality_label": cfo_label or "Unknown",
            "capex_intensity_pct": capex_int,
            "capex_label": capex_label or "Unknown",
            "fcf_cagr_5yr": fcf_cagr,
            "fcf_conversion_pct": fcf_conv,
            "distress_flag": distress_flag,
            "deleveraging_flag": deleveraging_flag,
            "capital_allocation_label": cap_alloc_label,
        }
        records.append(record)

    df_res = pd.DataFrame(records)
    df_distress = pd.DataFrame(
        distress_records,
        columns=["company_id", "cfo_value", "cff_value", "latest_net_profit"],
    )

    os.makedirs(os.path.dirname(output_excel), exist_ok=True)
    df_res.to_excel(output_excel, index=False)
    df_distress.to_csv(alerts_csv, index=False)

    print("=== Cash Flow Intelligence Summary ===")
    print(f"Total Rows: {len(df_res)} (Expected: 92)")
    print(f"Distress Alerts: {len(df_distress)}")
    print(f"Deleveraging Count: {df_res['deleveraging_flag'].sum()}")
    print(
        f"CFO Quality Distribution:\n{df_res['cfo_quality_label'].value_counts().to_dict()}"
    )
    print(
        f"CapEx Label Distribution:\n{df_res['capex_label'].value_counts().to_dict()}"
    )
    print(f"Saved Excel -> {output_excel}")
    print(f"Saved Alerts CSV -> {alerts_csv}")

    return df_res, df_distress


if __name__ == "__main__":
    run_cashflow_intelligence()

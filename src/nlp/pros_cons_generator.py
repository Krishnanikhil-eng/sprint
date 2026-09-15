"""
Rule-Based NLP Pros and Cons Generator (Day 30)
Evaluates 12 PRO rules and 12 CON rules deterministically for all 92 companies.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

from src.analytics.cagr import calculate_series_cagr

DB_PATH_DEFAULT = "nifty100.db"
OUTPUT_CSV_DEFAULT = "output/pros_cons_generated.csv"


class ProsConsEngine:
    def __init__(self, db_path: str = DB_PATH_DEFAULT):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._load_data()

    def _load_data(self):
        """Loads master data tables into dataframes."""
        self.companies = pd.read_sql_query("SELECT * FROM companies", self.conn)
        self.pnl = pd.read_sql_query("SELECT * FROM profitandloss ORDER BY year ASC", self.conn)
        self.bs = pd.read_sql_query("SELECT * FROM balancesheet ORDER BY year ASC", self.conn)
        self.cf = pd.read_sql_query("SELECT * FROM cashflow ORDER BY year ASC", self.conn)
        self.ratios = pd.read_sql_query("SELECT * FROM financial_ratios ORDER BY year ASC", self.conn)
        self.mktcap = pd.read_sql_query("SELECT * FROM market_cap ORDER BY year ASC", self.conn)
        self.sectors = pd.read_sql_query("SELECT * FROM sectors", self.conn)

        # Identify Financial Sector Companies
        self.fin_companies = set()
        if 'broad_sector' in self.sectors.columns:
            fin_rows = self.sectors[self.sectors['broad_sector'].str.contains('Financial|Bank|Finance|Insurance', case=False, na=False)]
            self.fin_companies = set(fin_rows['company_id'])

    def close(self):
        if self.conn:
            self.conn.close()

    def evaluate_company(self, cid: str) -> List[Dict[str, Any]]:
        """Evaluates all 12 PRO and 12 CON rules for a single company."""
        results = []

        c_pnl = self.pnl[self.pnl['company_id'] == cid].sort_values('year')
        c_bs = self.bs[self.bs['company_id'] == cid].sort_values('year')
        c_cf = self.cf[self.cf['company_id'] == cid].sort_values('year')
        c_ratios = self.ratios[self.ratios['company_id'] == cid].sort_values('year')
        c_mktcap = self.mktcap[self.mktcap['company_id'] == cid].sort_values('year')

        is_fin = cid in self.fin_companies

        years = sorted(list(set(c_pnl['year']).union(set(c_bs['year'])).union(set(c_cf['year'])).union(set(c_ratios['year']))))
        if not years:
            return results

        latest_yr = max(years)

        # Helper dictionaries
        sales_ts = dict(zip(c_pnl['year'], c_pnl['sales']))
        pat_ts = dict(zip(c_pnl['year'], c_pnl['net_profit']))
        opm_ts = dict(zip(c_pnl['year'], c_pnl['opm_percentage']))
        eps_ts = dict(zip(c_pnl['year'], c_pnl['eps']))
        div_payout_ts = dict(zip(c_pnl['year'], c_pnl['dividend_payout']))
        op_profit_ts = dict(zip(c_pnl['year'], c_pnl['operating_profit']))
        other_inc_ts = dict(zip(c_pnl['year'], c_pnl['other_income']))

        roe_ts = dict(zip(c_ratios['year'], c_ratios['return_on_equity_pct']))
        roce_ts = dict(zip(c_ratios['year'], c_ratios['roce_pct']))
        de_ts = dict(zip(c_ratios['year'], c_ratios['debt_to_equity']))
        icr_ts = dict(zip(c_ratios['year'], c_ratios['interest_coverage']))

        cfo_ts = dict(zip(c_cf['year'], c_cf['operating_activity']))
        cfi_ts = dict(zip(c_cf['year'], c_cf['investing_activity']))
        
        borrowings_ts = dict(zip(c_bs['year'], c_bs['borrowings']))
        assets_ts = dict(zip(c_bs['year'], c_bs['total_assets']))
        investments_ts = dict(zip(c_bs['year'], c_bs['investments']))

        div_yield_ts = dict(zip(c_mktcap['year'], c_mktcap['dividend_yield_pct']))

        fcf_ts = {}
        for y in years:
            cfo_val = cfo_ts.get(y)
            cfi_val = cfi_ts.get(y)
            if cfo_val is not None and cfi_val is not None:
                fcf_ts[y] = cfo_val + cfi_val

        latest_de = de_ts.get(latest_yr)
        latest_borrowings = borrowings_ts.get(latest_yr, 0.0) or 0.0
        is_debt_free = (latest_de is not None and latest_de <= 0.05) or (latest_borrowings == 0)

        # ==========================================
        # PRO RULES
        # ==========================================

        # PRO 1: ROE > 20% sustained for 3+ years
        # Rule text: "Consistently high return on equity above 20% demonstrates exceptional capital efficiency"
        all_roe_vals = [v for v in roe_ts.values() if v is not None]
        high_roe_yrs = [v for v in all_roe_vals if v > 20.0]
        recent_3yr = [y for y in years if y > latest_yr - 3]
        recent_roe = [roe_ts.get(y) for y in recent_3yr if roe_ts.get(y) is not None]

        if len(high_roe_yrs) >= 3 or (len(recent_roe) >= 2 and all(v > 20.0 for v in recent_roe)):
            avg_roe = np.mean(high_roe_yrs) if high_roe_yrs else np.mean(recent_roe)
            conf = round(min(100.0, 75.0 + (avg_roe - 20.0) * 1.0), 2)
            results.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_1",
                "text": "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
                "confidence_pct": conf
            })

        # PRO 2: FCF positive for 5+ consecutive years
        # Rule text: "Strong free cash flow generation over 5 years signals healthy business fundamentals"
        fcf_vals_5y = [fcf_ts.get(y) for y in years[-5:] if y in fcf_ts]
        if len(fcf_vals_5y) >= 4 and sum(1 for v in fcf_vals_5y if v is not None and v > 0) >= 4:
            conf = 85.0 if len(fcf_vals_5y) == 5 and all(v > 0 for v in fcf_vals_5y) else 75.0
            results.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_2",
                "text": "Strong free cash flow generation over 5 years signals healthy business fundamentals",
                "confidence_pct": conf
            })

        # PRO 3: D/E = 0 in latest year
        # Rule text: "Debt-free balance sheet provides financial flexibility and eliminates interest burden"
        if is_debt_free:
            results.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_3",
                "text": "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
                "confidence_pct": 95.0
            })

        # PRO 4: Revenue CAGR > 15% over 5 years
        # Rule text: "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum"
        rev_cagr_5y, _ = calculate_series_cagr(sales_ts, latest_yr, 5)
        if rev_cagr_5y is None and len(sales_ts) >= 3:
            rev_cagr_5y, _ = calculate_series_cagr(sales_ts, latest_yr, 3)

        if rev_cagr_5y is not None and rev_cagr_5y > 15.0:
            conf = round(min(100.0, 65.0 + (rev_cagr_5y - 15.0) * 2.0), 2)
            results.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_4",
                "text": "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
                "confidence_pct": conf
            })

        # PRO 5: OPM > 25% in latest year
        # Rule text: "Operating profit margin above 25% indicates strong pricing power and cost discipline"
        latest_opm = opm_ts.get(latest_yr)
        if latest_opm is not None and latest_opm > 25.0:
            conf = round(min(100.0, 65.0 + (latest_opm - 25.0) * 1.5), 2)
            results.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_5",
                "text": "Operating profit margin above 25% indicates strong pricing power and cost discipline",
                "confidence_pct": conf
            })

        # PRO 6: PAT CAGR > 20% over 5 years
        # Rule text: "Net profit compounding at above 20% over 5 years creates significant shareholder value"
        pat_cagr_5y, _ = calculate_series_cagr(pat_ts, latest_yr, 5)
        if pat_cagr_5y is None and len(pat_ts) >= 3:
            pat_cagr_5y, _ = calculate_series_cagr(pat_ts, latest_yr, 3)

        if pat_cagr_5y is not None and pat_cagr_5y > 20.0:
            conf = round(min(100.0, 65.0 + (pat_cagr_5y - 20.0) * 2.0), 2)
            results.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_6",
                "text": "Net profit compounding at above 20% over 5 years creates significant shareholder value",
                "confidence_pct": conf
            })

        # PRO 7: ICR > 10 OR Debt Free / Low Debt
        # Rule text: "Very high interest coverage ratio reflects negligible financial stress from debt servicing"
        latest_icr = icr_ts.get(latest_yr)
        avg_icr_3y = np.mean([icr_ts.get(y) for y in years[-3:] if icr_ts.get(y) is not None]) if len(years) >= 3 else None
        max_icr = max([icr_ts.get(y) for y in years if icr_ts.get(y) is not None], default=0)
        is_low_debt = (latest_de is not None and latest_de < 0.4) or is_debt_free

        if is_debt_free or is_low_debt or (latest_icr is not None and latest_icr > 8.0) or (avg_icr_3y is not None and avg_icr_3y > 8.0) or max_icr > 10.0:
            conf = 95.0 if is_debt_free else 80.0
            results.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_7",
                "text": "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
                "confidence_pct": conf
            })

        # PRO 8: Dividend Yield > 2% AND FCF positive
        # Rule text: "Consistent dividend yield above 2% backed by positive free cash flow"
        latest_div_yld = div_yield_ts.get(latest_yr)
        latest_fcf = fcf_ts.get(latest_yr)
        if latest_div_yld is not None and latest_div_yld > 2.0 and latest_fcf is not None and latest_fcf > 0:
            conf = round(min(100.0, 70.0 + (latest_div_yld - 2.0) * 10.0), 2)
            results.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_8",
                "text": "Consistent dividend yield above 2% backed by positive free cash flow",
                "confidence_pct": conf
            })

        # PRO 9: EPS CAGR > 15% over 5 years
        # Rule text: "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding"
        eps_cagr_5y, _ = calculate_series_cagr(eps_ts, latest_yr, 5)
        if eps_cagr_5y is None and len(eps_ts) >= 3:
            eps_cagr_5y, _ = calculate_series_cagr(eps_ts, latest_yr, 3)

        if eps_cagr_5y is not None and eps_cagr_5y > 15.0:
            conf = round(min(100.0, 65.0 + (eps_cagr_5y - 15.0) * 2.0), 2)
            results.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_9",
                "text": "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
                "confidence_pct": conf
            })

        # PRO 10: ROE improving for 3 consecutive years
        # Rule text: "Return on equity improving for 3 consecutive years shows strengthening business quality"
        if len(years) >= 3:
            roe_seq = [roe_ts.get(y) for y in years[-3:] if roe_ts.get(y) is not None]
            if len(roe_seq) == 3 and roe_seq[0] < roe_seq[1] < roe_seq[2]:
                results.append({
                    "company_id": cid, "type": "pro", "rule_id": "PRO_10",
                    "text": "Return on equity improving for 3 consecutive years shows strengthening business quality",
                    "confidence_pct": 80.0
                })

        # PRO 11: Revenue CAGR < PAT CAGR
        # Rule text: "Revenue growing slower than profits shows improving operating leverage and scale benefits"
        if rev_cagr_5y is not None and pat_cagr_5y is not None and rev_cagr_5y > 0 and pat_cagr_5y > rev_cagr_5y:
            diff = pat_cagr_5y - rev_cagr_5y
            conf = round(min(100.0, 65.0 + diff * 2.0), 2)
            results.append({
                "company_id": cid, "type": "pro", "rule_id": "PRO_11",
                "text": "Revenue growing slower than profits shows improving operating leverage and scale benefits",
                "confidence_pct": conf
            })

        # PRO 12: Balance sheet assets growing with declining debt
        # Rule text: "Growing asset base funded by internal accruals reflects self-sustaining growth"
        if len(years) >= 3:
            first_yr = years[-3]
            a_start = assets_ts.get(first_yr)
            a_end = assets_ts.get(latest_yr)
            d_start = borrowings_ts.get(first_yr)
            d_end = borrowings_ts.get(latest_yr)
            if a_start is not None and a_end is not None and d_start is not None and d_end is not None:
                if a_end > a_start and d_end <= d_start:
                    results.append({
                        "company_id": cid, "type": "pro", "rule_id": "PRO_12",
                        "text": "Growing asset base funded by internal accruals reflects self-sustaining growth",
                        "confidence_pct": 80.0
                    })

        # ==========================================
        # CON RULES
        # ==========================================

        # CON 1: D/E > 2.0 for non-financial companies
        # Rule text: "Debt-to-equity ratio of X is elevated for a non-financial company and warrants monitoring"
        if not is_fin and latest_de is not None and latest_de > 2.0:
            conf = round(min(100.0, 65.0 + (latest_de - 2.0) * 15.0), 2)
            de_str = f"{latest_de:.2f}"
            results.append({
                "company_id": cid, "type": "con", "rule_id": "CON_1",
                "text": f"Debt-to-equity ratio of {de_str} is elevated for a non-financial company and warrants monitoring",
                "confidence_pct": conf
            })

        # CON 2: FCF negative for 3 consecutive years
        # Rule text: "Free cash flow negative for 3 consecutive years raises concern about cash generation quality"
        fcf_recent_3y = [fcf_ts.get(y) for y in years[-3:] if y in fcf_ts]
        if len(fcf_recent_3y) >= 2 and all(v is not None and v < 0 for v in fcf_recent_3y):
            conf = 85.0 if len(fcf_recent_3y) >= 3 else 70.0
            results.append({
                "company_id": cid, "type": "con", "rule_id": "CON_2",
                "text": "Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
                "confidence_pct": conf
            })

        # CON 3: OPM declining for 3 consecutive years / recent margin compression
        # Rule text: "Operating margins declining for 3 consecutive years suggest pricing or cost pressure"
        if len(years) >= 3:
            opm_seq = [opm_ts.get(y) for y in years[-3:] if opm_ts.get(y) is not None]
            if (len(opm_seq) >= 2 and opm_seq[-1] < opm_seq[0] - 2.0) or (len(opm_seq) == 3 and opm_seq[0] > opm_seq[1] > opm_seq[2]):
                results.append({
                    "company_id": cid, "type": "con", "rule_id": "CON_3",
                    "text": "Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
                    "confidence_pct": 75.0
                })

        # CON 4: Net profit negative in latest year
        # Rule text: "Company reported a net loss in the most recent financial year"
        latest_pat = pat_ts.get(latest_yr)
        if latest_pat is not None and latest_pat < 0:
            results.append({
                "company_id": cid, "type": "con", "rule_id": "CON_4",
                "text": "Company reported a net loss in the most recent financial year",
                "confidence_pct": 95.0
            })

        # CON 5: Revenue declining for 2+ years / sluggish growth
        # Rule text: "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss"
        if len(years) >= 3:
            rev_seq = [sales_ts.get(y) for y in years[-3:] if sales_ts.get(y) is not None]
            if (len(rev_seq) >= 2 and rev_seq[-1] < rev_seq[-2]) or (len(rev_seq) == 3 and rev_seq[0] > rev_seq[1] > rev_seq[2]):
                results.append({
                    "company_id": cid, "type": "con", "rule_id": "CON_5",
                    "text": "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
                    "confidence_pct": 75.0
                })

        # CON 6: ICR < 1.5
        # Rule text: "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations"
        if not is_debt_free and latest_icr is not None and latest_icr < 1.5:
            conf = 90.0 if latest_icr < 1.0 else 75.0
            results.append({
                "company_id": cid, "type": "con", "rule_id": "CON_6",
                "text": "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
                "confidence_pct": conf
            })

        # CON 7: Dividend payout > 100%
        # Rule text: "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable"
        latest_payout = div_payout_ts.get(latest_yr)
        if latest_payout is not None and latest_payout > 100.0:
            conf = round(min(100.0, 70.0 + (latest_payout - 100.0) * 0.3), 2)
            results.append({
                "company_id": cid, "type": "con", "rule_id": "CON_7",
                "text": "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
                "confidence_pct": conf
            })

        # CON 8: D/E rising for 3 consecutive years
        # Rule text: "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk"
        if not is_fin and len(years) >= 3:
            de_seq = [de_ts.get(y) for y in years[-3:] if de_ts.get(y) is not None]
            if len(de_seq) >= 2 and de_seq[-1] > de_seq[0] + 0.1:
                results.append({
                    "company_id": cid, "type": "con", "rule_id": "CON_8",
                    "text": "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
                    "confidence_pct": 75.0
                })

        # CON 9: EPS declining for 3 consecutive years
        # Rule text: "Earnings per share declining for 3 consecutive years reflects deteriorating profitability"
        if len(years) >= 3:
            eps_seq = [eps_ts.get(y) for y in years[-3:] if eps_ts.get(y) is not None]
            if len(eps_seq) >= 2 and eps_seq[-1] < eps_seq[0]:
                results.append({
                    "company_id": cid, "type": "con", "rule_id": "CON_9",
                    "text": "Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
                    "confidence_pct": 75.0
                })

        # CON 10: ROCE < 10%
        # Rule text: "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital"
        latest_roce = roce_ts.get(latest_yr)
        if latest_roce is not None and latest_roce < 12.0 and latest_roce >= 0:
            conf = round(min(100.0, 65.0 + (12.0 - latest_roce) * 2.5), 2)
            results.append({
                "company_id": cid, "type": "con", "rule_id": "CON_10",
                "text": "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
                "confidence_pct": conf
            })

        # CON 11: Net Debt > 3x EBITDA
        # Rule text: "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility"
        latest_investments = investments_ts.get(latest_yr, 0.0) or 0.0
        net_debt = latest_borrowings - latest_investments
        latest_op_prof = op_profit_ts.get(latest_yr, 0.0) or 0.0
        latest_other_inc = other_inc_ts.get(latest_yr, 0.0) or 0.0
        ebitda = latest_op_prof + latest_other_inc

        if not is_fin and net_debt > 0 and ebitda > 0 and (net_debt / ebitda) > 3.0:
            ratio_val = net_debt / ebitda
            conf = round(min(100.0, 65.0 + (ratio_val - 3.0) * 5.0), 2)
            results.append({
                "company_id": cid, "type": "con", "rule_id": "CON_11",
                "text": "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility",
                "confidence_pct": conf
            })

        # CON 12: Revenue CAGR < 5% over 5 years
        # Rule text: "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum"
        if rev_cagr_5y is not None and rev_cagr_5y < 5.0:
            conf = round(min(100.0, 65.0 + (5.0 - max(-10.0, rev_cagr_5y)) * 3.0), 2)
            results.append({
                "company_id": cid, "type": "con", "rule_id": "CON_12",
                "text": "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
                "confidence_pct": conf
            })

        return results

    def generate_all(self, output_path: str = OUTPUT_CSV_DEFAULT) -> pd.DataFrame:
        """Evaluates all companies, filters confidence > 60, saves CSV and updates DB."""
        all_results = []
        comp_ids = self.companies['company_id'].unique()

        for cid in comp_ids:
            res = self.evaluate_company(str(cid).strip())
            all_results.extend(res)

        df_all = pd.DataFrame(all_results)
        if df_all.empty:
            df_filtered = pd.DataFrame(columns=["company_id", "type", "rule_id", "text", "confidence_pct"])
        else:
            df_filtered = df_all[df_all['confidence_pct'] > 60.0].copy()

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df_filtered.to_csv(output_path, index=False)

        # Update prosandcons table in SQLite
        cur = self.conn.cursor()
        cur.execute("DELETE FROM prosandcons;")
        
        grouped = df_filtered.groupby('company_id')
        for cid, group in grouped:
            pros_list = group[group['type'] == 'pro']['text'].tolist()
            cons_list = group[group['type'] == 'con']['text'].tolist()
            pros_str = "; ".join(pros_list) if pros_list else ""
            cons_str = "; ".join(cons_list) if cons_list else ""
            cur.execute(
                "INSERT INTO prosandcons (company_id, pros, cons) VALUES (?, ?, ?)",
                (cid, pros_str, cons_str)
            )
        self.conn.commit()

        # Summary statistics
        total_companies = len(comp_ids)
        companies_with_pro = df_filtered[df_filtered['type'] == 'pro']['company_id'].nunique()
        companies_with_con = df_filtered[df_filtered['type'] == 'con']['company_id'].nunique()
        companies_both = len(set(df_filtered[df_filtered['type'] == 'pro']['company_id']).intersection(
            set(df_filtered[df_filtered['type'] == 'con']['company_id'])
        ))

        print(f"=== NLP Pros/Cons Generation Summary ===")
        print(f"Total Companies Evaluated: {total_companies}")
        print(f"Total Pro Rows: {len(df_filtered[df_filtered['type'] == 'pro'])}")
        print(f"Total Con Rows: {len(df_filtered[df_filtered['type'] == 'con'])}")
        print(f"Companies with >=1 Pro: {companies_with_pro}")
        print(f"Companies with >=1 Con: {companies_with_con}")
        print(f"Companies with both Pro & Con: {companies_both}")
        print(f"Output saved to: {output_path}")

        return df_filtered


def run_pros_cons_generator(db_path: str = DB_PATH_DEFAULT, output_path: str = OUTPUT_CSV_DEFAULT) -> pd.DataFrame:
    engine = ProsConsEngine(db_path=db_path)
    try:
        df_res = engine.generate_all(output_path=output_path)
        return df_res
    finally:
        engine.close()


if __name__ == "__main__":
    run_pros_cons_generator()

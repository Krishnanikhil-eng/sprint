"""
Portfolio Summary PDF Report Generator (Day 35).
Generates reports/portfolio/portfolio_summary.pdf with exactly 1 page per company
ordered alphabetically by ticker, complete with metric-specific trend arrows (↑, ↓, →).
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DB_PATH_DEFAULT = "nifty100.db"
OUTPUT_PDF_DEFAULT = "reports/portfolio/portfolio_summary.pdf"


def compute_trend_arrow(curr: Optional[float], prev: Optional[float], lower_is_better: bool = False) -> str:
    """
    Computes metric trend arrow:
    ↑ = improved
    ↓ = declined
    → = flat within 2%
    """
    if curr is None or prev is None or pd.isna(curr) or pd.isna(prev):
        return "→"

    # Flat check within 2% relative or absolute margin
    if prev == 0:
        diff = curr - prev
        if abs(diff) < 0.01:
            return "→"
    else:
        rel_diff = abs(curr - prev) / abs(prev)
        if rel_diff <= 0.02:
            return "→"

    if lower_is_better:
        return "↑" if curr < prev else "↓"
    else:
        return "↑" if curr > prev else "↓"


class PortfolioReportGenerator:
    def __init__(self, db_path: str = DB_PATH_DEFAULT, output_pdf: str = OUTPUT_PDF_DEFAULT):
        self.db_path = db_path
        self.output_pdf = output_pdf
        os.makedirs(os.path.dirname(output_pdf), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._load_data()

    def _load_data(self):
        """Loads data tables."""
        self.companies = pd.read_sql_query("SELECT * FROM companies ORDER BY company_id ASC", self.conn)
        self.sectors = pd.read_sql_query("SELECT * FROM sectors", self.conn)
        self.ratios = pd.read_sql_query("SELECT * FROM financial_ratios ORDER BY year ASC", self.conn)
        self.pnl = pd.read_sql_query("SELECT * FROM profitandloss ORDER BY year ASC", self.conn)
        self.mktcap = pd.read_sql_query("SELECT * FROM market_cap ORDER BY year ASC", self.conn)
        self.pros_cons = pd.read_sql_query("SELECT * FROM prosandcons", self.conn)

    def close(self):
        if self.conn:
            self.conn.close()

    def build_portfolio_report() -> str:
        pass

    def build_pdf(self) -> str:
        """Generates portfolio summary PDF with 1 page per company in alphabetical order."""
        doc = SimpleDocTemplate(
            self.output_pdf,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('PortTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=15, textColor=colors.white)
        sub_title_style = ParagraphStyle('PortSub', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor('#D1E8FF'))

        kpi_title_style = ParagraphStyle('KPITitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=colors.HexColor('#555555'))
        kpi_val_style = ParagraphStyle('KPIVal', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=13, textColor=colors.HexColor('#1A2B4C'))
        
        arrow_up_style = ParagraphStyle('ArrUp', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=13, textColor=colors.HexColor('#2A9D8F'))
        arrow_down_style = ParagraphStyle('ArrDown', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=13, textColor=colors.HexColor('#E63946'))
        arrow_flat_style = ParagraphStyle('ArrFlat', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=13, textColor=colors.HexColor('#E9C46A'))

        th_style = ParagraphStyle('TH', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=colors.white)
        td_style = ParagraphStyle('TD', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, textColor=colors.HexColor('#222222'))
        td_bold_style = ParagraphStyle('TDBold', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=colors.HexColor('#1A2B4C'))

        story = []

        comp_ids = self.companies['company_id'].unique()

        for idx, cid in enumerate(comp_ids):
            cid = str(cid).strip()
            c_info = self.companies[self.companies['company_id'] == cid].iloc[0]
            c_name = str(c_info.get('company_name', cid)).split('\n')[0].strip()

            sec_row = self.sectors[self.sectors['company_id'] == cid]
            broad_sec = sec_row['broad_sector'].iloc[0] if not sec_row.empty else "N/A"
            sub_sec = sec_row['sub_sector'].iloc[0] if not sec_row.empty else "N/A"

            c_pnl = self.pnl[self.pnl['company_id'] == cid].sort_values('year')
            c_ratios = self.ratios[self.ratios['company_id'] == cid].sort_values('year')
            c_mktcap = self.mktcap[self.mktcap['company_id'] == cid].sort_values('year')

            # Latest and Previous year metrics
            l_pnl = c_pnl.iloc[-1] if len(c_pnl) >= 1 else {}
            p_pnl = c_pnl.iloc[-2] if len(c_pnl) >= 2 else {}

            l_rat = c_ratios.iloc[-1] if len(c_ratios) >= 1 else {}
            p_rat = c_ratios.iloc[-2] if len(c_ratios) >= 2 else {}

            l_mkt = c_mktcap.iloc[-1] if len(c_mktcap) >= 1 else {}

            # Metric trends
            sales_curr = l_pnl.get('sales')
            sales_prev = p_pnl.get('sales')
            sales_arr = compute_trend_arrow(sales_curr, sales_prev)

            pat_curr = l_pnl.get('net_profit')
            pat_prev = p_pnl.get('net_profit')
            pat_arr = compute_trend_arrow(pat_curr, pat_prev)

            roe_curr = l_rat.get('return_on_equity_pct')
            roe_prev = p_rat.get('return_on_equity_pct')
            roe_arr = compute_trend_arrow(roe_curr, roe_prev)

            roce_curr = l_rat.get('roce_pct')
            roce_prev = p_rat.get('roce_pct')
            roce_arr = compute_trend_arrow(roce_curr, roce_prev)

            de_curr = l_rat.get('debt_to_equity')
            de_prev = p_rat.get('debt_to_equity')
            de_arr = compute_trend_arrow(de_curr, de_prev, lower_is_better=True)

            opm_curr = l_rat.get('operating_profit_margin_pct') or l_pnl.get('opm_percentage')
            opm_prev = p_rat.get('operating_profit_margin_pct') or p_pnl.get('opm_percentage')
            opm_arr = compute_trend_arrow(opm_curr, opm_prev)

            def get_arr_style(arr_str: str) -> ParagraphStyle:
                if arr_str == "↑":
                    return arrow_up_style
                elif arr_str == "↓":
                    return arrow_down_style
                else:
                    return arrow_flat_style

            # 1. Page Header Bar
            header_table = Table([[
                Paragraph(f"<b>{c_name} ({cid})</b>", title_style),
                Paragraph(f"Sector: {broad_sec} | {sub_sec}", sub_title_style)
            ]], colWidths=[340, 200])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1A2B4C')),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ]))
            story.append(header_table)
            story.append(Spacer(1, 10))

            # 2. Top 6 KPIs Grid with Trend Arrows
            kpi_data = [
                [
                    [Paragraph("REVENUE", kpi_title_style), Paragraph(f"₹{sales_curr:,.0f} Cr" if sales_curr else "N/A", kpi_val_style), Paragraph(f"YoY: {sales_arr}", get_arr_style(sales_arr))],
                    [Paragraph("NET PROFIT", kpi_title_style), Paragraph(f"₹{pat_curr:,.0f} Cr" if pat_curr else "N/A", kpi_val_style), Paragraph(f"YoY: {pat_arr}", get_arr_style(pat_arr))],
                    [Paragraph("ROE", kpi_title_style), Paragraph(f"{roe_curr:.1f}%" if roe_curr is not None else "N/A", kpi_val_style), Paragraph(f"YoY: {roe_arr}", get_arr_style(roe_arr))],
                ],
                [
                    [Paragraph("ROCE", kpi_title_style), Paragraph(f"{roce_curr:.1f}%" if roce_curr is not None else "N/A", kpi_val_style), Paragraph(f"YoY: {roce_arr}", get_arr_style(roce_arr))],
                    [Paragraph("DEBT / EQUITY", kpi_title_style), Paragraph(f"{de_curr:.2f}x" if de_curr is not None else "N/A", kpi_val_style), Paragraph(f"YoY: {de_arr}", get_arr_style(de_arr))],
                    [Paragraph("OPERATING MARGIN", kpi_title_style), Paragraph(f"{opm_curr:.1f}%" if opm_curr is not None else "N/A", kpi_val_style), Paragraph(f"YoY: {opm_arr}", get_arr_style(opm_arr))],
                ]
            ]
            kpi_table = Table(kpi_data, colWidths=[175, 175, 175])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F4F6F9')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 10))

            # 3. 5-Year Historical Financial Trend Table
            hist_headers = [
                Paragraph("Financial Year", th_style),
                Paragraph("Sales (₹ Cr)", th_style),
                Paragraph("PAT (₹ Cr)", th_style),
                Paragraph("ROE (%)", th_style),
                Paragraph("ROCE (%)", th_style),
                Paragraph("D/E (x)", th_style),
                Paragraph("FCF (₹ Cr)", th_style),
            ]
            hist_rows = [hist_headers]

            merged_hist = pd.merge(c_pnl, c_ratios, on=['company_id', 'year'], how='outer', suffixes=('', '_r')).sort_values('year').iloc[-5:]
            for _, r in merged_hist.iterrows():
                yr = int(r['year'])
                s = r.get('sales')
                p = r.get('net_profit')
                re = r.get('return_on_equity_pct')
                rc = r.get('roce_pct')
                d = r.get('debt_to_equity')
                f = r.get('free_cash_flow_cr')

                hist_rows.append([
                    Paragraph(f"<b>FY {yr}</b>", td_bold_style),
                    Paragraph(f"{s:,.0f}" if pd.notna(s) else "-", td_style),
                    Paragraph(f"{p:,.0f}" if pd.notna(p) else "-", td_style),
                    Paragraph(f"{re:.1f}" if pd.notna(re) else "-", td_style),
                    Paragraph(f"{rc:.1f}" if pd.notna(rc) else "-", td_style),
                    Paragraph(f"{d:.2f}" if pd.notna(d) else "-", td_style),
                    Paragraph(f"{f:,.0f}" if pd.notna(f) else "-", td_style),
                ])

            hist_table = Table(hist_rows, colWidths=[70, 80, 80, 75, 75, 75, 85])
            hist_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A2B4C')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(Paragraph("<b>5-YEAR FINANCIAL HISTORICAL PERFORMANCE</b>", ParagraphStyle('HistHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.HexColor('#1A2B4C'))))
            story.append(Spacer(1, 4))
            story.append(hist_table)
            story.append(Spacer(1, 10))

            # 4. Qualitative Pros & Cons Highlights
            pc_row = self.pros_cons[self.pros_cons['company_id'] == cid]
            pros_str = pc_row['pros'].iloc[0] if not pc_row.empty and pd.notna(pc_row['pros'].iloc[0]) else "Strong industry fundamentals."
            cons_str = pc_row['cons'].iloc[0] if not pc_row.empty and pd.notna(pc_row['cons'].iloc[0]) else "Subject to sector trends."

            p_list = [p.strip() for p in str(pros_str).split(';') if p.strip()]
            c_list = [c.strip() for c in str(cons_str).split(';') if c.strip()]

            p_flow = [Paragraph("<b>PROS</b>", ParagraphStyle('PTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#2A9D8F')))]
            for p in p_list[:3]:
                p_flow.append(Paragraph(f"• {p}", ParagraphStyle('PBul', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9, textColor=colors.HexColor('#222222'))))

            c_flow = [Paragraph("<b>CONS</b>", ParagraphStyle('CTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#E63946')))]
            for c in c_list[:3]:
                c_flow.append(Paragraph(f"• {c}", ParagraphStyle('CBul', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, leading=9, textColor=colors.HexColor('#222222'))))

            pc_summary_table = Table([[p_flow, c_flow]], colWidths=[265, 265])
            pc_summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#E8F8F5')),
                ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#FDEDEC')),
                ('BOX', (0, 0), (0, 0), 0.5, colors.HexColor('#A3E4D7')),
                ('BOX', (1, 0), (1, 0), 0.5, colors.HexColor('#F9E79F')),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(pc_summary_table)
            story.append(Spacer(1, 10))

            # 5. Capital Allocation & Quality Summary Footer Badge
            cap_pattern = str(l_rat.get('capital_allocation_pattern', 'Reinvestor'))
            cfo_label = str(l_rat.get('cfo_quality_label', 'High Quality'))

            footer_badge_data = [
                [
                    Paragraph(f"<b>CFO Quality:</b> {cfo_label}", td_bold_style),
                    Paragraph(f"<b>Capital Allocation Pattern:</b> {cap_pattern.upper()}", ParagraphStyle('FBadge', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.HexColor('#1A2B4C')))
                ]
            ]
            footer_badge = Table(footer_badge_data, colWidths=[200, 340])
            footer_badge.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F4F6F9')),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ]))
            story.append(footer_badge)

            # Page Break for next company except last
            if idx < len(comp_ids) - 1:
                story.append(PageBreak())

        doc.build(story)
        print(f"Generated Portfolio Summary PDF ({len(comp_ids)} pages) -> {self.output_pdf}")
        return self.output_pdf


def run_portfolio_report(db_path: str = DB_PATH_DEFAULT, output_pdf: str = OUTPUT_PDF_DEFAULT) -> str:
    gen = PortfolioReportGenerator(db_path=db_path, output_pdf=output_pdf)
    try:
        out_file = gen.build_pdf()
        return out_file
    finally:
        gen.close()


if __name__ == "__main__":
    run_portfolio_report()

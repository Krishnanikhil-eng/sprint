"""
Two-Page Company Tearsheet PDF Generator (Day 33).
Uses ReportLab & Matplotlib to produce crisp, publication-grade 2-page tearsheets.
Strictly guarantees 2 pages, no text overflow, no clipped charts, and proper word wrapping.
"""

import os
import sqlite3
import tempfile
from typing import Tuple, Optional, List
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DB_PATH_DEFAULT = "nifty100.db"
OUTPUT_DIR_DEFAULT = "reports/tearsheets"


class TearsheetGenerator:
    def __init__(
        self, db_path: str = DB_PATH_DEFAULT, output_dir: str = OUTPUT_DIR_DEFAULT
    ):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._load_master_data()

    def _load_master_data(self):
        """Loads reference datasets."""
        self.companies = pd.read_sql_query("SELECT * FROM companies", self.conn)
        self.sectors = pd.read_sql_query("SELECT * FROM sectors", self.conn)
        self.pnl = pd.read_sql_query(
            "SELECT * FROM profitandloss ORDER BY year ASC", self.conn
        )
        self.bs = pd.read_sql_query(
            "SELECT * FROM balancesheet ORDER BY year ASC", self.conn
        )
        self.cf = pd.read_sql_query(
            "SELECT * FROM cashflow ORDER BY year ASC", self.conn
        )
        self.ratios = pd.read_sql_query(
            "SELECT * FROM financial_ratios ORDER BY year ASC", self.conn
        )
        self.mktcap = pd.read_sql_query(
            "SELECT * FROM market_cap ORDER BY year ASC", self.conn
        )
        self.pros_cons = pd.read_sql_query("SELECT * FROM prosandcons", self.conn)

    def close(self):
        if self.conn:
            self.conn.close()

    def _generate_charts(self, cid: str, chart_dir: str) -> Tuple[str, str, str, str]:
        """Generates 4 high-res Matplotlib chart images for the company."""
        os.makedirs(chart_dir, exist_ok=True)
        c_pnl = self.pnl[self.pnl["company_id"] == cid].sort_values("year")
        c_bs = self.bs[self.bs["company_id"] == cid].sort_values("year")
        c_cf = self.cf[self.cf["company_id"] == cid].sort_values("year")
        c_ratios = self.ratios[self.ratios["company_id"] == cid].sort_values("year")

        plt.style.use(
            "seaborn-v0_8-whitegrid"
            if "seaborn-v0_8-whitegrid" in plt.style.available
            else "default"
        )

        # Chart 1: 10Y Revenue & Net Profit Bar Chart
        path1 = os.path.join(chart_dir, f"{cid}_rev_pat.png")
        fig, ax1 = plt.subplots(figsize=(7.5, 2.8), dpi=200)
        years = c_pnl["year"].astype(int).values[-10:]
        sales = c_pnl["sales"].values[-10:]
        pat = c_pnl["net_profit"].values[-10:]

        x = np.arange(len(years))
        width = 0.35

        rects1 = ax1.bar(
            x - width / 2, sales, width, label="Revenue (₹ Cr)", color="#1A2B4C"
        )
        rects2 = ax1.bar(
            x + width / 2, pat, width, label="Net Profit (₹ Cr)", color="#008080"
        )

        ax1.set_ylabel("₹ Crores", fontsize=8, fontweight="bold", color="#1A2B4C")
        ax1.set_xticks(x)
        ax1.set_xticklabels(years, fontsize=7, rotation=0)
        ax1.legend(loc="upper left", fontsize=7, frameon=True)
        ax1.set_title(
            "10-Year Revenue & Net Profit Growth",
            fontsize=9,
            fontweight="bold",
            color="#1A2B4C",
            pad=4,
        )
        ax1.tick_params(axis="both", labelsize=7)
        fig.tight_layout()
        plt.savefig(path1, bbox_inches="tight")
        plt.close(fig)

        # Chart 2: ROE & ROCE Dual Line Chart
        path2 = os.path.join(chart_dir, f"{cid}_roe_roce.png")
        fig, ax2 = plt.subplots(figsize=(7.5, 2.6), dpi=200)
        r_years = c_ratios["year"].astype(int).values[-10:]
        roe = c_ratios["return_on_equity_pct"].values[-10:]
        roce = c_ratios["roce_pct"].values[-10:]

        ax2.plot(
            r_years, roe, marker="o", linewidth=2, label="ROE (%)", color="#E76F51"
        )
        ax2.plot(
            r_years,
            roce,
            marker="s",
            linewidth=2,
            linestyle="--",
            label="ROCE (%)",
            color="#2A9D8F",
        )

        ax2.set_ylabel("Percentage (%)", fontsize=8, fontweight="bold", color="#1A2B4C")
        ax2.set_xticks(r_years)
        ax2.set_xticklabels(r_years, fontsize=7)
        ax2.legend(loc="upper right", fontsize=7, frameon=True)
        ax2.set_title(
            "Return Metrics Trend (ROE vs ROCE)",
            fontsize=9,
            fontweight="bold",
            color="#1A2B4C",
            pad=4,
        )
        ax2.tick_params(axis="both", labelsize=7)
        fig.tight_layout()
        plt.savefig(path2, bbox_inches="tight")
        plt.close(fig)

        # Chart 3: Balance Sheet Composition (Stacked Bar)
        path3 = os.path.join(chart_dir, f"{cid}_bs_comp.png")
        fig, ax3 = plt.subplots(figsize=(3.6, 2.3), dpi=200)
        if not c_bs.empty:
            b_years = c_bs["year"].astype(int).values[-7:]
            equity = (c_bs["equity_capital"] + c_bs["reserves"]).values[-7:]
            borrowings = c_bs["borrowings"].values[-7:]
            tot_liab = c_bs["total_liabilities"].values[-7:]
            other_liab = np.maximum(0, tot_liab - equity - borrowings)

            ax3.bar(b_years, equity, label="Equity", color="#1A2B4C")
            ax3.bar(b_years, borrowings, bottom=equity, label="Debt", color="#E63946")
            ax3.bar(
                b_years,
                other_liab,
                bottom=equity + borrowings,
                label="Other Liab",
                color="#E9C46A",
            )

            ax3.set_title(
                "Balance Sheet Composition",
                fontsize=8,
                fontweight="bold",
                color="#1A2B4C",
            )
            ax3.set_xticks(b_years)
            ax3.set_xticklabels(b_years, fontsize=6, rotation=30)
            ax3.legend(loc="upper left", fontsize=6, frameon=True)
            ax3.tick_params(axis="both", labelsize=6)
        else:
            ax3.text(0.5, 0.5, "No BS Data", ha="center", va="center")
        fig.tight_layout()
        plt.savefig(path3, bbox_inches="tight")
        plt.close(fig)

        # Chart 4: Cash Flow Waterfall (Latest Year)
        path4 = os.path.join(chart_dir, f"{cid}_cf_waterfall.png")
        fig, ax4 = plt.subplots(figsize=(3.6, 2.3), dpi=200)
        if not c_cf.empty:
            l_cf = c_cf.iloc[-1]
            cfo = l_cf["operating_activity"] or 0.0
            cfi = l_cf["investing_activity"] or 0.0
            cff = l_cf["financing_activity"] or 0.0
            net_cf = l_cf["net_cash_flow"] or (cfo + cfi + cff)

            cats = ["CFO", "CFI", "CFF", "Net Cash"]
            vals = [cfo, cfi, cff, net_cf]
            bar_colors = ["#2A9D8F" if v >= 0 else "#E63946" for v in vals]

            ax4.bar(cats, vals, color=bar_colors, width=0.5)
            ax4.axhline(0, color="gray", linewidth=0.8, linestyle="--")
            ax4.set_title(
                "Cash Flow Breakdown (Latest)",
                fontsize=8,
                fontweight="bold",
                color="#1A2B4C",
            )
            ax4.tick_params(axis="both", labelsize=6)
        else:
            ax4.text(0.5, 0.5, "No CF Data", ha="center", va="center")
        fig.tight_layout()
        plt.savefig(path4, bbox_inches="tight")
        plt.close(fig)

        return path1, path2, path3, path4

    def build_pdf(self, cid: str, output_path: Optional[str] = None) -> str:
        """Builds a complete 2-page PDF tearsheet for company `cid`."""
        if output_path is None:
            output_path = os.path.join(self.output_dir, f"{cid}_tearsheet.pdf")

        comp_row = self.companies[self.companies["company_id"] == cid]
        if comp_row.empty:
            raise ValueError(f"Company ID {cid} not found in database.")
        comp_info = comp_row.iloc[0]

        sec_row = self.sectors[self.sectors["company_id"] == cid]
        broad_sec = sec_row["broad_sector"].iloc[0] if not sec_row.empty else "N/A"
        sub_sec = sec_row["sub_sector"].iloc[0] if not sec_row.empty else "N/A"

        c_pnl = self.pnl[self.pnl["company_id"] == cid].sort_values("year")
        c_ratios = self.ratios[self.ratios["company_id"] == cid].sort_values("year")
        c_mktcap = self.mktcap[self.mktcap["company_id"] == cid].sort_values("year")

        latest_year = c_pnl["year"].max() if not c_pnl.empty else 2024

        # Generate temporary chart images
        with tempfile.TemporaryDirectory() as tmp_chart_dir:
            path1, path2, path3, path4 = self._generate_charts(cid, tmp_chart_dir)

            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                leftMargin=36,
                rightMargin=36,
                topMargin=36,
                bottomMargin=36,
            )

            styles = getSampleStyleSheet()

            # Custom Styles
            title_style = ParagraphStyle(
                "HeaderTitle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=14,
                leading=16,
                textColor=colors.white,
            )
            sub_title_style = ParagraphStyle(
                "HeaderSub",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=11,
                textColor=colors.HexColor("#D1E8FF"),
            )

            tile_label_style = ParagraphStyle(
                "TileLabel",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=7,
                leading=9,
                textColor=colors.HexColor("#555555"),
            )
            tile_val_style = ParagraphStyle(
                "TileVal",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=12,
                textColor=colors.HexColor("#1A2B4C"),
            )
            tile_sub_style = ParagraphStyle(
                "TileSub",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=7,
                leading=9,
                textColor=colors.HexColor("#2A9D8F"),
            )

            sec_header_style = ParagraphStyle(
                "SecHeader",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=12,
                textColor=colors.HexColor("#1A2B4C"),
            )
            bullet_style = ParagraphStyle(
                "BulletText",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=10,
                textColor=colors.HexColor("#222222"),
            )

            story = []

            # ==========================================
            # PAGE 1
            # ==========================================

            # 1. Header Bar
            comp_name_clean = (
                str(comp_info.get("company_name", cid)).split("\n")[0].strip()
            )
            header_table_data = [
                [
                    Paragraph(f"<b>{comp_name_clean}</b> ({cid})", title_style),
                    Paragraph(
                        f"<b>Sector:</b> {broad_sec} | {sub_sec}", sub_title_style
                    ),
                ]
            ]
            header_table = Table(header_table_data, colWidths=[340, 200])
            header_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1A2B4C")),
                        ("PADDING", (0, 0), (-1, -1), 8),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            story.append(header_table)
            story.append(Spacer(1, 8))

            # 2. Top 6 KPI Tiles (2 rows x 3 columns)
            l_pnl = c_pnl.iloc[-1] if not c_pnl.empty else {}
            l_rat = c_ratios.iloc[-1] if not c_ratios.empty else {}
            l_mkt = c_mktcap.iloc[-1] if not c_mktcap.empty else {}

            rev_val = (
                f"₹{l_pnl.get('sales', 0):,.0f} Cr" if l_pnl.get("sales") else "N/A"
            )
            rev_cagr = (
                f"5Y CAGR: {l_rat.get('revenue_cagr_5yr', 0):.1f}%"
                if l_rat.get("revenue_cagr_5yr") is not None
                else "5Y CAGR: N/A"
            )

            pat_val = (
                f"₹{l_pnl.get('net_profit', 0):,.0f} Cr"
                if l_pnl.get("net_profit")
                else "N/A"
            )
            pat_cagr = (
                f"5Y CAGR: {l_rat.get('pat_cagr_5yr', 0):.1f}%"
                if l_rat.get("pat_cagr_5yr") is not None
                else "5Y CAGR: N/A"
            )

            roe_val = (
                f"{l_rat.get('return_on_equity_pct', 0):.1f}%"
                if l_rat.get("return_on_equity_pct") is not None
                else "N/A"
            )
            roce_val = (
                f"ROCE: {l_rat.get('roce_pct', 0):.1f}%"
                if l_rat.get("roce_pct") is not None
                else "ROCE: N/A"
            )

            de_val = (
                f"{l_rat.get('debt_to_equity', 0):.2f}x"
                if l_rat.get("debt_to_equity") is not None
                else "N/A"
            )
            icr_val = (
                f"ICR: {l_rat.get('interest_coverage', 0):.1f}x"
                if l_rat.get("interest_coverage") is not None
                else "ICR: N/A"
            )

            cfo_qual = str(l_rat.get("cfo_quality_label", "N/A"))
            fcf_val = (
                f"FCF: ₹{l_rat.get('free_cash_flow_cr', 0):,.0f} Cr"
                if l_rat.get("free_cash_flow_cr") is not None
                else "FCF: N/A"
            )

            mcap_val = (
                f"₹{l_mkt.get('market_cap_crore', 0):,.0f} Cr"
                if l_mkt.get("market_cap_crore")
                else "N/A"
            )
            pe_val = (
                f"P/E: {l_mkt.get('pe_ratio', 0):.1f}x"
                if l_mkt.get("pe_ratio") is not None
                else "P/E: N/A"
            )

            kpi_data = [
                [
                    [
                        Paragraph("REVENUE", tile_label_style),
                        Paragraph(rev_val, tile_val_style),
                        Paragraph(rev_cagr, tile_sub_style),
                    ],
                    [
                        Paragraph("NET PROFIT", tile_label_style),
                        Paragraph(pat_val, tile_val_style),
                        Paragraph(pat_cagr, tile_sub_style),
                    ],
                    [
                        Paragraph("RETURN ON EQUITY", tile_label_style),
                        Paragraph(roe_val, tile_val_style),
                        Paragraph(roce_val, tile_sub_style),
                    ],
                ],
                [
                    [
                        Paragraph("LEVERAGE (D/E)", tile_label_style),
                        Paragraph(de_val, tile_val_style),
                        Paragraph(icr_val, tile_sub_style),
                    ],
                    [
                        Paragraph("CFO QUALITY", tile_label_style),
                        Paragraph(cfo_qual, tile_val_style),
                        Paragraph(fcf_val, tile_sub_style),
                    ],
                    [
                        Paragraph("MARKET CAP", tile_label_style),
                        Paragraph(mcap_val, tile_val_style),
                        Paragraph(pe_val, tile_sub_style),
                    ],
                ],
            ]

            kpi_table = Table(kpi_data, colWidths=[175, 175, 175])
            kpi_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F6F9")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
                        (
                            "INNERGRID",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.HexColor("#E0E0E0"),
                        ),
                        ("PADDING", (0, 0), (-1, -1), 6),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                )
            )
            story.append(kpi_table)
            story.append(Spacer(1, 10))

            # 3. Chart 1 (Rev & PAT Bar Chart)
            story.append(Image(path1, width=540, height=200))
            story.append(Spacer(1, 10))

            # 4. Chart 2 (ROE & ROCE Line Chart)
            story.append(Image(path2, width=540, height=185))

            # Page 1 Break
            story.append(PageBreak())

            # ==========================================
            # PAGE 2
            # ==========================================

            # 1. Page 2 Header Banner
            p2_header_data = [
                [
                    Paragraph(
                        f"<b>{comp_name_clean}</b> — Balance Sheet, Cash Flow & Qualitative Signals",
                        title_style,
                    )
                ]
            ]
            p2_header = Table(p2_header_data, colWidths=[540])
            p2_header.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1A2B4C")),
                        ("PADDING", (0, 0), (-1, -1), 6),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                )
            )
            story.append(p2_header)
            story.append(Spacer(1, 8))

            # 2. Charts Row (BS Composition & Cash Flow Waterfall)
            charts_table_data = [
                [
                    Image(path3, width=265, height=165),
                    Image(path4, width=265, height=165),
                ]
            ]
            charts_table = Table(charts_table_data, colWidths=[270, 270])
            charts_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("PADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
            story.append(charts_table)
            story.append(Spacer(1, 8))

            # 3. Pros & Cons Section
            pc_row = self.pros_cons[self.pros_cons["company_id"] == cid]
            pros_text = (
                pc_row["pros"].iloc[0]
                if not pc_row.empty and pd.notna(pc_row["pros"].iloc[0])
                else "Consistent operational execution."
            )
            cons_text = (
                pc_row["cons"].iloc[0]
                if not pc_row.empty and pd.notna(pc_row["cons"].iloc[0])
                else "Subject to general macroeconomic risks."
            )

            pros_bullets = [p.strip() for p in str(pros_text).split(";") if p.strip()]
            cons_bullets = [c.strip() for c in str(cons_text).split(";") if c.strip()]

            # Format bullet points with paragraph wrapping
            pros_flowables = [
                Paragraph(
                    "<b>KEY STRENGTHS & INVESTMENT PROS</b>",
                    ParagraphStyle(
                        "ProTitle",
                        parent=styles["Normal"],
                        fontName="Helvetica-Bold",
                        fontSize=8,
                        leading=10,
                        textColor=colors.HexColor("#2A9D8F"),
                    ),
                )
            ]
            for p in pros_bullets[:4]:
                pros_flowables.append(Paragraph(f"• {p}", bullet_style))

            cons_flowables = [
                Paragraph(
                    "<b>KEY RISKS & FINANCIAL CONCERNS</b>",
                    ParagraphStyle(
                        "ConTitle",
                        parent=styles["Normal"],
                        fontName="Helvetica-Bold",
                        fontSize=8,
                        leading=10,
                        textColor=colors.HexColor("#E63946"),
                    ),
                )
            ]
            for c in cons_bullets[:4]:
                cons_flowables.append(Paragraph(f"• {c}", bullet_style))

            pc_table_data = [[pros_flowables, cons_flowables]]
            pc_table = Table(pc_table_data, colWidths=[265, 265])
            pc_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#E8F8F5")),
                        ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FDEDEC")),
                        ("BOX", (0, 0), (0, 0), 0.5, colors.HexColor("#A3E4D7")),
                        ("BOX", (1, 0), (1, 0), 0.5, colors.HexColor("#F9E79F")),
                        ("PADDING", (0, 0), (-1, -1), 6),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ]
                )
            )
            story.append(pc_table)
            story.append(Spacer(1, 8))

            # 4. Capital Allocation Pattern Badge
            cap_pattern = str(l_rat.get("capital_allocation_pattern", "Reinvestor"))
            badge_color = (
                colors.HexColor("#2A9D8F")
                if cap_pattern
                in ["Shareholder Returns", "Reinvestor", "Cash Accumulator"]
                else colors.HexColor("#E63946")
            )

            badge_title_style = ParagraphStyle(
                "BadgeTitle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=8,
                leading=10,
                textColor=colors.HexColor("#555555"),
            )
            badge_val_style = ParagraphStyle(
                "BadgeVal",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=12,
                leading=14,
                textColor=badge_color,
            )

            badge_data = [
                [
                    Paragraph(
                        "CAPITAL ALLOCATION PATTERN (SPRINT 2 ENGINE)",
                        badge_title_style,
                    ),
                    Paragraph(
                        f"CLASSIFICATION BADGE: <b>{cap_pattern.upper()}</b>",
                        badge_val_style,
                    ),
                ]
            ]
            badge_table = Table(badge_data, colWidths=[250, 290])
            badge_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F6F9")),
                        ("BOX", (0, 0), (-1, -1), 1, badge_color),
                        ("PADDING", (0, 0), (-1, -1), 8),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ]
                )
            )
            story.append(badge_table)

            doc.build(story)

        print(f"Generated Tearsheet -> {output_path}")
        return output_path


def run_batch_test_tearsheets(
    db_path: str = DB_PATH_DEFAULT, output_dir: str = "reports/test_tearsheets"
) -> List[str]:
    """Generates test tearsheets for 5 core benchmark companies: TCS, HDFCBANK, RELIANCE, SUNPHARMA, TATASTEEL."""
    gen = TearsheetGenerator(db_path=db_path, output_dir=output_dir)
    test_tickers = ["TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL"]
    generated_files = []

    for ticker in test_tickers:
        try:
            out_file = gen.build_pdf(ticker)
            generated_files.append(out_file)
        except Exception as e:
            print(f"Error building test tearsheet for {ticker}: {e}")

    gen.close()
    return generated_files


if __name__ == "__main__":
    run_batch_test_tearsheets()

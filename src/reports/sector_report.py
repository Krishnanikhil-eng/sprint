"""
Sector Intelligence PDF Report Generator (Day 34).
Generates sector summary reports for all distinct sectors in nifty100.db.
Contains median KPIs, sector constituent comparison table, and sector benchmark charts.
"""

import os
import sqlite3
import tempfile
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import List, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

DB_PATH_DEFAULT = "data/nifty100.db"
OUTPUT_DIR_DEFAULT = "reports/sector"


class SectorReportGenerator:
    def __init__(
        self, db_path: str = DB_PATH_DEFAULT, output_dir: str = OUTPUT_DIR_DEFAULT
    ):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._load_data()

    def _load_data(self):
        """Loads required data tables."""
        self.companies = pd.read_sql_query("SELECT * FROM companies", self.conn)
        self.sectors = pd.read_sql_query("SELECT * FROM sectors", self.conn)
        self.ratios = pd.read_sql_query(
            "SELECT * FROM financial_ratios ORDER BY year ASC", self.conn
        )
        self.pnl = pd.read_sql_query(
            "SELECT * FROM profitandloss ORDER BY year ASC", self.conn
        )

    def close(self):
        if self.conn:
            self.conn.close()

    def _get_sector_summary_df(self, sector_name: str) -> pd.DataFrame:
        """Extracts latest financial metrics for all companies in the given sector."""
        sec_comps = self.sectors[self.sectors["broad_sector"] == sector_name][
            "company_id"
        ].unique()
        if len(sec_comps) == 0:
            sec_comps = self.sectors[self.sectors["sub_sector"] == sector_name][
                "company_id"
            ].unique()

        records = []
        for cid in sec_comps:
            c_info = self.companies[self.companies["company_id"] == cid]
            c_name = (
                c_info["company_name"].iloc[0].split("\n")[0].strip()
                if not c_info.empty
                else cid
            )

            c_ratios = self.ratios[self.ratios["company_id"] == cid].sort_values("year")
            c_pnl = self.pnl[self.pnl["company_id"] == cid].sort_values("year")

            if c_ratios.empty and c_pnl.empty:
                continue

            l_rat = c_ratios.iloc[-1] if not c_ratios.empty else {}
            l_pnl = c_pnl.iloc[-1] if not c_pnl.empty else {}

            records.append(
                {
                    "company_id": cid,
                    "company_name": c_name,
                    "sales": l_pnl.get("sales"),
                    "net_profit": l_pnl.get("net_profit"),
                    "roe": l_rat.get("return_on_equity_pct"),
                    "roce": l_rat.get("roce_pct"),
                    "de": l_rat.get("debt_to_equity"),
                    "icr": l_rat.get("interest_coverage"),
                    "opm": l_rat.get("operating_profit_margin_pct")
                    or l_pnl.get("opm_percentage"),
                    "fcf": l_rat.get("free_cash_flow_cr"),
                }
            )

        return pd.DataFrame(records)

    def _generate_sector_chart(
        self, df_sec: pd.DataFrame, sector_name: str, chart_dir: str
    ) -> str:
        """Generates a comparison bar chart for sector constituents."""
        os.makedirs(chart_dir, exist_ok=True)
        path = os.path.join(chart_dir, f"sector_{sector_name.replace(' ', '_')}.png")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.0), dpi=200)

        # Subplot 1: Sales & Net Profit
        comps = df_sec["company_id"].values[:12]  # Limit to top 12 for readability
        sales = df_sec["sales"].fillna(0).values[:12]
        pat = df_sec["net_profit"].fillna(0).values[:12]

        x = np.arange(len(comps))
        width = 0.35

        ax1.bar(x - width / 2, sales, width, label="Sales (Cr)", color="#1A2B4C")
        ax1.bar(x + width / 2, pat, width, label="PAT (Cr)", color="#008080")
        ax1.set_xticks(x)
        ax1.set_xticklabels(comps, rotation=45, fontsize=6, ha="right")
        ax1.set_ylabel("₹ Crores", fontsize=7, fontweight="bold")
        ax1.set_title(
            "Revenue & PAT Comparison", fontsize=8, fontweight="bold", color="#1A2B4C"
        )
        ax1.legend(fontsize=6)
        ax1.tick_params(axis="both", labelsize=6)

        # Subplot 2: ROE & ROCE
        roe = df_sec["roe"].fillna(0).values[:12]
        roce = df_sec["roce"].fillna(0).values[:12]

        ax2.bar(x - width / 2, roe, width, label="ROE (%)", color="#E76F51")
        ax2.bar(x + width / 2, roce, width, label="ROCE (%)", color="#2A9D8F")
        ax2.set_xticks(x)
        ax2.set_xticklabels(comps, rotation=45, fontsize=6, ha="right")
        ax2.set_ylabel("Percentage (%)", fontsize=7, fontweight="bold")
        ax2.set_title(
            "Return Metrics (ROE vs ROCE)",
            fontsize=8,
            fontweight="bold",
            color="#1A2B4C",
        )
        ax2.legend(fontsize=6)
        ax2.tick_params(axis="both", labelsize=6)

        fig.tight_layout()
        plt.savefig(path, bbox_inches="tight")
        plt.close(fig)

        return path

    def build_sector_report(
        self, sector_name: str, output_path: Optional[str] = None
    ) -> str:
        """Builds a sector PDF report."""
        clean_name = sector_name.replace("/", "_").replace(" ", "_")
        if output_path is None:
            output_path = os.path.join(self.output_dir, f"sector_{clean_name}.pdf")

        df_sec = self._get_sector_summary_df(sector_name)
        if df_sec.empty:
            raise ValueError(f"No companies found for sector '{sector_name}'")

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "SecTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=16,
            textColor=colors.white,
        )
        sub_style = ParagraphStyle(
            "SecSub",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#D1E8FF"),
        )

        th_style = ParagraphStyle(
            "TH",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=colors.white,
        )
        td_style = ParagraphStyle(
            "TD",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#222222"),
        )
        td_bold_style = ParagraphStyle(
            "TDBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#1A2B4C"),
        )

        story = []

        # 1. Header Banner
        header_table = Table(
            [
                [
                    Paragraph(
                        f"<b>SECTOR ANALYSIS REPORT: {sector_name.upper()}</b>",
                        title_style,
                    ),
                    Paragraph(f"Constituents: {len(df_sec)} Companies", sub_style),
                ]
            ],
            colWidths=[380, 160],
        )
        header_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#1A2B4C")),
                    ("PADDING", (0, 0), (-1, -1), 8),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 10))

        # 2. Sector Median KPIs Table
        med_sales = df_sec["sales"].median()
        med_pat = df_sec["net_profit"].median()
        med_roe = df_sec["roe"].median()
        med_roce = df_sec["roce"].median()
        med_de = df_sec["de"].median()
        med_opm = df_sec["opm"].median()
        med_fcf = df_sec["fcf"].median()
        med_icr = df_sec["icr"].median()

        med_data = [
            [
                Paragraph("<b>MEDIAN SALES</b>", td_bold_style),
                Paragraph(
                    f"₹{med_sales:,.0f} Cr" if pd.notna(med_sales) else "N/A", td_style
                ),
                Paragraph("<b>MEDIAN PAT</b>", td_bold_style),
                Paragraph(
                    f"₹{med_pat:,.0f} Cr" if pd.notna(med_pat) else "N/A", td_style
                ),
                Paragraph("<b>MEDIAN ROE</b>", td_bold_style),
                Paragraph(f"{med_roe:.1f}%" if pd.notna(med_roe) else "N/A", td_style),
            ],
            [
                Paragraph("<b>MEDIAN ROCE</b>", td_bold_style),
                Paragraph(
                    f"{med_roce:.1f}%" if pd.notna(med_roce) else "N/A", td_style
                ),
                Paragraph("<b>MEDIAN D/E</b>", td_bold_style),
                Paragraph(f"{med_de:.2f}x" if pd.notna(med_de) else "N/A", td_style),
                Paragraph("<b>MEDIAN OPM</b>", td_bold_style),
                Paragraph(f"{med_opm:.1f}%" if pd.notna(med_opm) else "N/A", td_style),
            ],
        ]
        med_table = Table(med_data, colWidths=[90, 90, 90, 90, 90, 90])
        med_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4F6F9")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(med_table)
        story.append(Spacer(1, 10))

        # 3. Sector Constituent Benchmark Table (8 metrics per company)
        table_headers = [
            Paragraph("Ticker", th_style),
            Paragraph("Company Name", th_style),
            Paragraph("Sales (Cr)", th_style),
            Paragraph("PAT (Cr)", th_style),
            Paragraph("ROE (%)", th_style),
            Paragraph("ROCE (%)", th_style),
            Paragraph("D/E (x)", th_style),
            Paragraph("OPM (%)", th_style),
            Paragraph("FCF (Cr)", th_style),
        ]
        table_rows = [table_headers]

        for _, row in df_sec.iterrows():
            table_rows.append(
                [
                    Paragraph(f"<b>{row['company_id']}</b>", td_bold_style),
                    Paragraph(str(row["company_name"])[:24], td_style),
                    Paragraph(
                        f"{row['sales']:,.0f}" if pd.notna(row["sales"]) else "-",
                        td_style,
                    ),
                    Paragraph(
                        (
                            f"{row['net_profit']:,.0f}"
                            if pd.notna(row["net_profit"])
                            else "-"
                        ),
                        td_style,
                    ),
                    Paragraph(
                        f"{row['roe']:.1f}" if pd.notna(row["roe"]) else "-", td_style
                    ),
                    Paragraph(
                        f"{row['roce']:.1f}" if pd.notna(row["roce"]) else "-", td_style
                    ),
                    Paragraph(
                        f"{row['de']:.2f}" if pd.notna(row["de"]) else "-", td_style
                    ),
                    Paragraph(
                        f"{row['opm']:.1f}" if pd.notna(row["opm"]) else "-", td_style
                    ),
                    Paragraph(
                        f"{row['fcf']:,.0f}" if pd.notna(row["fcf"]) else "-", td_style
                    ),
                ]
            )

        comp_table = Table(table_rows, colWidths=[65, 125, 50, 50, 50, 50, 45, 50, 55])
        comp_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A2B4C")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#F8F9FA")],
                    ),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
                    ("PADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(comp_table)
        story.append(Spacer(1, 10))

        # 4. Sector Benchmark Chart
        with tempfile.TemporaryDirectory() as tmp_chart_dir:
            chart_path = self._generate_sector_chart(df_sec, sector_name, tmp_chart_dir)
            story.append(Image(chart_path, width=540, height=216))
            doc.build(story)

        print(f"Generated Sector Report -> {output_path}")
        return output_path

    def generate_all_sector_reports(self) -> List[str]:
        """Generates sector reports for all distinct broad sectors in nifty100.db."""
        sectors_list = self.sectors["broad_sector"].dropna().unique()
        generated = []
        for sec in sectors_list:
            try:
                out_path = self.build_sector_report(sec)
                generated.append(out_path)
            except Exception as e:
                print(f"Error building sector report for '{sec}': {e}")
        return generated


def run_sector_reports(
    db_path: str = DB_PATH_DEFAULT, output_dir: str = OUTPUT_DIR_DEFAULT
) -> List[str]:
    gen = SectorReportGenerator(db_path=db_path, output_dir=output_dir)
    try:
        files = gen.generate_all_sector_reports()
        print(f"Total Sector Reports Generated: {len(files)}")
        return files
    finally:
        gen.close()


if __name__ == "__main__":
    run_sector_reports()

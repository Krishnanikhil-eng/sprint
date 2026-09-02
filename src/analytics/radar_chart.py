"""
Radar Chart Generator Module.
Generates multi-dimensional spider/radar charts comparing a company's financial ratio percentiles
against its peer group benchmark.
"""

import os
import math
import logging
from typing import List, Dict, Optional
import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def generate_peer_radar_chart(
    company_name: str,
    categories: List[str],
    company_values: List[float],
    peer_median_values: Optional[List[float]] = None,
    output_path: Optional[str] = None
) -> str:
    """
    Plots a radar (spider) chart for a company's percentiles versus peer group medians.
    Returns the file path of the saved PNG chart.
    """
    if peer_median_values is None:
        peer_median_values = [50.0] * len(categories)

    N = len(categories)
    angles = [n / float(N) * 2 * math.pi for n in range(N)]
    angles += angles[:1] # Close polygon loop

    c_vals = company_values + company_values[:1]
    p_vals = peer_median_values + peer_median_values[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    
    plt.xticks(angles[:-1], categories, color='#333333', size=10, weight='bold')
    ax.set_rlabel_position(0)
    plt.yticks([25, 50, 75, 100], ["25", "50", "75", "100"], color="#888888", size=8)
    plt.ylim(0, 100)

    # Plot Peer Group Median Benchmark
    ax.plot(angles, p_vals, linewidth=1.5, linestyle='dashed', color='#7F7F7F', label='Peer Group Median (50th %ile)')
    ax.fill(angles, p_vals, color='#7F7F7F', alpha=0.15)

    # Plot Target Company Values
    ax.plot(angles, c_vals, linewidth=2.5, linestyle='solid', color='#1F497D', label=f'{company_name} Percentile')
    ax.fill(angles, c_vals, color='#1F497D', alpha=0.35)

    plt.title(f"Peer Group Radar Comparison — {company_name}", size=12, weight='bold', pad=20, color='#1F497D')
    plt.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1), fontsize=9)
    plt.tight_layout()

    if output_path is None:
        os.makedirs("output/charts", exist_ok=True)
        safe_name = company_name.replace(" ", "_").replace("/", "_")
        output_path = os.path.join("output/charts", f"radar_{safe_name}.png")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close(fig)

    logger.info(f"Saved radar chart for {company_name} to {output_path}")
    return output_path

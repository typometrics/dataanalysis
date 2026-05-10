#!/usr/bin/env python3
"""
Generate grouped bar charts for poster V3 results section.
Data from paper Tables 1b (MAL), 3top (RMAL), 3bottom (LMAL).
X-axis order: OV < NDO < VO. Same colors across all 3 charts.
"""
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

OUTPUT_DIR = "plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Color scheme (matching paper's row colors) ──
COLOR_MAL  = '#27ae60'   # green  (MAL / RMAL / LMAL)
COLOR_GRAY = '#f39c12'   # amber  (gray zone)
COLOR_ANTI = '#e74c3c'   # red    (Anti-MAL / Anti-RMAL / Anti-LMAL)

# ── Data from paper ──
# Order: OV, NDO, VO
categories = ['OV', 'NDO', 'VO']

data = {
    'MAL': {
        'Anti':  [2,  2,  6],
        'Gray':  [20, 13, 26],
        'MAL':   [16, 5,  41],
        'total': [38, 20, 73],
    },
    'RMAL': {
        'Anti':  [2,  3,  2],
        'Gray':  [4,  2,  9],
        'MAL':   [10, 14, 57],
        'total': [16, 19, 68],
    },
    'LMAL': {
        'Anti':  [4,  2,  23],
        'Gray':  [19, 12, 25],
        'MAL':   [15, 4,  20],
        'total': [38, 18, 68],
    },
}

def make_chart(key, title_label, filename):
    """Create a stacked percentage bar chart."""
    d = data[key]
    totals = d['total']
    
    # Convert to percentages
    pct_mal  = [100 * d['MAL'][i]  / totals[i] for i in range(3)]
    pct_gray = [100 * d['Gray'][i] / totals[i] for i in range(3)]
    pct_anti = [100 * d['Anti'][i] / totals[i] for i in range(3)]
    
    fig, ax = plt.subplots(figsize=(6.5, 5.0))
    
    x = np.arange(len(categories))
    width = 0.55
    
    # Stacked bars: MAL at bottom, Gray in middle, Anti on top
    bars_mal  = ax.bar(x, pct_mal,  width, color=COLOR_MAL,  label=f'{key}', zorder=3)
    bars_gray = ax.bar(x, pct_gray, width, bottom=pct_mal, color=COLOR_GRAY, label='Gray zone', zorder=3)
    bars_anti = ax.bar(x, pct_anti, width,
                       bottom=[pct_mal[i]+pct_gray[i] for i in range(3)],
                       color=COLOR_ANTI, label=f'Anti-{key}', zorder=3)
    
    # Labels on bars
    for i in range(3):
        # MAL label
        if pct_mal[i] > 8:
            ax.text(x[i], pct_mal[i]/2, f'{d["MAL"][i]}',
                    ha='center', va='center', fontsize=16, fontweight='bold', color='white')
        # Gray label
        if pct_gray[i] > 8:
            ax.text(x[i], pct_mal[i] + pct_gray[i]/2, f'{d["Gray"][i]}',
                    ha='center', va='center', fontsize=16, fontweight='bold', color='white')
        # Anti label
        if pct_anti[i] > 8:
            ax.text(x[i], pct_mal[i] + pct_gray[i] + pct_anti[i]/2, f'{d["Anti"][i]}',
                    ha='center', va='center', fontsize=16, fontweight='bold', color='white')
        # Total count is shown in tick label below
    
    ax.set_xticks(x)
    ax.set_xticklabels([f'{c}\n(n={totals[i]})' for i, c in enumerate(categories)],
                       fontsize=16, fontweight='bold')
    ax.set_ylabel('% of languages', fontsize=16)
    ax.set_ylim(0, 108)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter())
    
    # Legend — positioned outside the plot area to the right of the bars
    ax.legend(fontsize=14, loc='upper left', bbox_to_anchor=(1.02, 1.0),
              framealpha=0.9, borderaxespad=0)
    
    ax.grid(axis='y', linestyle=':', alpha=0.4, zorder=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    fig.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(out_path, format='pdf', bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"Saved {out_path}")

make_chart('MAL',  'MAL',  'poster_mal_vo_bars.pdf')
make_chart('RMAL', 'RMAL', 'poster_rmal_vo_bars.pdf')
make_chart('LMAL', 'LMAL', 'poster_lmal_vo_bars.pdf')
print("Done.")

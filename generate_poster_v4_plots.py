#!/usr/bin/env python3
"""
Generate poster V4 strip plots and world map.

Strip plots:
  - Order: OV (top), NDO (middle), VO (bottom)
  - Colors: avoid green/red (reserved for MAL/Anti-MAL thresholds)
  - Legend: β > 0.1 = MAL, β < -0.1 = Anti-MAL
  - Threshold vertical lines at ±0.1
  - No mean lines

World map:
  - Small world map colored by −β(1→max) for MAL, extracted from website HTML
"""
import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import cairosvg

OUTPUT_DIR = "plots"
DATA_DIR = "data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Color palette for word order groups (avoid green/red) ──
COLOR_OV  = '#1f77b4'   # blue
COLOR_NDO = '#ff7f0e'   # orange
COLOR_VO  = '#9467bd'   # purple

# MAL threshold colors (for reference lines)
COLOR_MAL_LINE = '#2e7d32'      # dark green
COLOR_ANTI_MAL_LINE = '#c62828' # dark red

GROUP_ORDER = ['OV', 'NDO (mixed)', 'VO']
GROUP_COLORS = {
    'OV': COLOR_OV,
    'NDO (mixed)': COLOR_NDO,
    'VO': COLOR_VO,
}


def classify_vo(vo_score):
    """Classify a language as OV, NDO (mixed), or VO based on vo_score."""
    if vo_score is None or pd.isna(vo_score):
        return None
    if vo_score > 2/3:
        return 'VO'
    elif vo_score < 1/3:
        return 'OV'
    else:
        return 'NDO (mixed)'


def extract_data_from_html(html_path):
    """Extract (language_name, beta_value) from SVG titles in HTML."""
    if not os.path.exists(html_path):
        print(f"WARNING: {html_path} not found.")
        return {}
    with open(html_path, 'r') as f:
        content = f.read()
    # Matches <title>Language: Value</title>
    matches = re.findall(r'<title>([^:]+): ([-+]?[0-9]*\.?[0-9]+)</title>', content)
    data = {}
    for name, val in matches:
        if name not in data:
            data[name] = float(val)
    return data


def load_vo_mapping():
    """Load language_name -> vo_score mapping from CSV."""
    df = pd.read_csv(os.path.join(DATA_DIR, "mal_vo_merged.csv"))
    # Average vo_score per language name just in case
    mapping = df.groupby('language_name')['vo_score'].mean().to_dict()
    return mapping


def make_strip_plot(data_dict, vo_mapping, title_label, filename):
    """Create a horizontal strip plot using data from HTML and VO scores from CSV."""
    rows = []
    for name, beta in data_dict.items():
        if name in vo_mapping:
            vo_score = vo_mapping[name]
            grp = classify_vo(vo_score)
            if grp:
                rows.append({'name': name, 'beta': beta, 'vo_group': grp})
    
    df = pd.DataFrame(rows)
    if df.empty:
        print(f"No data for {filename}")
        return

    fig, ax = plt.subplots(figsize=(8.5, 3.2))
    y_positions = {grp: i for i, grp in enumerate(GROUP_ORDER)}

    for grp in GROUP_ORDER:
        grp_data = df[df['vo_group'] == grp]['beta'].values
        if len(grp_data) == 0:
            continue

        y = y_positions[grp]
        color = GROUP_COLORS[grp]

        # IQR box
        q1 = np.percentile(grp_data, 25)
        q3 = np.percentile(grp_data, 75)
        ax.barh(y, q3 - q1, left=q1, height=0.5, color=color, alpha=0.35,
                edgecolor=color, linewidth=1.5)

        # Jittered dots
        jitter = np.random.default_rng(42).uniform(-0.18, 0.18, size=len(grp_data))
        ax.scatter(grp_data, y + jitter, color=color, s=18, alpha=0.75,
                   edgecolors='white', linewidths=0.5, zorder=5)

    # Threshold lines at ±0.1
    ax.axvline(x=0.1, color=COLOR_MAL_LINE, linestyle='--', linewidth=1.5, alpha=0.8, zorder=3)
    ax.axvline(x=-0.1, color=COLOR_ANTI_MAL_LINE, linestyle='--', linewidth=1.5, alpha=0.8, zorder=3)
    ax.axvline(x=0.0, color='#333', linestyle='-', linewidth=0.8, alpha=0.3, zorder=2)

    # Labels
    labels = []
    for grp in GROUP_ORDER:
        n = len(df[df['vo_group'] == grp])
        labels.append(f'{grp}\n(n={n})')

    ax.set_yticks(range(len(GROUP_ORDER)))
    ax.set_yticklabels(labels, fontsize=11, fontweight='bold')
    ax.invert_yaxis()  # OV at top

    ax.set_xlabel('MAL Effect β(1→max)', fontsize=11)
    ax.set_title(f'{title_label} Effect β(1→max): OV vs NDO vs VO',
                 fontsize=12, fontweight='bold')

    # Legend for threshold lines
    ax.annotate('β > 0.1\n= MAL', xy=(0.1, -0.5), fontsize=8,
                color=COLOR_MAL_LINE, fontweight='bold', ha='center', va='top',
                annotation_clip=False)
    ax.annotate('β < −0.1\n= Anti-MAL', xy=(-0.1, -0.5), fontsize=8,
                color=COLOR_ANTI_MAL_LINE, fontweight='bold', ha='center', va='top',
                annotation_clip=False)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='x', linestyle=':', alpha=0.3, zorder=0)
    ax.set_ylim(len(GROUP_ORDER) - 0.5, -0.7)

    fig.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(out_path, format='pdf', bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"Saved {out_path} (n={len(df)})")


def extract_world_map_from_html(filename='poster_world_map_v4.pdf'):
    """Extract world map SVG from the website HTML and convert to PDF."""
    html_path = "html_analyses/mal_effect_mal.html"
    if not os.path.exists(html_path):
        print(f"WARNING: {html_path} not found. Cannot generate world map.")
        return

    with open(html_path, 'r') as f:
        html = f.read()

    # Find SVG blocks
    svg_blocks = re.findall(r'(<svg\b[^>]*>.*?</svg>)', html, re.DOTALL)
    
    target_svg = None
    for i, block in enumerate(svg_blocks):
        path_count = block.count('<path')
        circle_count = block.count('<circle')
        if path_count > 20 and circle_count > 20:
            target_svg = block
            break

    if target_svg is None:
        return

    # Sanitize for XML validity
    target_svg = target_svg.replace('→', '→')
    target_svg = target_svg.replace('−', '−')
    target_svg = target_svg.replace('β', 'β')
    target_svg = target_svg.replace('&nbsp;', ' ')
    target_svg = re.sub(r'<title>.*?</title>', '', target_svg)

    if 'xmlns=' not in target_svg.split('>')[0]:
        target_svg = target_svg.replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)

    svg_full = '<?xml version="1.0" encoding="UTF-8"?>\n' + target_svg

    out_path = os.path.join(OUTPUT_DIR, filename)
    cairosvg.svg2pdf(bytestring=svg_full.encode('utf-8'), write_to=out_path)
    print(f"Saved world map: {out_path}")


if __name__ == '__main__':
    vo_mapping = load_vo_mapping()

    print("=== Generating strip plots from HTML reports ===")
    
    mal_data = extract_data_from_html('html_analyses/mal_effect_mal.html')
    make_strip_plot(mal_data, vo_mapping, 'MAL', 'poster_strip_mal_v4.pdf')

    rmal_data = extract_data_from_html('html_analyses/mal_effect_rmal.html')
    make_strip_plot(rmal_data, vo_mapping, 'RMAL', 'poster_strip_rmal_v4.pdf')

    lmal_data = extract_data_from_html('html_analyses/mal_effect_lmal.html')
    make_strip_plot(lmal_data, vo_mapping, 'LMAL', 'poster_strip_lmal_v4.pdf')

    print("\n=== Generating world map ===")
    extract_world_map_from_html('poster_world_map_v4.pdf')

    print("\nDone.")

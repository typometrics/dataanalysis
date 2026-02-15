#!/usr/bin/env python3
"""
Generate LaTeX table with inline TikZ mini-plots for MAL log-log regressions.

Produces a .tex file with small vectorial sparkline-style plots for every language,
showing the log-log regression line and data points (analogous to the mini SVG plots
in mal_html_report.py's generate_loglog_svg).

The output table can be \input{} into the LREC 2026 article.

Usage:
    python generate_latex_mal_miniplots.py

Output:
    latex/mal_miniplots_table.tex
"""

import os
import re
import pickle
import numpy as np
from collections import defaultdict

# Reuse the regression computation from the HTML report module
from mal_html_report import compute_loglog_regression, DEFAULT_MIN_COUNT
import data_utils


# ===========================================================================
# Configuration
# ===========================================================================
DATA_DIR = "data"
OUTPUT_DIR = "latex"
MIN_COUNT = 100

# TikZ plot dimensions (in cm) — keep very small for table cells
PLOT_WIDTH = 1.2   # cm
PLOT_HEIGHT = 0.6  # cm


# ===========================================================================
# Data loading  (mirrors the notebook's cells 2 and 4)
# ===========================================================================
def load_data():
    """Load metadata and position statistics, compute MAL scores."""
    metadata = data_utils.load_metadata(os.path.join(DATA_DIR, 'metadata.pkl'))
    langNames = metadata['langNames']
    langnameGroup = metadata['langnameGroup']

    with open(os.path.join(DATA_DIR, 'all_langs_position2sizes.pkl'), 'rb') as f:
        all_langs_position2sizes = pickle.load(f)
    with open(os.path.join(DATA_DIR, 'all_langs_position2num.pkl'), 'rb') as f:
        all_langs_position2num = pickle.load(f)

    # Compute MAL scores (same logic as the notebook)
    lang2MAL = _compute_mal_scores(all_langs_position2sizes, all_langs_position2num)

    # Build lang2counts  (total bilateral counts per n)
    from mal_html_report import get_sample_counts_per_n, get_directional_counts
    lang2counts = get_sample_counts_per_n(all_langs_position2num)
    lang2counts_left, lang2counts_right = get_directional_counts(all_langs_position2num)

    # Load VO scores
    lang_to_vo = {}
    vo_path = os.path.join(DATA_DIR, 'vo_vs_hi_scores.csv')
    if os.path.exists(vo_path):
        import pandas as pd
        vo_df = pd.read_csv(vo_path)
        for _, row in vo_df.iterrows():
            lc = row.get('language_code')
            if lc and 'vo_score' in row and not np.isnan(row['vo_score']):
                lang_to_vo[str(lc)] = row['vo_score']

    return (lang2MAL, lang2counts, lang2counts_left, lang2counts_right,
            langNames, langnameGroup, lang_to_vo)


def _compute_mal_scores(all_langs_position2sizes, all_langs_position2num):
    """Simplified MAL computation (bilateral keys only)."""
    lang2MAL = {}
    for lang in all_langs_position2sizes:
        total_n_to_constituents = defaultdict(list)
        right_n_to_constituents = defaultdict(list)
        left_n_to_constituents = defaultdict(list)

        for key, size_sum in all_langs_position2sizes[lang].items():
            count = all_langs_position2num[lang].get(key, 0)
            if count == 0:
                continue

            m = re.match(r'bilateral_L(\d+)_R(\d+)_pos_(\d+)_(left|right)$', key)
            if m:
                n_left, n_right = int(m.group(1)), int(m.group(2))
                total_n = n_left + n_right
                avg_size = size_sum / count
                total_n_to_constituents[total_n].append((avg_size, count))

            m2 = re.match(r'right_(\d+)_anyother_totright_(\d+)$', key)
            if m2:
                tot = int(m2.group(2))
                avg_size = size_sum / count
                right_n_to_constituents[tot].append((avg_size, count))

            m3 = re.match(r'left_(\d+)_anyother_totleft_(\d+)$', key)
            if m3:
                tot = int(m3.group(2))
                avg_size = size_sum / count
                left_n_to_constituents[tot].append((avg_size, count))

        def _weighted_avg(n_to_c):
            out = {}
            for n, cs in n_to_c.items():
                tw = sum(s * c for s, c in cs)
                tc = sum(c for _, c in cs)
                if tc > 0:
                    out[n] = tw / tc
            return out

        lang2MAL[lang] = {
            'total': _weighted_avg(total_n_to_constituents),
            'right': _weighted_avg(right_n_to_constituents),
            'left':  _weighted_avg(left_n_to_constituents),
        }
    return lang2MAL


# ===========================================================================
# TikZ mini-plot generation
# ===========================================================================
def generate_tikz_miniplot(mal_data, counts, start_n=1, width=PLOT_WIDTH, height=PLOT_HEIGHT):
    """
    Generate a tiny TikZ picture showing the log-log regression for one language.

    Returns (tikz_string, beta_value) or (empty_string, None).
    """
    # Filter by min_count
    filtered = {n: v for n, v in mal_data.items() if counts.get(n, 0) >= MIN_COUNT}
    regression = compute_loglog_regression(filtered, start_n)

    if regression is None or len(regression['points']) < 2:
        return "", None

    points = regression['points']          # list of (log_n, log_mal)
    reg_line = regression['regression_line']  # [(x0,y0), (x1,y1)]
    slope = regression['slope']

    # Determine colour
    beta = -slope
    if beta > 0.1:
        color = "malgreen"
    elif beta < -0.1:
        color = "malred"
    else:
        color = "malgray"

    # Axis bounds (with 10 % margin)
    all_x = [p[0] for p in points] + [r[0] for r in reg_line]
    all_y = [p[1] for p in points] + [r[1] for r in reg_line]
    xmin, xmax = min(all_x), max(all_x)
    ymin, ymax = min(all_y), max(all_y)
    rx = (xmax - xmin) if xmax > xmin else 1
    ry = (ymax - ymin) if ymax > ymin else 1
    xmin -= rx * 0.1; xmax += rx * 0.1
    ymin -= ry * 0.1; ymax += ry * 0.1
    rx = xmax - xmin
    ry = ymax - ymin

    def sx(v):
        return (v - xmin) / rx * width

    def sy(v):
        return (v - ymin) / ry * height

    lines = []
    lines.append(
        f"\\begin{{tikzpicture}}[x=1cm,y=1cm]"
    )
    # Background rectangle
    lines.append(
        f"  \\fill[{color}!15] (0,0) rectangle ({width},{height});"
    )
    # Regression line
    x0, y0 = sx(reg_line[0][0]), sy(reg_line[0][1])
    x1, y1 = sx(reg_line[1][0]), sy(reg_line[1][1])
    lines.append(
        f"  \\draw[{color},line width=0.6pt,opacity=0.8] "
        f"({x0:.4f},{y0:.4f}) -- ({x1:.4f},{y1:.4f});"
    )
    # Data points
    for lx, ly in points:
        cx, cy = sx(lx), sy(ly)
        lines.append(
            f"  \\fill[malblue] ({cx:.4f},{cy:.4f}) circle[radius=0.03cm];"
        )
    lines.append("\\end{tikzpicture}")
    return "\n".join(lines), beta


def beta_cell(beta):
    """Format a beta value for a table cell with colour."""
    if beta is None:
        return "---"
    if beta > 0.1:
        col = "malgreen"
    elif beta < -0.1:
        col = "malred"
    else:
        col = "malgray"
    return f"\\textcolor{{{col}}}{{{beta:+.2f}}}"


def vo_label(vo):
    """Return VO/OV/mix label."""
    if vo is None:
        return "---"
    if vo > 0.66:
        return "VO"
    if vo < 0.33:
        return "OV"
    return "mix"


# ===========================================================================
# LaTeX table builder
# ===========================================================================
def build_latex_table(lang2MAL, lang2counts, lang2counts_left, lang2counts_right,
                      langNames, langnameGroup, lang_to_vo):
    """Build the complete LaTeX longtable with mini-plots for MAL, LMAL, RMAL."""

    rows = []  # list of tuples for sorting

    for lang in lang2MAL:
        mal_total = lang2MAL[lang].get('total', {})
        mal_left = lang2MAL[lang].get('left', {})
        mal_right = lang2MAL[lang].get('right', {})
        counts_t = lang2counts.get(lang, {})
        counts_l = lang2counts_left.get(lang, {})
        counts_r = lang2counts_right.get(lang, {})

        # Compute plots and betas (start_n=1 → β(1→∞))
        tikz_t, beta_t = generate_tikz_miniplot(mal_total, counts_t, start_n=1)
        tikz_l, beta_l = generate_tikz_miniplot(mal_left, counts_l, start_n=1)
        tikz_r, beta_r = generate_tikz_miniplot(mal_right, counts_r, start_n=1)

        name = langNames.get(lang, lang)
        family = langnameGroup.get(name, "?")
        vo = lang_to_vo.get(lang)

        rows.append((name, family, vo, tikz_t, beta_t, tikz_l, beta_l, tikz_r, beta_r))

    # Sort alphabetically by language name
    rows.sort(key=lambda r: r[0].lower())

    # ------------------------------------------------------------------
    # Build LaTeX
    # ------------------------------------------------------------------
    tex = []
    tex.append(r"% Auto-generated by generate_latex_mal_miniplots.py — do not edit")
    tex.append(r"% Requires: \usepackage{tikz}, \usepackage{longtable}, \usepackage{booktabs}")
    tex.append(r"% Colour definitions (put in preamble):")
    tex.append(r"% \definecolor{malgreen}{HTML}{27ae60}")
    tex.append(r"% \definecolor{malred}{HTML}{e74c3c}")
    tex.append(r"% \definecolor{malgray}{HTML}{f39c12}")
    tex.append(r"% \definecolor{malblue}{HTML}{3498db}")
    tex.append("")
    tex.append(r"\begin{longtable}{@{}l l c "   # name, family, VO
               r"c r "                           # MAL plot, β
               r"c r "                           # LMAL plot, β
               r"c r@{}}")                       # RMAL plot, β
    tex.append(r"\caption{MAL, LMAL and RMAL mini log-log plots and $\beta(1\!\to\!\infty)$ "
               r"for all languages. Green = MAL ($\beta>0.1$), "
               r"red = Anti-MAL ($\beta<-0.1$), orange = grey zone.}")
    tex.append(r"\label{tab:all-miniplots}\\")
    tex.append(r"\toprule")
    tex.append(r"\textbf{Language} & \textbf{Family} & \textbf{Type} "
               r"& \textbf{MAL} & $\boldsymbol{\beta}$ "
               r"& \textbf{LMAL} & $\boldsymbol{\beta}$ "
               r"& \textbf{RMAL} & $\boldsymbol{\beta}$ \\")
    tex.append(r"\midrule")
    tex.append(r"\endfirsthead")
    tex.append(r"\toprule")
    tex.append(r"\textbf{Language} & \textbf{Family} & \textbf{Type} "
               r"& \textbf{MAL} & $\boldsymbol{\beta}$ "
               r"& \textbf{LMAL} & $\boldsymbol{\beta}$ "
               r"& \textbf{RMAL} & $\boldsymbol{\beta}$ \\")
    tex.append(r"\midrule")
    tex.append(r"\endhead")
    tex.append(r"\midrule")
    tex.append(r"\multicolumn{9}{r}{\footnotesize\itshape continued on next page}\\")
    tex.append(r"\endfoot")
    tex.append(r"\bottomrule")
    tex.append(r"\endlastfoot")

    n_with_plot = 0
    for (name, family, vo, tikz_t, beta_t, tikz_l, beta_l, tikz_r, beta_r) in rows:
        # Skip languages that have no data at all
        if beta_t is None and beta_l is None and beta_r is None:
            continue

        n_with_plot += 1
        safe_name = _latex_escape(name)
        safe_family = _latex_escape(_shorten_family(family))
        vo_str = vo_label(vo)

        # Wrap tikz in raisebox so it aligns vertically in table
        def wrap(tikz):
            if not tikz:
                return "---"
            return f"\\raisebox{{-0.25\\height}}{{{tikz}}}"

        tex.append(
            f"  {safe_name} & {safe_family} & {vo_str} "
            f"& {wrap(tikz_t)} & {beta_cell(beta_t)} "
            f"& {wrap(tikz_l)} & {beta_cell(beta_l)} "
            f"& {wrap(tikz_r)} & {beta_cell(beta_r)} \\\\"
        )

    tex.append(r"\end{longtable}")

    print(f"Generated table with {n_with_plot} languages (out of {len(rows)} total)")
    return "\n".join(tex)


def _latex_escape(s):
    """Escape special LaTeX characters."""
    for ch in ['&', '%', '$', '#', '_', '{', '}']:
        s = s.replace(ch, '\\' + ch)
    s = s.replace('~', r'\textasciitilde{}')
    return s


def _shorten_family(family):
    """Abbreviate long family names to fit in table."""
    abbrevs = {
        'Indo-European': 'IE',
        'Austronesian': 'Austrn.',
        'Afro-Asiatic': 'Afr-As.',
        'Niger-Congo': 'Nig-Co.',
        'Sino-Tibetan': 'Sin-Tib.',
        'Dravidian': 'Dravid.',
        'Turkic': 'Turkic',
        'Uralic': 'Uralic',
        'Austro-Asiatic': 'Au-As.',
        'Atlantic-Congo': 'Atl-Co.',
        'Trans-New Guinea': 'TNG',
        'Tai-Kadai': 'T-Kadai',
    }
    return abbrevs.get(family, family[:8] if len(family) > 8 else family)


# ===========================================================================
# Main
# ===========================================================================
def main():
    print("Loading data...")
    (lang2MAL, lang2counts, lang2counts_left, lang2counts_right,
     langNames, langnameGroup, lang_to_vo) = load_data()

    print("Generating TikZ mini-plots...")
    table_tex = build_latex_table(
        lang2MAL, lang2counts, lang2counts_left, lang2counts_right,
        langNames, langnameGroup, lang_to_vo
    )

    out_path = os.path.join(OUTPUT_DIR, "mal_miniplots_table.tex")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(table_tex)
    print(f"\n✓ Written to {out_path}")
    print(f"  Add to main.tex:  \\input{{latex/mal_miniplots_table}}")


if __name__ == "__main__":
    main()

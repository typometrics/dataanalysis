"""
MAL HTML Report Generator

Generates interactive HTML tables and charts for Menzerath-Altmann Law analysis.
Uses Chart.js for visualizations.
"""

import os
import re
import json
import numpy as np
import pandas as pd
from collections import defaultdict

# Import coordinate data from generate_ud_maps to ensure consistency
try:
    from generate_ud_maps import MANUAL_COORDS, ISO_639_1_TO_3
except ImportError:
    # Fallback if generate_ud_maps is not available
    MANUAL_COORDS = {}
    ISO_639_1_TO_3 = {}

# Minimum sample count threshold for statistical reliability
# This value should match the MIN_COUNT defined in the notebook
DEFAULT_MIN_COUNT = 100

# Paper reference (UDW26 / LREC 2026)
PAPER_REFERENCE = {
    'authors': 'Pegah Faghiri, Kim Gerdes, Sylvain Kahane',
    'year': 2026,
    'title': 'Verifying the Menzerath-Altmann law in the verbal domain in 180 languages',
    'venue': 'UDW26 @ LREC 2026',
}


def _compliance_category(ratio):
    """Classify a MAL compliance (decrease) ratio. Paper §4.2 reports
    high=79, middle=29, low=23 (total 131). Those counts only reproduce
    when boundaries are the *exact fractions* 2/3 and 1/3 (not the rounded
    0.67/0.33), because many languages have compliance equal to exactly
    2/3 or 1/3 — just under the rounded value.

    Returns one of 'high', 'middle', 'low', or None when ratio is None.
    """
    if ratio is None:
        return None
    if ratio >= 2/3:
        return 'high'
    if ratio <= 1/3:
        return 'low'
    return 'middle'


def compute_global_scale(*lang2MAL_dicts, min_count_filter=None, lang2counts_dicts=None,
                        force_min_n=1, padding=0.1):
    """Compute a single (xmin, xmax, ymin, ymax) bounding box in log-space
    that covers every language regression across the supplied MAL dictionaries.

    The x-range always starts at log(force_min_n) (so n=1 is reserved on every
    plot, even when MAL_1 is excluded for low count).

    Args:
        *lang2MAL_dicts: any number of dicts mapping lang -> {n: MAL_n}.
        min_count_filter: if given, only n values whose count >= this threshold
            in the matching counts dict are used to compute y-bounds.
        lang2counts_dicts: aligned list of counts dicts (same length/order as
            lang2MAL_dicts); ignored when min_count_filter is None.
        force_min_n: x-axis is forced to include log(force_min_n).
        padding: fraction of range added on every side.

    Returns:
        (xmin, xmax, ymin, ymax) tuple of floats in log-space.
    """
    log_n_values = []
    log_mal_values = []
    max_n_seen = force_min_n

    if lang2counts_dicts is None:
        lang2counts_dicts = [None] * len(lang2MAL_dicts)

    for mal_dict, counts_dict in zip(lang2MAL_dicts, lang2counts_dicts):
        if not mal_dict:
            continue
        for lang, mal_data in mal_dict.items():
            counts = counts_dict.get(lang, {}) if counts_dict else {}
            for n, v in mal_data.items():
                if v <= 0:
                    continue
                if min_count_filter is not None and counts.get(n, 0) < min_count_filter:
                    continue
                if n > max_n_seen:
                    max_n_seen = n
                log_n_values.append(np.log(n))
                log_mal_values.append(np.log(v))

    if not log_mal_values:
        # Degenerate fallback
        return (0.0, np.log(max(force_min_n, 2)), 0.0, 1.0)

    xmin = np.log(force_min_n)
    xmax = np.log(max_n_seen)
    ymin = float(min(log_mal_values))
    ymax = float(max(log_mal_values))

    rx = xmax - xmin if xmax > xmin else 1.0
    ry = ymax - ymin if ymax > ymin else 1.0
    xmin -= rx * padding
    xmax += rx * padding
    ymin -= ry * padding
    ymax += ry * padding
    return (float(xmin), float(xmax), float(ymin), float(ymax))


def compute_loglog_regression(mal_data, start_n=1):
    """
    Compute linear regression in log-log space: log(MAL_n) = a - b * log(n)
    
    The negative of the slope (b) is the MAL effect score.
    
    Args:
        mal_data: Dict mapping n -> MAL value
        start_n: Starting n value for regression (1 for full, 2 for excluding small n)
        
    Returns:
        Dict with 'slope', 'intercept', 'r_squared', 'points' (list of (log_n, log_mal)),
        'regression_line' (list of (log_n, predicted_log_mal)), or None if insufficient data
    """
    # Filter data points with n >= start_n
    points = [(n, mal) for n, mal in mal_data.items() if n >= start_n and mal > 0]
    
    if len(points) < 2:
        return None
    
    # Sort by n
    points.sort(key=lambda x: x[0])
    
    # Convert to log space
    log_n = np.array([np.log(p[0]) for p in points])
    log_mal = np.array([np.log(p[1]) for p in points])
    
    # Linear regression: log_mal = intercept + slope * log_n
    # Using numpy polyfit (degree 1)
    try:
        slope, intercept = np.polyfit(log_n, log_mal, 1)
        
        # Compute R-squared
        predicted = intercept + slope * log_n
        ss_res = np.sum((log_mal - predicted) ** 2)
        ss_tot = np.sum((log_mal - np.mean(log_mal)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': float(r_squared),
            'points': [(float(log_n[i]), float(log_mal[i])) for i in range(len(points))],
            'n_values': [p[0] for p in points],
            'mal_values': [p[1] for p in points],
            'regression_line': [(float(log_n[0]), float(intercept + slope * log_n[0])),
                               (float(log_n[-1]), float(intercept + slope * log_n[-1]))]
        }
    except Exception:
        return None


def compute_decrease_ratio(mal_data):
    """
    Compute MAL decrease ratio: proportion of consecutive pairs where MAL decreases.
    
    For each pair (n, n+1) in the data, check if MAL_{n+1} < MAL_n.
    The ratio is the count of decreasing pairs divided by total pairs.
    
    A value of 1.0 means all consecutive pairs show decrease (perfect MAL).
    A value of 0.0 means no consecutive pairs show decrease (anti-MAL).
    A value of 0.5 means half the pairs show decrease.
    
    Args:
        mal_data: Dict mapping n -> MAL value
        
    Returns:
        Float decrease ratio (0 to 1), or None if insufficient data
    """
    if not mal_data or len(mal_data) < 2:
        return None
    
    ns = sorted(mal_data.keys())
    
    # Count consecutive pairs where MAL decreases
    decreasing_count = 0
    total_pairs = 0
    
    for i in range(len(ns) - 1):
        n_curr = ns[i]
        n_next = ns[i + 1]
        mal_curr = mal_data.get(n_curr)
        mal_next = mal_data.get(n_next)
        
        if mal_curr is not None and mal_next is not None:
            total_pairs += 1
            if mal_next < mal_curr:
                decreasing_count += 1
    
    if total_pairs == 0:
        return None
    
    return decreasing_count / total_pairs


def generate_loglog_svg(mal_data, start_n=1, width=120, height=60, lang_name="", lang_code="", mal_label="MAL",
                        fixed_bounds=None, n_axis_max=None):
    """
    Generate a small inline SVG plot showing log-log regression.
    Clicking the plot opens a larger popup with full annotations.

    Args:
        mal_data: Dict mapping n -> MAL value
        start_n: Starting n value for regression
        width: SVG width in pixels
        height: SVG height in pixels
        lang_name: Language name for popup title
        lang_code: Language code for unique ID
        mal_label: Label for MAL type ('MAL', 'Left MAL', 'Right MAL')
        fixed_bounds: Optional (xmin, xmax, ymin, ymax) tuple in log-space.
            When set, the same fixed scale is used for every plot so slopes
            are visually comparable across languages. The popup chart will
            also use this scale.
        n_axis_max: Optional integer max n value for the x-axis. Used to
            ensure the x range covers n=1..n_axis_max even if MAL_1 was
            filtered out.

    Returns:
        Tuple of (svg_string, slope) or (empty_svg, None) if insufficient data
    """
    regression = compute_loglog_regression(mal_data, start_n)

    if regression is None or len(regression['points']) < 2:
        # Return empty placeholder, but still keep SVG box at the requested size.
        # If fixed_bounds is provided, render a faint axis backdrop so the cell
        # visually matches the others.
        return (f'<svg width="{width}" height="{height}" style="background:#f9f9f9;border-radius:3px;">'
                f'<text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" '
                f'font-size="10" fill="#999">—</text></svg>'), None

    points = regression['points']
    reg_line = regression['regression_line']
    slope = regression['slope']
    r_squared = regression['r_squared']
    n_values = regression['n_values']
    mal_values = regression['mal_values']

    # Padding
    pad = 8
    plot_w = width - 2 * pad
    plot_h = height - 2 * pad

    if fixed_bounds is not None:
        min_x, max_x, min_y, max_y = fixed_bounds
    else:
        # Get bounds from data + regression line
        all_x = [p[0] for p in points] + [r[0] for r in reg_line]
        all_y = [p[1] for p in points] + [r[1] for r in reg_line]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        # Always include n=1 on the axis if requested via n_axis_max
        if n_axis_max is not None:
            min_x = min(min_x, np.log(1))
            max_x = max(max_x, np.log(n_axis_max))
        # Add small margin to bounds
        range_x = max_x - min_x if max_x > min_x else 1
        range_y = max_y - min_y if max_y > min_y else 1
        min_x -= range_x * 0.1
        max_x += range_x * 0.1
        min_y -= range_y * 0.1
        max_y += range_y * 0.1
    range_x = max_x - min_x
    range_y = max_y - min_y
    
    def scale_x(val):
        return pad + (val - min_x) / range_x * plot_w
    
    def scale_y(val):
        # Invert Y axis (SVG has Y increasing downward)
        return pad + (1 - (val - min_y) / range_y) * plot_h
    
    # Determine color based on slope (negative slope = MAL compliance = green)
    if slope < -0.1:
        line_color = "#27ae60"  # Green
        bg_color = "#e8f8f0"
    elif slope > 0.1:
        line_color = "#e74c3c"  # Red  
        bg_color = "#fdeaea"
    else:
        line_color = "#f39c12"  # Yellow/Orange
        bg_color = "#fef9e7"
    
    # Prepare data for popup (as JSON-safe format, escaped for HTML attribute)
    popup_data = {
        'lang_name': lang_name,
        'start_n': start_n,
        'mal_label': mal_label,
        'n_values': n_values,
        'mal_values': mal_values,
        'slope': float(slope),
        'intercept': float(regression['intercept']),
        'r_squared': float(r_squared),
        'points': [[float(p[0]), float(p[1])] for p in points],
        'reg_line': [[float(r[0]), float(r[1])] for r in reg_line],
        # Fixed scale (in log-space) so the popup uses the same axes as the
        # mini-plot. None when no fixed scale is provided (popup auto-scales).
        'fixed_bounds': list(fixed_bounds) if fixed_bounds is not None else None,
        'n_axis_max': int(n_axis_max) if n_axis_max is not None else int(max(n_values)),
    }
    # HTML-escape double quotes so they don't break the onclick attribute
    popup_json = json.dumps(popup_data).replace('"', '&quot;')
    
    # Build SVG with onclick handler - use single quotes to wrap the JSON string in JS
    svg_parts = [f'<svg width="{width}" height="{height}" style="background:{bg_color};border-radius:3px;cursor:pointer;" onclick="showLogLogPopup(\'{popup_json}\')">']
    
    # Draw regression line
    x1, y1 = scale_x(reg_line[0][0]), scale_y(reg_line[0][1])
    x2, y2 = scale_x(reg_line[1][0]), scale_y(reg_line[1][1])
    svg_parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{line_color}" stroke-width="2" stroke-opacity="0.7"/>')
    
    # Draw data points
    for log_n, log_mal in points:
        cx, cy = scale_x(log_n), scale_y(log_mal)
        svg_parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3" fill="#3498db" stroke="white" stroke-width="1"/>')
    
    svg_parts.append('</svg>')
    
    return ''.join(svg_parts), -slope  # Return negative slope as the effect score


def get_sample_counts_per_n(all_langs_position2num, min_count=None):
    """
    Get total sample count for each (language, n) combination from bilateral keys.
    
    Counts all bilateral configurations for a given total n (left + right dependents),
    using pos_1 counts to avoid double-counting.
    
    Args:
        all_langs_position2num: Dict mapping lang -> key -> count
        min_count: Not used for filtering anymore - all counts are returned.
                   Filtering by MIN_COUNT happens in the table rendering.
        
    Returns:
        Dict mapping lang -> n -> total_count (unfiltered)
    """
    lang2counts = {}
    for lang in all_langs_position2num:
        n_to_count = defaultdict(int)
        for key, count in all_langs_position2num[lang].items():
            # Only match bilateral keys with pos_1 to count each configuration once
            # Use pos_1_left as the canonical count (each config has exactly one)
            match = re.match(r'bilateral_L(\d+)_R(\d+)_pos_1_left$', key)
            if match:
                n_left = int(match.group(1))
                n_right = int(match.group(2))
                total_n = n_left + n_right
                n_to_count[total_n] += count
        lang2counts[lang] = dict(n_to_count)
    return lang2counts


def get_directional_counts(all_langs_position2num, min_count=None):
    """
    Get sample counts for left and right dependent configurations.
    
    Uses _anyother_ keys to match how MAL_left and MAL_right are computed:
    - left_i_anyother_totleft_n: position i in config with n total left deps (any right)
    - right_i_anyother_totright_n: position i in config with n total right deps (any left)
    
    Only counts pos_1 keys to avoid double-counting.
    
    Args:
        all_langs_position2num: Dict mapping lang -> key -> count
        min_count: Not used for filtering anymore - all counts are returned.
                   Filtering by MIN_COUNT happens in the table rendering.
        
    Returns:
        Tuple of (lang2counts_left, lang2counts_right)
    """
    lang2counts_left = {}
    lang2counts_right = {}
    
    for lang in all_langs_position2num:
        left_counts = defaultdict(int)
        right_counts = defaultdict(int)
        
        for key, count in all_langs_position2num[lang].items():
            # Match _anyother_ keys for right dependents: right_1_anyother_totright_n
            # Only use position 1 to count each configuration once
            match_right = re.match(r'right_1_anyother_totright_(\d+)$', key)
            if match_right:
                tot_right = int(match_right.group(1))
                right_counts[tot_right] += count
                continue
            
            # Match _anyother_ keys for left dependents: left_1_anyother_totleft_n
            match_left = re.match(r'left_1_anyother_totleft_(\d+)$', key)
            if match_left:
                tot_left = int(match_left.group(1))
                left_counts[tot_left] += count
                continue
        
        lang2counts_left[lang] = dict(left_counts)
        lang2counts_right[lang] = dict(right_counts)
    
    return lang2counts_left, lang2counts_right


def compute_local_change_score(mal_n, mal_n1, n):
    """
    Compute local MAL elasticity: [ln(MAL_n) - ln(MAL_{n+1})] / [ln(n+1) - ln(n)]
    
    This measures how much the log of constituent size changes relative to the log of n.
    A positive value indicates MAL compliance (size decreases as n increases).
    The expected value under ideal MAL is approximately constant (the 'b' parameter).
    
    Args:
        mal_n: MAL value at n
        mal_n1: MAL value at n+1
        n: The starting n value
        
    Returns:
        Local change score (float), or np.nan if invalid
    """
    if mal_n <= 0 or mal_n1 <= 0:
        return np.nan
    log_mal_diff = np.log(mal_n) - np.log(mal_n1)
    log_n_diff = np.log(n + 1) - np.log(n)
    return log_mal_diff / log_n_diff


def compute_local_scores_for_all_languages(lang2MAL_total):
    """
    Compute local change scores for all languages.
    
    Args:
        lang2MAL_total: Dict mapping lang -> n -> MAL value
        
    Returns:
        Dict mapping lang -> "n→n+1" -> score
    """
    lang2local_scores = {}
    for lang, mal_data in lang2MAL_total.items():
        scores = {}
        ns = sorted(mal_data.keys())
        for i in range(len(ns) - 1):
            n = ns[i]
            n_next = ns[i + 1]
            if n_next == n + 1:  # Only consecutive n values
                score = compute_local_change_score(mal_data[n], mal_data[n_next], n)
                scores[f"{n}→{n_next}"] = score
        lang2local_scores[lang] = scores
    return lang2local_scores


# (removed dead function `_compute_chart_data` — superseded by mal_site.py)


def _macroarea_from_latlon(lat, lon):
    """Approximate WALS macroarea from lat/lon. Used as a fallback for
    languages whose coordinates come from MANUAL_COORDS (no WALS row).
    The six WALS macroareas are:
        Africa, Eurasia, Australia, Papunesia, North America, South America.
    """
    if lat is None or lon is None:
        return 'Unknown'
    # Australia (mainland + Tasmania)
    if -45 <= lat <= -10 and 110 <= lon <= 155:
        return 'Australia'
    # Papunesia: insular SE Asia + New Guinea + Pacific (excluding mainland Asia)
    if -15 <= lat <= 25 and ((95 <= lon <= 180) or (-180 <= lon <= -130)):
        return 'Papunesia'
    # Africa (incl. Madagascar)
    if -35 <= lat <= 38 and -20 <= lon <= 55:
        return 'Africa'
    # Americas (split by latitude ~12°N at the Panama isthmus)
    if -180 <= lon <= -30:
        return 'North America' if lat >= 12 else 'South America'
    # Default for the remaining Old World mass
    return 'Eurasia'


def _load_geographic_data(wals_path, lang2MAL_total, lang2local_scores, langNames):
    """
    Load WALS language coordinates and match with UD languages.
    
    MANUAL_COORDS takes priority for relocated/corrected languages,
    matching the behavior of generate_ud_maps.py.
    
    Returns list of dicts with: name, code, lat, lon, mal_score, family
    """
    try:
        wals_df = pd.read_csv(wals_path)
    except Exception as e:
        print(f"Warning: Could not load WALS data: {e}")
        wals_df = pd.DataFrame()
    
    geo_data = []
    
    for lang_code, mal_data in lang2MAL_total.items():
        lang_name = langNames.get(lang_code, lang_code)
        
        # Compute global MAL score: −β(2→max) (negated so positive = MAL compliance)
        regression = compute_loglog_regression(mal_data, start_n=2)
        mal_score = float(-regression['slope']) if regression else 0.0
        
        # MANUAL_COORDS takes priority (for relocated/corrected languages)
        # This matches the behavior of generate_ud_maps.py
        if lang_code in MANUAL_COORDS:
            lat, lon, name, family = MANUAL_COORDS[lang_code]
            geo_data.append({
                'name': lang_name,
                'code': lang_code,
                'lat': lat,
                'lon': lon,
                'mal_score': mal_score,
                'family': family,
                'macroarea': _macroarea_from_latlon(lat, lon),
                'n_points': len(regression['n_values']) if regression else 0
            })
            continue
        
        # Try to find matching WALS language by ISO code
        match = None
        
        if not wals_df.empty and 'ISO639P3code' in wals_df.columns:
            # First try exact ISO639P3code match (for 3-letter codes)
            matches = wals_df[wals_df['ISO639P3code'] == lang_code]
            if len(matches) > 0:
                match = matches.iloc[0]
            
            # If no match and code is 2-letter, try converting to 3-letter
            if match is None and len(lang_code) == 2:
                iso3_code = ISO_639_1_TO_3.get(lang_code)
                if iso3_code:
                    matches = wals_df[wals_df['ISO639P3code'] == iso3_code]
                    if len(matches) > 0:
                        match = matches.iloc[0]
        
        # Try matching by EXACT name only (no substring matching to avoid false positives)
        if match is None and not wals_df.empty and 'Name' in wals_df.columns:
            clean_name = lang_name.split('(')[0].strip().lower()
            
            for _, row in wals_df.iterrows():
                wals_name = str(row['Name']).split('(')[0].strip().lower()
                if clean_name == wals_name:
                    match = row
                    break
        
        if match is not None and pd.notna(match.get('Latitude')) and pd.notna(match.get('Longitude')):
            family = str(match.get('Family', 'Unknown')) if pd.notna(match.get('Family')) else 'Unknown'
            lat_val = float(match['Latitude'])
            lon_val = float(match['Longitude'])
            macroarea = match.get('Macroarea')
            if not (isinstance(macroarea, str) and macroarea.strip()):
                macroarea = _macroarea_from_latlon(lat_val, lon_val)

            geo_data.append({
                'name': lang_name,
                'code': lang_code,
                'lat': lat_val,
                'lon': lon_val,
                'mal_score': mal_score,
                'family': family,
                'macroarea': macroarea,
                'n_points': len(regression['n_values']) if regression else 0
            })
    
    return geo_data


def _filter_mal_by_count(mal_dict, counts_dict, threshold):
    """Return a copy of mal_dict keeping only n-values where count >= threshold."""
    filtered = {}
    for lang, mal_data in mal_dict.items():
        count_data = counts_dict.get(lang, {})
        filt = {n: v for n, v in mal_data.items() if count_data.get(n, 0) >= threshold}
        if filt:
            filtered[lang] = filt
    return filtered


# (removed dead function `generate_mal_html_report` — superseded by mal_site.py)


# (removed dead function `_build_table` — superseded by mal_site.py)


# (removed dead function `_get_html_header` — superseded by mal_site.py)


# (removed dead function `_get_html_header_with_nav` — superseded by mal_site.py)


# (removed dead function `_get_table_explanation` — superseded by mal_site.py)


def _generate_slope_summary_table(lang2MAL_filtered, lang2local_scores, max_n=5):
    """
    Generate an HTML table counting languages per slope category.
    
    Columns: β(2→max), 1→2, 2→3, ..., (max_n-1)→max_n
    Rows: green (>0.1), yellow-high (0 to 0.1), yellow-low (-0.1 to 0), red (<-0.1), total
    """
    # Define columns
    columns = []
    # Regression slope β(2→max)
    values_2max = []
    for lang, mal_data in lang2MAL_filtered.items():
        reg = compute_loglog_regression(mal_data, start_n=2)
        if reg is not None:
            values_2max.append(reg['slope'])
    columns.append(('β(2→max)', values_2max))
    
    # Local change scores
    for n in range(1, max_n):
        col_label = f"{n}→{n+1}"
        values = []
        for lang, scores in lang2local_scores.items():
            key = f"{n}→{n+1}"
            if key in scores and not np.isnan(scores[key]):
                values.append(scores[key])
        columns.append((col_label, values))
    
    # Define row categories (raw slope: negative = MAL compliance, positive = anti-MAL)
    categories = [
        ("β < -0.1",   "#c8e6c9", lambda v: v < -0.1),
        ("-0.1 ≤ β < 0", "#fff9c4", lambda v: -0.1 <= v < 0),
        ("0 ≤ β ≤ 0.1", "#fff9c4", lambda v: 0 <= v <= 0.1),
        ("β > 0.1",  "#ffcdd2", lambda v: v > 0.1),
    ]
    
    # Build HTML
    html = []
    html.append('<div class="chart-container">')
    html.append('<h3>Slope Distribution Summary</h3>')
    html.append('<table class="summary-table" style="border-collapse: collapse; width: auto; margin: 20px auto; font-size: 13px;">')
    
    # Header row
    html.append('<tr style="border-bottom: 2px solid #333;">')
    html.append('<th style="padding: 6px 12px; text-align: left; border: 1px solid #ddd;">Category</th>')
    for col_label, _ in columns:
        html.append(f'<th style="padding: 6px 12px; text-align: center; border: 1px solid #ddd;">{col_label}</th>')
    html.append('</tr>')
    
    # Data rows
    for cat_label, bg_color, test_fn in categories:
        html.append(f'<tr style="background-color: {bg_color};">')
        html.append(f'<td style="padding: 6px 12px; border: 1px solid #ddd; font-weight: bold;">{cat_label}</td>')
        for _, values in columns:
            count = sum(1 for v in values if test_fn(v))
            html.append(f'<td style="padding: 6px 12px; text-align: center; border: 1px solid #ddd;">{count}</td>')
        html.append('</tr>')
    
    # Total row
    html.append('<tr style="border-top: 2px solid #333; font-weight: bold;">')
    html.append('<td style="padding: 6px 12px; border: 1px solid #ddd;">Total</td>')
    for _, values in columns:
        html.append(f'<td style="padding: 6px 12px; text-align: center; border: 1px solid #ddd;">{len(values)}</td>')
    html.append('</tr>')
    
    html.append('</table>')
    html.append('<div class="explanation">')
    html.append('<p><strong>Note:</strong> β(2→max) is the log-log regression slope from n=2 (negative = MAL compliance). ')
    html.append('Local change scores (1→2, 2→3, ...) are positive when MAL holds (constituent size decreases).</p>')
    html.append('</div>')
    html.append('</div>')
    
    return '\n'.join(html)


# (removed dead function `_generate_directional_beta_table` — superseded by mal_site.py)


# (removed dead function `_generate_directional_scatter_section` — superseded by mal_site.py)


# (removed dead function `_get_charts_section` — superseded by mal_site.py)


def _generate_svg_box_plot(box_plot_data):
    """Generate an SVG box plot with whiskers for local change scores."""
    
    if not box_plot_data:
        return "<p>No box plot data available.</p>"
    
    # SVG dimensions
    width = 800
    height = 350
    margin_left = 60
    margin_right = 30
    margin_top = 30
    margin_bottom = 60
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    
    # Get transitions and find y-axis range
    transitions = sorted(box_plot_data.keys())
    all_values = []
    for data in box_plot_data.values():
        all_values.extend([data['min'], data['max']])
        all_values.extend(data.get('outliers', []))
    
    y_min = min(all_values) - 0.1
    y_max = max(all_values) + 0.1
    y_range = y_max - y_min
    
    def scale_y(val):
        return margin_top + plot_height - ((val - y_min) / y_range * plot_height)
    
    # Calculate box positions
    n_boxes = len(transitions)
    box_spacing = plot_width / n_boxes
    box_width = min(60, box_spacing * 0.6)
    
    svg_parts = []
    svg_parts.append(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: white; font-family: Arial, sans-serif;">')
    
    # Y-axis
    svg_parts.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="#333" stroke-width="1"/>')
    
    # Y-axis ticks and labels
    n_ticks = 6
    for i in range(n_ticks + 1):
        y_val = y_min + (y_range * i / n_ticks)
        y_pos = scale_y(y_val)
        svg_parts.append(f'<line x1="{margin_left - 5}" y1="{y_pos}" x2="{margin_left}" y2="{y_pos}" stroke="#333" stroke-width="1"/>')
        svg_parts.append(f'<text x="{margin_left - 10}" y="{y_pos + 4}" text-anchor="end" font-size="11">{y_val:.1f}</text>')
        # Grid lines
        svg_parts.append(f'<line x1="{margin_left}" y1="{y_pos}" x2="{width - margin_right}" y2="{y_pos}" stroke="#eee" stroke-width="1"/>')
    
    # Zero line (dashed)
    zero_y = scale_y(0)
    if y_min < 0 < y_max:
        svg_parts.append(f'<line x1="{margin_left}" y1="{zero_y}" x2="{width - margin_right}" y2="{zero_y}" stroke="#333" stroke-width="2" stroke-dasharray="6,4"/>')
    
    # X-axis
    svg_parts.append(f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}" stroke="#333" stroke-width="1"/>')
    
    # Y-axis label
    svg_parts.append(f'<text x="15" y="{height/2}" text-anchor="middle" font-size="12" transform="rotate(-90, 15, {height/2})">Local Change Score</text>')
    
    # X-axis label  
    svg_parts.append(f'<text x="{margin_left + plot_width/2}" y="{height - 10}" text-anchor="middle" font-size="12">Transition</text>')
    
    # Draw box plots
    for i, trans in enumerate(transitions):
        data = box_plot_data[trans]
        x_center = margin_left + (i + 0.5) * box_spacing
        x_left = x_center - box_width / 2
        x_right = x_center + box_width / 2
        
        q1_y = scale_y(data['q1'])
        median_y = scale_y(data['median'])
        q3_y = scale_y(data['q3'])
        min_y = scale_y(data['min'])
        max_y = scale_y(data['max'])
        
        # Determine color based on median
        if data['median'] > 0.1:
            fill_color = 'rgba(76, 175, 80, 0.6)'  # Green
            stroke_color = 'rgba(76, 175, 80, 1)'
        elif data['median'] < -0.1:
            fill_color = 'rgba(244, 67, 54, 0.6)'  # Red
            stroke_color = 'rgba(244, 67, 54, 1)'
        else:
            fill_color = 'rgba(255, 193, 7, 0.6)'  # Yellow
            stroke_color = 'rgba(255, 193, 7, 1)'
        
        # Whisker (bottom)
        svg_parts.append(f'<line x1="{x_center}" y1="{q1_y}" x2="{x_center}" y2="{min_y}" stroke="{stroke_color}" stroke-width="2"/>')
        svg_parts.append(f'<line x1="{x_left + 10}" y1="{min_y}" x2="{x_right - 10}" y2="{min_y}" stroke="{stroke_color}" stroke-width="2"/>')
        
        # Whisker (top)
        svg_parts.append(f'<line x1="{x_center}" y1="{q3_y}" x2="{x_center}" y2="{max_y}" stroke="{stroke_color}" stroke-width="2"/>')
        svg_parts.append(f'<line x1="{x_left + 10}" y1="{max_y}" x2="{x_right - 10}" y2="{max_y}" stroke="{stroke_color}" stroke-width="2"/>')
        
        # Box (Q1 to Q3)
        box_height = q1_y - q3_y  # Note: y increases downward
        svg_parts.append(f'<rect x="{x_left}" y="{q3_y}" width="{box_width}" height="{box_height}" fill="{fill_color}" stroke="{stroke_color}" stroke-width="2"/>')
        
        # Median line
        svg_parts.append(f'<line x1="{x_left}" y1="{median_y}" x2="{x_right}" y2="{median_y}" stroke="#333" stroke-width="3"/>')
        
        # Outliers
        for outlier in data.get('outliers', []):
            outlier_y = scale_y(outlier)
            svg_parts.append(f'<circle cx="{x_center}" cy="{outlier_y}" r="4" fill="none" stroke="{stroke_color}" stroke-width="2"/>')
        
        # X-axis label
        svg_parts.append(f'<text x="{x_center}" y="{margin_top + plot_height + 20}" text-anchor="middle" font-size="11">{trans}</text>')
        svg_parts.append(f'<text x="{x_center}" y="{margin_top + plot_height + 35}" text-anchor="middle" font-size="9" fill="#666">(n={data["count"]})</text>')
    
    svg_parts.append('</svg>')
    
    return '\n'.join(svg_parts)


def _generate_svg_combined_box_plot(box_plot_total, box_plot_left, box_plot_right, max_transition=5):
    """
    Generate an SVG box plot comparing LMAL, MAL, and RMAL for each transition.
    
    Args:
        box_plot_total: Box plot data for total MAL
        box_plot_left: Box plot data for left-side MAL  
        box_plot_right: Box plot data for right-side MAL
        max_transition: Maximum transition to show (e.g., 5 means show up to 5→6)
    
    Returns:
        SVG string with grouped box plots
    """
    
    if not box_plot_total:
        return "<p>No box plot data available.</p>"
    
    # SVG dimensions  
    width = 950
    height = 400
    margin_left = 70
    margin_right = 40
    margin_top = 40
    margin_bottom = 80
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    
    # Get transitions up to max_transition (e.g., "1→2" through "5→6")
    transitions = []
    for trans in sorted(box_plot_total.keys()):
        # Parse the transition number (first digit before →)
        try:
            n = int(trans.split('→')[0])
            if n <= max_transition:
                transitions.append(trans)
        except:
            continue
    
    if not transitions:
        return "<p>No transitions available up to n={max_transition}.</p>"
    
    # Find y-axis range based on actual whiskers (min/max), not outliers
    # This preserves the true whisker asymmetry while excluding extreme outliers
    all_whiskers = []
    for data_dict in [box_plot_total, box_plot_left or {}, box_plot_right or {}]:
        for trans in transitions:
            if trans in data_dict:
                data = data_dict[trans]
                all_whiskers.extend([data['min'], data['max']])
    
    if not all_whiskers:
        return "<p>No data available for the selected transitions.</p>"
    
    # Use actual whisker range with modest padding
    whisker_min = min(all_whiskers)
    whisker_max = max(all_whiskers)
    
    # Add 10% padding to each side
    y_range_raw = whisker_max - whisker_min
    padding = max(0.1, y_range_raw * 0.1)  # At least 0.1 units padding
    
    y_min = whisker_min - padding
    y_max = whisker_max + padding
    y_range = y_max - y_min
    
    def scale_y(val):
        # Don't clip - use actual values to preserve whisker asymmetry
        return margin_top + plot_height - ((val - y_min) / y_range * plot_height)
    
    # Layout: for each transition, we have 3 boxes (LMAL, MAL, RMAL)
    n_transitions = len(transitions)
    group_width = plot_width / n_transitions
    box_width = min(25, group_width * 0.25)
    box_gap = 5
    
    svg_parts = []
    svg_parts.append(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: white; font-family: Arial, sans-serif;">')
    
    # Title
    svg_parts.append(f'<text x="{width/2}" y="20" text-anchor="middle" font-size="14" font-weight="bold">LMAL vs MAL vs RMAL: Local Change Scores by Transition</text>')
    
    # Y-axis
    svg_parts.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="#333" stroke-width="1"/>')
    
    # Y-axis ticks and labels
    n_ticks = 6
    for i in range(n_ticks + 1):
        y_val = y_min + (y_range * i / n_ticks)
        y_pos = scale_y(y_val)
        svg_parts.append(f'<line x1="{margin_left - 5}" y1="{y_pos}" x2="{margin_left}" y2="{y_pos}" stroke="#333" stroke-width="1"/>')
        svg_parts.append(f'<text x="{margin_left - 10}" y="{y_pos + 4}" text-anchor="end" font-size="11">{y_val:.2f}</text>')
        # Grid lines
        svg_parts.append(f'<line x1="{margin_left}" y1="{y_pos}" x2="{width - margin_right}" y2="{y_pos}" stroke="#eee" stroke-width="1"/>')
    
    # Zero line (dashed)
    if y_min < 0 < y_max:
        zero_y = scale_y(0)
        svg_parts.append(f'<line x1="{margin_left}" y1="{zero_y}" x2="{width - margin_right}" y2="{zero_y}" stroke="#333" stroke-width="2" stroke-dasharray="6,4"/>')
    
    # X-axis
    svg_parts.append(f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}" stroke="#333" stroke-width="1"/>')
    
    # Y-axis label
    svg_parts.append(f'<text x="15" y="{height/2}" text-anchor="middle" font-size="12" transform="rotate(-90, 15, {height/2})">Local Change Score</text>')
    
    # X-axis label  
    svg_parts.append(f'<text x="{margin_left + plot_width/2}" y="{height - 10}" text-anchor="middle" font-size="12">Transition (n → n+1)</text>')
    
    # Colors for each type
    colors = {
        'left': {'fill': 'rgba(33, 150, 243, 0.6)', 'stroke': 'rgba(33, 150, 243, 1)'},  # Blue for LMAL
        'total': {'fill': 'rgba(156, 39, 176, 0.6)', 'stroke': 'rgba(156, 39, 176, 1)'},  # Purple for MAL
        'right': {'fill': 'rgba(255, 152, 0, 0.6)', 'stroke': 'rgba(255, 152, 0, 1)'}   # Orange for RMAL
    }
    
    # Draw grouped box plots
    for i, trans in enumerate(transitions):
        group_center = margin_left + (i + 0.5) * group_width
        
        # Calculate positions for 3 boxes
        positions = [
            ('left', group_center - box_width - box_gap, box_plot_left),
            ('total', group_center, box_plot_total),
            ('right', group_center + box_width + box_gap, box_plot_right)
        ]
        
        for label, x_center, data_dict in positions:
            if not data_dict or trans not in data_dict:
                continue
                
            data = data_dict[trans]
            x_left = x_center - box_width / 2
            x_right = x_center + box_width / 2
            
            q1_y = scale_y(data['q1'])
            median_y = scale_y(data['median'])
            q3_y = scale_y(data['q3'])
            min_y = scale_y(data['min'])
            max_y = scale_y(data['max'])
            
            fill_color = colors[label]['fill']
            stroke_color = colors[label]['stroke']
            
            # Whisker (bottom)
            svg_parts.append(f'<line x1="{x_center}" y1="{q1_y}" x2="{x_center}" y2="{min_y}" stroke="{stroke_color}" stroke-width="1.5"/>')
            svg_parts.append(f'<line x1="{x_left + 3}" y1="{min_y}" x2="{x_right - 3}" y2="{min_y}" stroke="{stroke_color}" stroke-width="1.5"/>')
            
            # Whisker (top)
            svg_parts.append(f'<line x1="{x_center}" y1="{q3_y}" x2="{x_center}" y2="{max_y}" stroke="{stroke_color}" stroke-width="1.5"/>')
            svg_parts.append(f'<line x1="{x_left + 3}" y1="{max_y}" x2="{x_right - 3}" y2="{max_y}" stroke="{stroke_color}" stroke-width="1.5"/>')
            
            # Box (Q1 to Q3)
            box_height = q1_y - q3_y
            svg_parts.append(f'<rect x="{x_left}" y="{q3_y}" width="{box_width}" height="{box_height}" fill="{fill_color}" stroke="{stroke_color}" stroke-width="1.5"/>')
            
            # Median line
            svg_parts.append(f'<line x1="{x_left}" y1="{median_y}" x2="{x_right}" y2="{median_y}" stroke="#333" stroke-width="2"/>')
        
        # X-axis label for transition
        svg_parts.append(f'<text x="{group_center}" y="{margin_top + plot_height + 20}" text-anchor="middle" font-size="12" font-weight="bold">{trans}</text>')
    
    # Legend
    legend_y = margin_top + plot_height + 45
    legend_items = [
        ('LMAL (Left)', colors['left']['fill'], colors['left']['stroke']),
        ('MAL (Total)', colors['total']['fill'], colors['total']['stroke']),
        ('RMAL (Right)', colors['right']['fill'], colors['right']['stroke'])
    ]
    legend_x = margin_left + plot_width / 2 - 150
    for j, (label, fill, stroke) in enumerate(legend_items):
        x = legend_x + j * 110
        svg_parts.append(f'<rect x="{x}" y="{legend_y - 10}" width="15" height="15" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
        svg_parts.append(f'<text x="{x + 20}" y="{legend_y + 2}" font-size="11">{label}</text>')
    
    svg_parts.append('</svg>')
    
    return '\n'.join(svg_parts)


# (removed dead function `_generate_svg_effect_by_family` — superseded by mal_site.py)


def _generate_svg_effect_by_grouping(effect_scores, group_fn, title, x_label, min_group_count=1):
    """Generate an SVG chart showing MAL effect scores by arbitrary grouping.
    
    Args:
        effect_scores: List of dicts with 'name', 'code', 'effect' (raw slope), etc.
        group_fn: Function that takes an effect_score item and returns a group label string (or None to exclude).
        title: Chart title.
        x_label: X-axis label.
        min_group_count: Minimum number of languages in a group to display it.
    """
    if not effect_scores:
        return "<p>No effect data available.</p>"
    
    # Group scores
    grouped = defaultdict(list)
    for item in effect_scores:
        grp = group_fn(item)
        if grp is not None:
            grouped[grp].append(-item['effect'])  # Negate: positive = MAL compliance
    
    if not grouped:
        return "<p>No grouping data available.</p>"
    
    # Compute stats per group
    group_stats = {}
    for grp, scores in grouped.items():
        if len(scores) >= min_group_count:
            group_stats[grp] = {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'count': len(scores),
                'min': float(np.min(scores)),
                'max': float(np.max(scores)),
                'scores': scores
            }
    
    if not group_stats:
        return "<p>Not enough data for this grouping.</p>"
    
    # Sort by mean descending (strongest MAL first)
    sorted_groups = sorted(group_stats.items(), key=lambda x: x[1]['mean'], reverse=True)
    
    # SVG dimensions
    width = 900
    height = max(250, len(sorted_groups) * 60 + 100)
    margin_left = 200
    margin_right = 50
    margin_top = 40
    margin_bottom = 60
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    
    x_min, x_max = -0.4, 0.4
    def scale_x(val):
        return margin_left + (val - x_min) / (x_max - x_min) * plot_width
    
    bar_height = min(35, (plot_height / len(sorted_groups)) * 0.7)
    bar_spacing = plot_height / len(sorted_groups)
    
    # Store individual scores by group for jitter
    group_individual = {}
    for item in effect_scores:
        grp = group_fn(item)
        if grp is not None and grp in group_stats:
            if grp not in group_individual:
                group_individual[grp] = []
            group_individual[grp].append({
                'name': item['name'],
                'effect': -item['effect']
            })
    
    color_palette = [
        '#2196F3', '#4CAF50', '#F44336', '#9C27B0', '#FF9800',
        '#00BCD4', '#E91E63', '#8BC34A', '#795548', '#3F51B5'
    ]
    
    svg_parts = []
    svg_parts.append(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: white; font-family: Arial, sans-serif;">')
    
    # Title
    svg_parts.append(f'<text x="{width/2}" y="25" text-anchor="middle" font-size="14" font-weight="bold">{title}</text>')
    
    # X-axis
    svg_parts.append(f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}" stroke="#333" stroke-width="1"/>')
    
    for i in range(-4, 5):
        x_val = i / 10
        x_pos = scale_x(x_val)
        svg_parts.append(f'<line x1="{x_pos}" y1="{margin_top + plot_height}" x2="{x_pos}" y2="{margin_top + plot_height + 5}" stroke="#333" stroke-width="1"/>')
        svg_parts.append(f'<text x="{x_pos}" y="{margin_top + plot_height + 20}" text-anchor="middle" font-size="10">{x_val:.1f}</text>')
        svg_parts.append(f'<line x1="{x_pos}" y1="{margin_top}" x2="{x_pos}" y2="{margin_top + plot_height}" stroke="#eee" stroke-width="1"/>')
    
    svg_parts.append(f'<text x="{margin_left + plot_width/2}" y="{height - 15}" text-anchor="middle" font-size="12">{x_label}</text>')
    
    # Draw bars and points
    for i, (grp, stats) in enumerate(sorted_groups):
        y_center = margin_top + (i + 0.5) * bar_spacing
        y_top = y_center - bar_height / 2
        color = color_palette[i % len(color_palette)]
        
        # Group label
        svg_parts.append(f'<text x="{margin_left - 10}" y="{y_center + 4}" text-anchor="end" font-size="11">{grp} (n={stats["count"]})</text>')
        
        # Background bar
        svg_parts.append(f'<rect x="{margin_left}" y="{y_top}" width="{plot_width}" height="{bar_height}" fill="#f5f5f5" stroke="#ddd" stroke-width="1"/>')
        
        # Mean bar
        zero_x = scale_x(0)
        mean_x = scale_x(stats['mean'])
        if stats['mean'] >= 0:
            bar_x = zero_x
            bar_width = mean_x - zero_x
        else:
            bar_x = mean_x
            bar_width = zero_x - mean_x
        svg_parts.append(f'<rect x="{bar_x}" y="{y_top}" width="{bar_width}" height="{bar_height}" fill="{color}" fill-opacity="0.6" stroke="{color}" stroke-width="1"/>')
        
        # Individual language points (jittered)
        if grp in group_individual:
            np.random.seed(hash(grp) % 2**32)
            for lang_item in group_individual[grp]:
                x_pos = scale_x(lang_item['effect'])
                x_pos = max(margin_left, min(width - margin_right, x_pos))
                jitter = (np.random.random() - 0.5) * bar_height * 0.6
                y_pos = y_center + jitter
                svg_parts.append(f'<circle cx="{x_pos}" cy="{y_pos}" r="4" fill="{color}" stroke="white" stroke-width="1">')
                svg_parts.append(f'<title>{lang_item["name"]}: {lang_item["effect"]:.3f}</title>')
                svg_parts.append('</circle>')
        
        # Mean marker
        svg_parts.append(f'<line x1="{mean_x}" y1="{y_top - 2}" x2="{mean_x}" y2="{y_top + bar_height + 2}" stroke="#333" stroke-width="2"/>')
    
    # Zero reference line
    x_zero = scale_x(0)
    svg_parts.append(f'<line x1="{x_zero}" y1="{margin_top}" x2="{x_zero}" y2="{margin_top + plot_height}" stroke="#333" stroke-width="1.5" stroke-dasharray="4,4"/>')
    svg_parts.append(f'<text x="{x_zero + 5}" y="{margin_top + 15}" font-size="10" fill="#666">0</text>')
    
    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


def _generate_svg_family_transition_heatmap(family_transition_stats):
    """Generate an SVG heatmap of mean local change scores by family × transition.
    
    Rows = language families, sorted by overall mean change score (strongest MAL first).
    Columns = transitions (1→2, 2→3, 3→4, 4→5).
    Cell color = green (negative/MAL-compliant) to red (positive/anti-MAL).
    Values are negated from the original local change scores so that negative = MAL compliance,
    consistent with the β slope convention used in Charts 6-7.
    Cell text = negated mean score (n=count).
    """
    
    if not family_transition_stats:
        return "<p>No family transition data available.</p>"
    
    transitions = ['1→2', '2→3', '3→4', '4→5']
    
    # Negate means for display: negative = MAL compliance (matching β convention)
    # Original local change = (MAL_n - MAL_{n+1}) / MAL_n is positive for compliance;
    # we negate so that negative = compliance, consistent with regression slopes.
    negated_stats = {}
    for family, trans in family_transition_stats.items():
        negated_stats[family] = {}
        for t, stats in trans.items():
            negated_stats[family][t] = {
                'mean': -stats['mean'],
                'count': stats['count'],
                'std': stats['std']
            }
    
    # Compute overall mean per family for sorting (most negative = strongest MAL first)
    family_means = {}
    for family, trans in negated_stats.items():
        all_means = [trans[t]['mean'] for t in transitions if t in trans]
        family_means[family] = np.mean(all_means) if all_means else 0
    
    # Sort families by overall mean (most negative = strongest MAL compliance first)
    sorted_families = sorted(family_means.keys(), key=lambda f: family_means[f])
    
    # Filter to families that have data in at least one transition
    sorted_families = [f for f in sorted_families if any(t in negated_stats[f] for t in transitions)]
    
    if not sorted_families:
        return "<p>No family transition data available.</p>"
    
    # Layout
    cell_w = 120
    cell_h = 40
    label_w = 180  # width for family labels
    header_h = 40  # height for column headers
    margin = 10
    
    n_rows = len(sorted_families)
    n_cols = len(transitions)
    
    svg_w = label_w + n_cols * cell_w + margin * 2
    svg_h = header_h + n_rows * cell_h + margin * 2
    
    # Find min/max for color scale (using negated values)
    all_values = []
    for family in sorted_families:
        for t in transitions:
            if t in negated_stats[family]:
                all_values.append(negated_stats[family][t]['mean'])
    
    if not all_values:
        return "<p>No family transition data available.</p>"
    
    max_abs = max(abs(v) for v in all_values) if all_values else 1
    # Symmetric scale around 0
    vmin, vmax = -max_abs, max_abs
    
    def value_to_color(val):
        """Map value to color: green (negative/MAL-compliant) to white (zero) to red (positive/anti-MAL)."""
        if val is None:
            return '#f0f0f0'
        # Normalize to [-1, 1]
        norm = max(-1, min(1, val / max_abs)) if max_abs > 0 else 0
        if norm <= 0:
            # Negative = green (MAL compliant) — matches β convention
            intensity = abs(norm)
            r = int(255 - intensity * 180)
            g = int(255 - intensity * 40)
            b = int(255 - intensity * 180)
        else:
            # Positive = red (anti-MAL)
            intensity = norm
            r = int(255 - intensity * 40)
            g = int(255 - intensity * 180)
            b = int(255 - intensity * 180)
        return f'rgb({r},{g},{b})'
    
    def text_color_for_bg(val):
        """Return black or white text depending on background brightness."""
        if val is None:
            return '#999'
        norm = abs(val / max_abs) if max_abs > 0 else 0
        return '#fff' if norm > 0.6 else '#333'
    
    lines = []
    lines.append(f'<svg width="{svg_w}" height="{svg_h}" xmlns="http://www.w3.org/2000/svg" '
                 f'style="font-family: Arial, sans-serif;">')
    
    # Column headers
    for j, t in enumerate(transitions):
        x = margin + label_w + j * cell_w + cell_w / 2
        y = margin + header_h / 2 + 5
        lines.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="13" font-weight="bold">{t}</text>')
    
    # Rows
    for i, family in enumerate(sorted_families):
        y = margin + header_h + i * cell_h
        
        # Family label
        label_x = margin + label_w - 8
        label_y = y + cell_h / 2 + 5
        # Truncate long names
        display_name = family if len(family) <= 22 else family[:20] + '…'
        lines.append(f'<text x="{label_x}" y="{label_y}" text-anchor="end" font-size="12">{display_name}</text>')
        
        # Cells
        for j, t in enumerate(transitions):
            cx = margin + label_w + j * cell_w
            cy = y
            
            if t in negated_stats[family]:
                stats = negated_stats[family][t]
                val = stats['mean']
                count = stats['count']
                bg = value_to_color(val)
                fg = text_color_for_bg(val)
                
                lines.append(f'<rect x="{cx}" y="{cy}" width="{cell_w}" height="{cell_h}" '
                             f'fill="{bg}" stroke="#ccc" stroke-width="1"/>')
                # Main value
                lines.append(f'<text x="{cx + cell_w/2}" y="{cy + cell_h/2 - 2}" text-anchor="middle" '
                             f'font-size="12" font-weight="bold" fill="{fg}">{val:.3f}</text>')
                # Count
                lines.append(f'<text x="{cx + cell_w/2}" y="{cy + cell_h/2 + 12}" text-anchor="middle" '
                             f'font-size="9" fill="{fg}">n={count}</text>')
            else:
                # No data
                lines.append(f'<rect x="{cx}" y="{cy}" width="{cell_w}" height="{cell_h}" '
                             f'fill="#f0f0f0" stroke="#ccc" stroke-width="1"/>')
                lines.append(f'<text x="{cx + cell_w/2}" y="{cy + cell_h/2 + 4}" text-anchor="middle" '
                             f'font-size="11" fill="#999">—</text>')
    
    # Color legend at the bottom
    legend_y = margin + header_h + n_rows * cell_h + 15
    legend_x = margin + label_w
    legend_w = n_cols * cell_w
    legend_h = 15
    
    # Gradient
    lines.append('<defs>')
    lines.append('<linearGradient id="heatmapGradient" x1="0%" y1="0%" x2="100%" y2="0%">')
    lines.append('<stop offset="0%" style="stop-color:rgb(75,215,75)"/>')
    lines.append('<stop offset="50%" style="stop-color:rgb(255,255,255)"/>')
    lines.append('<stop offset="100%" style="stop-color:rgb(215,75,75)"/>')
    lines.append('</linearGradient>')
    lines.append('</defs>')
    
    new_svg_h = legend_y + legend_h + 25
    lines[0] = (f'<svg width="{svg_w}" height="{new_svg_h}" xmlns="http://www.w3.org/2000/svg" '
                f'style="font-family: Arial, sans-serif;">')
    
    lines.append(f'<rect x="{legend_x}" y="{legend_y}" width="{legend_w}" height="{legend_h}" '
                 f'fill="url(#heatmapGradient)" stroke="#ccc" stroke-width="1"/>')
    lines.append(f'<text x="{legend_x}" y="{legend_y + legend_h + 14}" font-size="10" text-anchor="start">'
                 f'MAL-compliant (−{max_abs:.3f})</text>')
    lines.append(f'<text x="{legend_x + legend_w/2}" y="{legend_y + legend_h + 14}" font-size="10" text-anchor="middle">'
                 f'0</text>')
    lines.append(f'<text x="{legend_x + legend_w}" y="{legend_y + legend_h + 14}" font-size="10" text-anchor="end">'
                 f'Anti-MAL (+{max_abs:.3f})</text>')
    
    lines.append('</svg>')
    
    return '\n'.join(lines)


def _generate_svg_world_map(geo_data):
    """Generate an interactive world map using D3.js with language points colored by MAL score."""
    
    if not geo_data:
        return "<p>No geographic data available. Provide WALS languages.csv path to enable the world map.</p>"
    
    # Convert geo_data to JSON for JavaScript
    geo_data_json = json.dumps(geo_data)
    
    # Generate unique ID to avoid conflicts if multiple maps on page
    map_id = "worldMap"
    
    return f'''
<div id="{map_id}" style="width: 100%; max-width: 1000px; margin: 0 auto;"></div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script src="https://d3js.org/topojson.v3.min.js"></script>

<script>
(function() {{
    const geoData = {geo_data_json};
    const container = document.getElementById("{map_id}");
    
    // Dimensions
    const width = Math.min(1000, container.clientWidth || 1000);
    const height = width * 0.5;
    
    // Create SVG
    const svg = d3.select("#{map_id}")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .style("background", "#f0f8ff")
        .style("border-radius", "8px")
        .style("border", "1px solid #ddd");
    
    // Projection (Natural Earth for nice appearance)
    const projection = d3.geoNaturalEarth1()
        .scale(width / 5.5)
        .translate([width / 2, height / 2]);
    
    const path = d3.geoPath().projection(projection);
    
    // Color scale for −β(2→max) scores: positive = MAL compliance (green), negative = anti-MAL (red)
    function scoreToColor(score) {{
        if (score > 0.1) {{
            // Green for MAL compliance (positive −β means size decreases with n)
            const t = Math.min(1, score / 0.3);
            return d3.interpolateRgb("#b8e6b8", "#2e7d32")(t);
        }} else if (score < -0.1) {{
            // Red for anti-MAL (negative −β)
            const t = Math.min(1, Math.abs(score) / 0.3);
            return d3.interpolateRgb("#ffcdd2", "#c62828")(t);
        }} else {{
            // Yellow for neutral
            return "#ffc107";
        }}
    }}
    
    // Create tooltip
    const tooltip = d3.select("body").append("div")
        .attr("class", "map-tooltip")
        .style("position", "absolute")
        .style("visibility", "hidden")
        .style("background", "rgba(255, 255, 255, 0.95)")
        .style("border", "1px solid #ccc")
        .style("border-radius", "6px")
        .style("padding", "10px")
        .style("font-size", "12px")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000");
    
    // Load world map data
    d3.json("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json").then(function(world) {{
        // Draw countries
        svg.append("g")
            .selectAll("path")
            .data(topojson.feature(world, world.objects.countries).features)
            .enter().append("path")
            .attr("d", path)
            .attr("fill", "#e8e8e8")
            .attr("stroke", "#999")
            .attr("stroke-width", 0.5);
        
        // Draw country borders
        svg.append("path")
            .datum(topojson.mesh(world, world.objects.countries, (a, b) => a !== b))
            .attr("fill", "none")
            .attr("stroke", "#aaa")
            .attr("stroke-width", 0.3)
            .attr("d", path);
        
        // Add graticule (grid lines)
        const graticule = d3.geoGraticule().step([30, 30]);
        svg.append("path")
            .datum(graticule)
            .attr("d", path)
            .attr("fill", "none")
            .attr("stroke", "#ddd")
            .attr("stroke-width", 0.3);
        
        // Draw language points
        svg.selectAll("circle.lang-point")
            .data(geoData.sort((a, b) => Math.abs(a.mal_score) - Math.abs(b.mal_score)))
            .enter().append("circle")
            .attr("class", "lang-point")
            .attr("cx", d => projection([d.lon, d.lat])[0])
            .attr("cy", d => projection([d.lon, d.lat])[1])
            .attr("r", 5)
            .attr("fill", d => scoreToColor(d.mal_score))
            .attr("stroke", "white")
            .attr("stroke-width", 1.5)
            .attr("opacity", 0.85)
            .style("cursor", "pointer")
            .on("mouseover", function(event, d) {{
                d3.select(this).attr("r", 8).attr("stroke-width", 2);
                tooltip.style("visibility", "visible")
                    .html(`<strong>${{d.name}}</strong><br/>
                           −β(2→max): ${{d.mal_score.toFixed(3)}}<br/>
                           Family: ${{d.family}}<br/>
                           Data points: ${{d.n_points}}`);
            }})
            .on("mousemove", function(event) {{
                tooltip.style("top", (event.pageY - 10) + "px")
                       .style("left", (event.pageX + 10) + "px");
            }})
            .on("mouseout", function() {{
                d3.select(this).attr("r", 5).attr("stroke-width", 1.5);
                tooltip.style("visibility", "hidden");
            }});
        
        // Add legend
        const legendData = [
            {{ label: "Strong MAL (>0.2)", score: 0.3 }},
            {{ label: "Moderate MAL", score: 0.15 }},
            {{ label: "Weak/Neutral", score: 0 }},
            {{ label: "Anti-MAL (<-0.1)", score: -0.2 }}
        ];
        
        const legend = svg.append("g")
            .attr("transform", `translate(${{width - 140}}, ${{height - 100}})`);
        
        legend.append("rect")
            .attr("x", -10)
            .attr("y", -25)
            .attr("width", 135)
            .attr("height", 100)
            .attr("fill", "white")
            .attr("stroke", "#ccc")
            .attr("rx", 5)
            .attr("opacity", 0.9);
        
        legend.append("text")
            .attr("x", 0)
            .attr("y", -8)
            .attr("font-size", "11px")
            .attr("font-weight", "bold")
            .text("−β(2→max)");
        
        legendData.forEach((item, i) => {{
            legend.append("circle")
                .attr("cx", 8)
                .attr("cy", 12 + i * 18)
                .attr("r", 5)
                .attr("fill", scoreToColor(item.score))
                .attr("stroke", "white")
                .attr("stroke-width", 1);
            
            legend.append("text")
                .attr("x", 20)
                .attr("y", 16 + i * 18)
                .attr("font-size", "10px")
                .text(item.label);
        }});
        
        // Add language count
        svg.append("text")
            .attr("x", 10)
            .attr("y", height - 10)
            .attr("font-size", "10px")
            .attr("fill", "#666")
            .text(`Languages shown: ${{geoData.length}}`);
            
    }}).catch(function(error) {{
        console.error("Error loading world map:", error);
        svg.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .attr("fill", "#666")
            .text("Could not load world map. Check internet connection.");
    }});
}})();
</script>
'''


def _generate_svg_categorical_world_map(points, map_id, legend_palette, legend_field,
                                        legend_title='', shape_field=None,
                                        shape_palette=None, shape_title='',
                                        external_legend_html=None):
    """D3-based world map for *categorical* point coloring (family / VO/OV / …).

    Same look-and-feel as `_generate_svg_world_map` (Natural-Earth projection,
    country fills, graticule, hover tooltip) but colored from a pre-computed
    palette rather than a numeric score.

    Optionally a second visual dimension can be encoded as the *shape* of the
    marker (e.g. a genealogical macro-group), useful when there are too many
    color classes to disambiguate by color alone.

    Legends are rendered as **HTML next to the SVG** (flex side-by-side on
    wide screens, stacked below on narrow ones) so they never occlude points
    on the map.

    Parameters
    ----------
    points : list[dict]
        Each dict must have ``name``, ``lat``, ``lon`` and the field named by
        ``legend_field`` (e.g. ``family``, ``vo``). When ``shape_field`` is
        given, each dict must also carry that field.
    map_id : str
        Unique DOM id for the container.
    legend_palette : dict[label -> color]
        Insertion-ordered dict of category label → hex/css color.
        Used for point coloring (and, when no ``external_legend_html`` is
        supplied, to render a default HTML color legend).
    legend_field : str
        Field name used to look up the color for each point and to display in
        the tooltip.
    legend_title : str
        Title shown above the default HTML color legend.
    shape_field : str or None
        Optional field name (e.g. ``"macro_group"``) used to pick a D3 symbol
        shape per point. ``None`` → all points are circles.
    shape_palette : dict[label -> shape_name] or None
        Mapping from shape-category label to one of D3's symbol names:
        ``circle``, ``square``, ``diamond``, ``triangle``, ``cross``, ``star``,
        ``wye``. Required when ``shape_field`` is given.
    shape_title : str
        Title shown above the default HTML shape legend.
    external_legend_html : str or None
        Pre-rendered HTML (typically combining color + shape sections in a
        custom way, e.g. families grouped under their macro-group). When
        supplied, this entirely replaces the default auto-generated legend.
    """
    if not points:
        return "<p>No geographic data available.</p>"

    points_json = json.dumps(points)
    palette_json = json.dumps(legend_palette)
    shape_palette_json = json.dumps(shape_palette or {})
    shape_field_js = json.dumps(shape_field or '')
    shape_title_js = json.dumps(shape_title or '')

    # --- Build the HTML legend (default auto-generated, unless caller passed one).
    if external_legend_html is None:
        rows = []
        rows.append(f'<div class="map-legend-block"><div class="map-legend-title">'
                    f'{legend_title or legend_field}</div><ul class="map-legend-list">')
        for lab, col in legend_palette.items():
            rows.append(f'<li><span class="map-legend-swatch" '
                        f'style="background:{col};"></span>{lab}</li>')
        rows.append('</ul></div>')
        if shape_field and shape_palette:
            rows.append(f'<div class="map-legend-block"><div class="map-legend-title">'
                        f'{shape_title or shape_field}</div><ul class="map-legend-list">')
            for lab, shp in shape_palette.items():
                rows.append(f'<li><span class="map-legend-shape" '
                            f'data-shape="{shp}"></span>{lab}</li>')
            rows.append('</ul></div>')
        external_legend_html = ''.join(rows)

    return f'''
<style>
.map-flex-{map_id} {{
    display: flex; flex-wrap: wrap; gap: 16px;
    align-items: flex-start; margin: 0 auto;
}}
.map-flex-{map_id} .map-area {{
    flex: 1 1 640px; min-width: 320px; max-width: 1000px;
}}
.map-flex-{map_id} .map-legend-panel {{
    flex: 0 0 240px; max-width: 280px;
    font-size: 12px; line-height: 1.35;
    background: #fafafa; border: 1px solid #ddd; border-radius: 6px;
    padding: 10px 12px;
}}
.map-flex-{map_id} .map-legend-block {{ margin: 0 0 12px 0; }}
.map-flex-{map_id} .map-legend-block:last-child {{ margin-bottom: 0; }}
.map-flex-{map_id} .map-legend-title {{
    font-weight: bold; font-size: 12px; margin-bottom: 4px;
    color: #333; border-bottom: 1px solid #e0e0e0; padding-bottom: 2px;
}}
.map-flex-{map_id} .map-legend-list {{
    list-style: none; padding: 0; margin: 0;
}}
.map-flex-{map_id} .map-legend-list li {{
    display: flex; align-items: center; gap: 6px;
    padding: 1px 0; font-size: 11px;
}}
.map-flex-{map_id} .map-legend-list li.macro-group-header {{
    font-weight: bold; margin-top: 4px; padding-top: 3px;
    border-top: 1px dashed #d0d0d0; color: #444;
}}
.map-flex-{map_id} .map-legend-list li.macro-group-header:first-child {{
    border-top: none; margin-top: 0; padding-top: 0;
}}
.map-flex-{map_id} .map-legend-swatch {{
    display: inline-block; width: 12px; height: 12px; border-radius: 50%;
    border: 1px solid rgba(0,0,0,0.25); flex: 0 0 auto;
}}
.map-flex-{map_id} .map-legend-shape {{
    display: inline-block; width: 14px; height: 14px; flex: 0 0 auto;
    background-repeat: no-repeat; background-position: center;
    background-size: contain;
}}
.map-flex-{map_id} .map-legend-shape[data-shape="circle"] {{
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='-6 -6 12 12'><circle r='5' fill='%23555'/></svg>");
}}
.map-flex-{map_id} .map-legend-shape[data-shape="square"] {{
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='-6 -6 12 12'><rect x='-4.5' y='-4.5' width='9' height='9' fill='%23555'/></svg>");
}}
.map-flex-{map_id} .map-legend-shape[data-shape="diamond"] {{
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='-6 -6 12 12'><polygon points='0,-5.5 5,0 0,5.5 -5,0' fill='%23555'/></svg>");
}}
.map-flex-{map_id} .map-legend-shape[data-shape="triangle"] {{
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='-6 -6 12 12'><polygon points='0,-5.5 5,4 -5,4' fill='%23555'/></svg>");
}}
.map-flex-{map_id} .map-legend-shape[data-shape="cross"] {{
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='-6 -6 12 12'><polygon points='-1.5,-5 1.5,-5 1.5,-1.5 5,-1.5 5,1.5 1.5,1.5 1.5,5 -1.5,5 -1.5,1.5 -5,1.5 -5,-1.5 -1.5,-1.5' fill='%23555'/></svg>");
}}
.map-flex-{map_id} .map-legend-shape[data-shape="star"] {{
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='-6 -6 12 12'><polygon points='0,-5.5 1.6,-1.7 5.5,-1.7 2.4,0.7 3.6,4.5 0,2.2 -3.6,4.5 -2.4,0.7 -5.5,-1.7 -1.6,-1.7' fill='%23555'/></svg>");
}}
.map-flex-{map_id} .map-legend-shape[data-shape="wye"] {{
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='-6 -6 12 12'><path d='M-1.5,-5 L1.5,-5 L1.5,-1.2 L4.7,2.4 L3.2,4 L0,1.2 L-3.2,4 L-4.7,2.4 L-1.5,-1.2 Z' fill='%23555'/></svg>");
}}
</style>
<div class="map-flex-{map_id}">
  <div class="map-area"><div id="{map_id}"></div></div>
  <div class="map-legend-panel">{external_legend_html}</div>
</div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script src="https://d3js.org/topojson.v3.min.js"></script>

<script>
(function() {{
    const points = {points_json};
    const palette = {palette_json};
    const shapePalette = {shape_palette_json};
    const shapeField = {shape_field_js};
    const shapeTitle = {shape_title_js};
    const legendField = "{legend_field}";
    const legendTitle = "{legend_title}";
    const container = document.getElementById("{map_id}");

    // Cross-chart "linked brushing" bus: a single d3.dispatch shared by every
    // chart on the page so hovering one language anywhere broadcasts a
    // highlight event that the other charts can react to.
    const bus = window.__malBus = window.__malBus || d3.dispatch('highlight');

    // Map shape-name → D3 symbol type.
    const SHAPE_TYPES = {{
        circle:   d3.symbolCircle,
        square:   d3.symbolSquare,
        diamond:  d3.symbolDiamond,
        triangle: d3.symbolTriangle,
        cross:    d3.symbolCross,
        star:     d3.symbolStar,
        wye:      d3.symbolWye,
    }};
    function shapeForPoint(d) {{
        if (!shapeField) return d3.symbolCircle;
        const cat = d[shapeField];
        const name = shapePalette[cat];
        return SHAPE_TYPES[name] || d3.symbolCircle;
    }}
    const SYMBOL_AREA = 70;
    const SYMBOL_AREA_HOVER = 180;
    const symbolGen = d3.symbol().size(SYMBOL_AREA);
    const symbolGenHover = d3.symbol().size(SYMBOL_AREA_HOVER);

    const width = Math.min(1000, container.clientWidth || 1000);
    const height = width * 0.5;

    const svg = d3.select("#{map_id}")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .style("background", "#f0f8ff")
        .style("border-radius", "8px")
        .style("border", "1px solid #ddd");

    const projection = d3.geoNaturalEarth1()
        .scale(width / 5.5)
        .translate([width / 2, height / 2]);
    const path = d3.geoPath().projection(projection);

    const tooltip = d3.select("body").append("div")
        .attr("class", "map-tooltip")
        .style("position", "absolute")
        .style("visibility", "hidden")
        .style("background", "rgba(255,255,255,0.95)")
        .style("border", "1px solid #ccc")
        .style("border-radius", "6px")
        .style("padding", "8px 10px")
        .style("font-size", "12px")
        .style("box-shadow", "0 2px 8px rgba(0,0,0,0.15)")
        .style("pointer-events", "none")
        .style("z-index", "1000");

    d3.json("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json").then(function(world) {{
        svg.append("g")
            .selectAll("path")
            .data(topojson.feature(world, world.objects.countries).features)
            .enter().append("path")
            .attr("d", path)
            .attr("fill", "#e8e8e8")
            .attr("stroke", "#999")
            .attr("stroke-width", 0.5);

        svg.append("path")
            .datum(topojson.mesh(world, world.objects.countries, (a, b) => a !== b))
            .attr("fill", "none")
            .attr("stroke", "#aaa")
            .attr("stroke-width", 0.3)
            .attr("d", path);

        const graticule = d3.geoGraticule().step([30, 30]);
        svg.append("path")
            .datum(graticule)
            .attr("d", path)
            .attr("fill", "none")
            .attr("stroke", "#ddd")
            .attr("stroke-width", 0.3);

        svg.selectAll("path.lang-point")
            .data(points)
            .enter().append("path")
            .attr("class", "lang-point")
            .attr("data-code", d => d.code || '')
            .attr("transform", d => {{
                const p = projection([d.lon, d.lat]);
                return "translate(" + p[0] + "," + p[1] + ")";
            }})
            .attr("d", d => symbolGen.type(shapeForPoint(d))())
            .attr("fill", d => d.color || "#999")
            .attr("stroke", "white")
            .attr("stroke-width", 1.0)
            .attr("opacity", 0.9)
            .style("cursor", "pointer")
            .on("mouseover", function(event, d) {{
                d3.select(this)
                    .attr("d", symbolGenHover.type(shapeForPoint(d))())
                    .attr("stroke-width", 1.8);
                let tt = "<strong>" + d.name + "</strong><br/>"
                       + (legendTitle || legendField) + ": " + (d[legendField] || "");
                if (shapeField) {{
                    tt += "<br/>" + (shapeTitle || shapeField) + ": " + (d[shapeField] || "");
                }}
                tooltip.style("visibility", "visible").html(tt);
                if (d.code) bus.call('highlight', null, d.code);
            }})
            .on("mousemove", function(event) {{
                tooltip.style("top", (event.pageY - 10) + "px")
                       .style("left", (event.pageX + 10) + "px");
            }})
            .on("mouseout", function(event, d) {{
                d3.select(this)
                    .attr("d", symbolGen.type(shapeForPoint(d))())
                    .attr("stroke-width", 1.0);
                tooltip.style("visibility", "hidden");
                bus.call('highlight', null, null);
            }});

        // Linked-brushing receiver: when another chart on the page emits a
        // highlight event, find the matching point and scale it up with a
        // black outline so the user can locate the same language across maps.
        bus.on('highlight.{map_id}', function(code) {{
            svg.selectAll('path.lang-point')
              .each(function(d) {{
                const sel = d3.select(this);
                if (code && d.code === code) {{
                    sel.attr('d', symbolGenHover.type(shapeForPoint(d))())
                       .attr('stroke', '#000').attr('stroke-width', 2);
                }} else {{
                    sel.attr('d', symbolGen.type(shapeForPoint(d))())
                       .attr('stroke', 'white').attr('stroke-width', 1.0);
                }}
              }});
        }});

        // Legends are rendered as HTML next to the SVG (see the wrapper
        // .map-flex-* container), so nothing is drawn inside the SVG here.

        svg.append("text")
            .attr("x", 10).attr("y", height - 10)
            .attr("font-size", "10px").attr("fill", "#666")
            .text("Languages shown: " + points.length);
    }}).catch(function(error) {{
        console.error("Error loading world map:", error);
        svg.append("text")
            .attr("x", width / 2).attr("y", height / 2)
            .attr("text-anchor", "middle").attr("fill", "#666")
            .text("Could not load world map. Check internet connection.");
    }});
}})();
</script>
'''


# (removed dead function `generate_directional_mal_html_report` — superseded by mal_site.py)


# (removed dead function `_get_directional_html_header` — superseded by mal_site.py)


# (removed dead function `_get_directional_charts_section` — superseded by mal_site.py)

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


def generate_loglog_svg(mal_data, start_n=1, width=120, height=60, lang_name="", lang_code="", mal_label="MAL"):
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
        
    Returns:
        Tuple of (svg_string, slope) or (empty_svg, None) if insufficient data
    """
    regression = compute_loglog_regression(mal_data, start_n)
    
    if regression is None or len(regression['points']) < 2:
        # Return empty placeholder
        return f'<svg width="{width}" height="{height}" style="background:#f9f9f9;border-radius:3px;"><text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle" font-size="10" fill="#999">—</text></svg>', None
    
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
    
    # Get bounds
    all_x = [p[0] for p in points] + [r[0] for r in reg_line]
    all_y = [p[1] for p in points] + [r[1] for r in reg_line]
    
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    
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
        'reg_line': [[float(r[0]), float(r[1])] for r in reg_line]
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


def _compute_chart_data(lang2MAL_total, lang2local_scores, langNames, langnameGroup=None):
    """
    Compute all data needed for the charts.
    
    Returns dict with:
        - chart_data: transition -> list of scores
        - mean_curve: n -> (mean, std, count)
        - language_curves: list of {name, values, group}
        - data_availability: n -> count of languages
        - normalized_curve: n -> stats for MAL_n/MAL_1 normalized values
        - box_plot_data: transition -> {min, q1, median, q3, max, outliers}
    """
    # Determine max_n
    all_n_values = set()
    for data in lang2MAL_total.values():
        all_n_values.update(data.keys())
    max_n = max(all_n_values) if all_n_values else 6
    
    # Local change score distributions
    chart_data = defaultdict(list)
    for lang, scores in lang2local_scores.items():
        for transition, score in scores.items():
            if not np.isnan(score):
                chart_data[transition].append(score)
    
    # Mean MAL curve with confidence
    mean_curve = {}
    for n in range(1, max_n + 1):
        values = [lang2MAL_total[lang][n] for lang in lang2MAL_total if n in lang2MAL_total[lang]]
        if values:
            mean_curve[n] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'count': len(values),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'q1': float(np.percentile(values, 25)),
                'median': float(np.median(values)),
                'q3': float(np.percentile(values, 75))
            }
    
    # Normalized MAL curve (MAL_n / MAL_2)
    normalized_curve = {}
    for n in range(2, max_n + 1):
        normalized_values = []
        for lang in lang2MAL_total:
            if 2 in lang2MAL_total[lang] and n in lang2MAL_total[lang]:
                mal_2 = lang2MAL_total[lang][2]
                mal_n = lang2MAL_total[lang][n]
                if mal_2 > 0:
                    normalized_values.append(mal_n / mal_2)
        if normalized_values:
            normalized_curve[n] = {
                'mean': float(np.mean(normalized_values)),
                'std': float(np.std(normalized_values)),
                'count': len(normalized_values),
                'min': float(np.min(normalized_values)),
                'max': float(np.max(normalized_values)),
                'q1': float(np.percentile(normalized_values, 25)),
                'median': float(np.median(normalized_values)),
                'q3': float(np.percentile(normalized_values, 75))
            }
    
    # Box plot data for local change scores
    box_plot_data = {}
    for transition, scores in chart_data.items():
        if scores:
            scores_sorted = sorted(scores)
            q1 = float(np.percentile(scores_sorted, 25))
            median = float(np.median(scores_sorted))
            q3 = float(np.percentile(scores_sorted, 75))
            iqr = q3 - q1
            lower_fence = q1 - 1.5 * iqr
            upper_fence = q3 + 1.5 * iqr
            
            # Whiskers extend to min/max within fences
            whisker_low = min([s for s in scores_sorted if s >= lower_fence], default=q1)
            whisker_high = max([s for s in scores_sorted if s <= upper_fence], default=q3)
            
            # Outliers are points beyond fences
            outliers = [s for s in scores_sorted if s < lower_fence or s > upper_fence]
            
            box_plot_data[transition] = {
                'min': float(whisker_low),
                'q1': q1,
                'median': median,
                'q3': q3,
                'max': float(whisker_high),
                'outliers': outliers,
                'count': len(scores)
            }
    
    # Individual language curves
    language_curves = []
    for lang, mal_data in lang2MAL_total.items():
        lang_name = langNames.get(lang, lang)
        group = langnameGroup.get(lang_name, 'Other') if langnameGroup else 'Other'
        curve = {
            'name': lang_name,
            'code': lang,
            'group': group,
            'values': {int(n): float(v) for n, v in mal_data.items()}
        }
        language_curves.append(curve)
    
    # Data availability
    data_availability = {}
    for n in range(1, max_n + 1):
        count = sum(1 for lang in lang2MAL_total if n in lang2MAL_total[lang])
        data_availability[n] = count
    
    # β(2→max) vs β(1→2) scatter plot data
    beta_scatter = []
    for lang, mal_data in lang2MAL_total.items():
        lang_name = langNames.get(lang, lang)
        group = langnameGroup.get(lang_name, 'Other') if langnameGroup else 'Other'
        
        # Compute β(1→2): local change score for n=1→2
        scores = lang2local_scores.get(lang, {})
        beta_1_2 = scores.get('1→2', None)
        if beta_1_2 is None or np.isnan(beta_1_2):
            continue
        
        # Compute β(2→max): log-log regression slope from n=2
        regression = compute_loglog_regression(mal_data, start_n=2)
        if regression is None:
            continue
        beta_2max = regression['slope']
        
        beta_scatter.append({
            'name': lang_name,
            'code': lang,
            'group': group,
            'beta_1_2': float(beta_1_2),
            'beta_2max': float(beta_2max),
            'r_squared': float(regression['r_squared'])
        })
    
    # Effect score: β(1→max) = log-log regression slope from n=1 (the MAL effect)
    effect_scores = []
    for lang, mal_data in lang2MAL_total.items():
        lang_name = langNames.get(lang, lang)
        group = langnameGroup.get(lang_name, 'Other') if langnameGroup else 'Other'
        
        regression = compute_loglog_regression(mal_data, start_n=1)
        if regression is None:
            continue
        effect = float(regression['slope'])
        r_squared = float(regression['r_squared'])
        
        effect_scores.append({
            'name': lang_name,
            'code': lang,
            'group': group,
            'effect': effect,
            'r_squared': r_squared,
            'n_points': len(regression['n_values'])
        })
    
    # Group effect scores by family for visualization
    effect_by_family = defaultdict(list)
    for item in effect_scores:
        effect_by_family[item['group']].append(item['effect'])
    
    # Compute family statistics
    family_stats = {}
    for family, scores in effect_by_family.items():
        if scores:
            family_stats[family] = {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'count': len(scores),
                'min': float(np.min(scores)),
                'max': float(np.max(scores))
            }
    
    # Create lookup dict for effect scores by language code
    effect_by_lang = {item['code']: item['effect'] for item in effect_scores}
    group_by_lang = {item['code']: item['group'] for item in effect_scores}
    
    # R² distribution for β(1→max) regressions
    r2_distribution = []
    for lang, mal_data in lang2MAL_total.items():
        reg = compute_loglog_regression(mal_data, start_n=1)
        if reg is not None:
            lang_name = langNames.get(lang, lang)
            group = langnameGroup.get(lang_name, 'Other') if langnameGroup else 'Other'
            r2_distribution.append({
                'name': lang_name,
                'code': lang,
                'group': group,
                'r_squared': float(reg['r_squared']),
                'slope': float(reg['slope']),
                'n_points': len(reg['n_values'])
            })
    
    # Family × Transition heatmap: mean local change score per family per transition
    family_transition = {}
    for lang, scores in lang2local_scores.items():
        lang_name = langNames.get(lang, lang)
        group = langnameGroup.get(lang_name, 'Other') if langnameGroup else 'Other'
        if group not in family_transition:
            family_transition[group] = {}
        for transition, score in scores.items():
            if not np.isnan(score):
                if transition not in family_transition[group]:
                    family_transition[group][transition] = []
                family_transition[group][transition].append(score)
    
    # Aggregate into means and counts
    family_transition_stats = {}
    for family, transitions in family_transition.items():
        family_transition_stats[family] = {}
        for transition, values in transitions.items():
            family_transition_stats[family][transition] = {
                'mean': float(np.mean(values)),
                'count': len(values),
                'std': float(np.std(values)) if len(values) > 1 else 0.0
            }
    
    return {
        'chart_data': {k: v for k, v in sorted(chart_data.items())},
        'mean_curve': mean_curve,
        'normalized_curve': normalized_curve,
        'box_plot_data': box_plot_data,
        'language_curves': language_curves,
        'data_availability': data_availability,
        'beta_scatter': beta_scatter,
        'effect_scores': effect_scores,
        'effect_by_lang': effect_by_lang,
        'group_by_lang': group_by_lang,
        'family_stats': family_stats,
        'r2_distribution': r2_distribution,
        'family_transition_stats': family_transition_stats,
        'max_n': max_n
    }


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
        
        # Compute global MAL score: β(1→max) log-log regression slope
        regression = compute_loglog_regression(mal_data, start_n=1)
        mal_score = float(regression['slope']) if regression else 0.0
        
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
            
            geo_data.append({
                'name': lang_name,
                'code': lang_code,
                'lat': float(match['Latitude']),
                'lon': float(match['Longitude']),
                'mal_score': mal_score,
                'family': family,
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


def generate_mal_html_report(
    lang2MAL_total,
    lang2counts,
    langNames,
    output_path,
    min_count=None,
    langnameGroup=None,
    wals_languages_path=None,
    lang2MAL_left=None,
    lang2MAL_right=None,
    lang2counts_left=None,
    lang2counts_right=None,
    lang_to_vo=None
):
    """
    Generate an interactive HTML report for MAL analysis.
    
    Args:
        lang2MAL_total: Dict mapping lang -> n -> MAL value (bilateral/total)
        lang2counts: Dict mapping lang -> n -> count (for total)
        langNames: Dict mapping lang code -> full language name
        output_path: Path to save the HTML file
        min_count: Minimum count threshold used in the analysis. Defaults to DEFAULT_MIN_COUNT.
        langnameGroup: Optional dict mapping language name -> language family/group
        wals_languages_path: Optional path to WALS languages.csv for geographic data
        lang2MAL_left: Optional dict mapping lang -> n -> MAL value (left deps, any right)
        lang2MAL_right: Optional dict mapping lang -> n -> MAL value (right deps, any left)
        lang2counts_left: Optional dict mapping lang -> n -> count for left configs
        lang2counts_right: Optional dict mapping lang -> n -> count for right configs
        lang_to_vo: Optional dict mapping lang code -> VO score (0-1)
        
    Returns:
        Dict with statistics about the generated report
    """
    if min_count is None:
        min_count = DEFAULT_MIN_COUNT
    
    # Filter lang2MAL_total to only include n-values with sufficient count (≥ min_count)
    # This ensures charts only reflect languages with reliable data at each n
    lang2MAL_filtered = _filter_mal_by_count(lang2MAL_total, lang2counts, min_count)
    
    # Compute local change scores on filtered data
    lang2local_scores = compute_local_scores_for_all_languages(lang2MAL_filtered)
    
    # Compute chart data using filtered data
    viz_data = _compute_chart_data(lang2MAL_filtered, lang2local_scores, langNames, langnameGroup)
    max_n = viz_data['max_n']
    
    # Add geographic data if WALS path provided
    if wals_languages_path and os.path.exists(wals_languages_path):
        geo_data = _load_geographic_data(wals_languages_path, lang2MAL_total, lang2local_scores, langNames)
        viz_data['geo_data'] = geo_data
    else:
        viz_data['geo_data'] = []
    max_n = viz_data['max_n']
    
    # Sort languages alphabetically by name
    lang_names_sorted = sorted(
        [(lang, langNames.get(lang, lang)) for lang in lang2MAL_total.keys()],
        key=lambda x: x[1].lower()
    )
    
    # Prepare directional data if provided
    has_directional = (lang2MAL_left is not None and lang2MAL_right is not None)
    if has_directional:
        lang2counts_left = lang2counts_left or {}
        lang2counts_right = lang2counts_right or {}
        # Filter directional data by min_count too
        lang2MAL_left_filtered = _filter_mal_by_count(lang2MAL_left, lang2counts_left, min_count)
        lang2MAL_right_filtered = _filter_mal_by_count(lang2MAL_right, lang2counts_right, min_count)
        lang2local_scores_left = compute_local_scores_for_all_languages(lang2MAL_left_filtered)
        lang2local_scores_right = compute_local_scores_for_all_languages(lang2MAL_right_filtered)
        viz_data_left = _compute_chart_data(lang2MAL_left_filtered, lang2local_scores_left, langNames, langnameGroup)
        viz_data_right = _compute_chart_data(lang2MAL_right_filtered, lang2local_scores_right, langNames, langnameGroup)
    
    # Build HTML
    html_parts = []
    html_parts.append(_get_html_header_with_nav(min_count, has_directional))
    
    # Section 1: Total (Bilateral) Analysis
    if has_directional:
        html_parts.append('<h2 id="total-section">1. Total Dependents Analysis (Bilateral)</h2>')
        html_parts.append('<p>This section shows MAL analysis for total dependents (left + right combined).</p>')
    
    # Table
    html_parts.append(_build_table(lang_names_sorted, lang2MAL_total, lang2counts, lang2local_scores, viz_data['effect_by_lang'], viz_data['group_by_lang'], max_n, min_count,
        table_id="malTable_total", include_sort_script=True, lang_to_vo=lang_to_vo, mal_label="MAL"))
    
    # Table explanation
    html_parts.append(_get_table_explanation(min_count))
    
    # Slope distribution summary table
    html_parts.append(_generate_slope_summary_table(lang2MAL_filtered, lang2local_scores))
    
    # Charts section (pass directional data if available for combined chart)
    if has_directional:
        html_parts.append(_get_charts_section(viz_data, min_count, viz_data_left, viz_data_right))
    else:
        html_parts.append(_get_charts_section(viz_data, min_count))
    
    # Directional sections if data provided
    n_languages_left = 0
    n_languages_right = 0
    if has_directional:
        # Section 2: Left Dependents
        html_parts.append('<h2 id="left-section">2. Left Dependents Analysis</h2>')
        html_parts.append('<p>MAL analysis for <strong>left-side dependents</strong> (n dependents to the left of the verb, regardless of how many are on the right).</p>')
        
        left_lang_names = [(l, n) for l, n in lang_names_sorted if l in lang2MAL_left and lang2MAL_left[l]]
        n_languages_left = len(left_lang_names)
        if left_lang_names:
            max_n_left = max(max(d.keys()) for d in lang2MAL_left.values() if d) if lang2MAL_left else 6
            html_parts.append(_build_table(
                left_lang_names, lang2MAL_left, lang2counts_left,
                lang2local_scores_left, viz_data_left.get('effect_by_lang', {}),
                viz_data_left.get('group_by_lang', {}), max_n_left, min_count,
                table_id="malTable_left", include_sort_script=False, lang_to_vo=lang_to_vo, mal_label="Left MAL"
            ))
            html_parts.append(_get_directional_charts_section(viz_data_left, "Left", min_count))
        else:
            html_parts.append('<p><em>No left dependent data available.</em></p>')
        
        # Section 3: Right Dependents
        html_parts.append('<h2 id="right-section">3. Right Dependents Analysis</h2>')
        html_parts.append('<p>MAL analysis for <strong>right-side dependents</strong> (n dependents to the right of the verb, regardless of how many are on the left).</p>')
        
        right_lang_names = [(l, n) for l, n in lang_names_sorted if l in lang2MAL_right and lang2MAL_right[l]]
        n_languages_right = len(right_lang_names)
        if right_lang_names:
            max_n_right = max(max(d.keys()) for d in lang2MAL_right.values() if d) if lang2MAL_right else 6
            html_parts.append(_build_table(
                right_lang_names, lang2MAL_right, lang2counts_right,
                lang2local_scores_right, viz_data_right.get('effect_by_lang', {}),
                viz_data_right.get('group_by_lang', {}), max_n_right, min_count,
                table_id="malTable_right", include_sort_script=False, lang_to_vo=lang_to_vo, mal_label="Right MAL"
            ))
            html_parts.append(_get_directional_charts_section(viz_data_right, "Right", min_count))
        else:
            html_parts.append('<p><em>No right dependent data available.</em></p>')
    
    # Footer
    html_parts.append('</body>\n</html>')
    
    # Write HTML file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    html_content = ''.join(html_parts)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Return statistics
    result = {
        'output_path': output_path,
        'n_languages': len(lang_names_sorted),
        'max_n': max_n,
        'n_transitions': len(viz_data['chart_data']),
        'chart_data': viz_data['chart_data']
    }
    if has_directional:
        result['n_languages_left'] = n_languages_left
        result['n_languages_right'] = n_languages_right
    return result


def _build_table(lang_names_sorted, lang2MAL_total, lang2counts, lang2local_scores, effect_by_lang, group_by_lang, max_n, min_count=None, table_id="malTable", include_sort_script=True, lang_to_vo=None, mal_label="MAL"):
    """Build the HTML table with sortable columns and inline log-log regression plots.
    
    Args:
        min_count: Minimum count for a value to be included in regressions/statistics.
                   Values below this threshold are shown greyed out. Defaults to DEFAULT_MIN_COUNT.
        table_id: Unique ID for the table element (for multiple tables on same page).
        include_sort_script: Whether to include the sorting JavaScript. Set to False for
                            subsequent tables to avoid duplicate declarations.
        lang_to_vo: Optional dict mapping lang code -> VO score (0-1).
        mal_label: Label for MAL type ('MAL', 'Left MAL', 'Right MAL').
    """
    if min_count is None:
        min_count = DEFAULT_MIN_COUNT
    html_parts = []
    
    # Table header with sortable columns
    html_parts.append(f'<table id="{table_id}">\n<thead>\n<tr>\n')
    html_parts.append(f'<th onclick="sortTable(\'{table_id}\', 0, \'string\')" style="cursor:pointer">Language ⇅</th>\n')
    html_parts.append(f'<th class="vo-col" onclick="sortTable(\'{table_id}\', 1, \'number\')" style="cursor:pointer">VO ⇅</th>\n')
    html_parts.append(f'<th class="group-col" onclick="sortTable(\'{table_id}\', 2, \'string\')" style="cursor:pointer">Family ⇅</th>\n')
    html_parts.append(f'<th class="effect-col" onclick="sortTable(\'{table_id}\', 3, \'number\')" style="cursor:pointer;min-width:140px;">Regression 1→max<br><small>β (slope)</small> ⇅</th>\n')
    html_parts.append(f'<th class="effect-col" onclick="sortTable(\'{table_id}\', 4, \'number\')" style="cursor:pointer;min-width:140px;">Regression 2→max<br><small>β (slope)</small> ⇅</th>\n')
    html_parts.append(f'<th class="conform-col" onclick="sortTable(\'{table_id}\', 5, \'number\')" style="cursor:pointer;min-width:100px;">Decrease<br><small>ratio</small> ⇅</th>\n')
    col_idx = 6
    for n in range(1, max_n + 1):
        html_parts.append(f'<th class="mal-col" onclick="sortTable(\'{table_id}\', {col_idx}, \'number\')" style="cursor:pointer">MAL_{n}<br>(count) ⇅</th>\n')
        col_idx += 1
        if n < max_n:
            html_parts.append(f'<th class="score-col" onclick="sortTable(\'{table_id}\', {col_idx}, \'number\')" style="cursor:pointer">{n}→{n+1} ⇅</th>\n')
            col_idx += 1
    html_parts.append('</tr>\n</thead>\n<tbody>\n')
    
    # Table rows
    for lang, lang_name in lang_names_sorted:
        mal_data = lang2MAL_total[lang]
        count_data = lang2counts.get(lang, {})
        score_data = lang2local_scores.get(lang, {})
        group = group_by_lang.get(lang, 'Unknown')
        vo_score = lang_to_vo.get(lang) if lang_to_vo else None
        
        # Filter mal_data to only include values with sufficient counts for regression
        mal_data_filtered = {n: v for n, v in mal_data.items() 
                            if count_data.get(n, 0) >= min_count}
        
        html_parts.append(f'<tr>\n<td class="lang-name">{lang_name}</td>\n')
        
        # VO score column
        if vo_score is not None:
            # Color based on VO score: green for VO (>0.66), red for OV (<0.33), yellow for mixed
            if vo_score > 0.66:
                vo_css = "vo-cell vo-high"
            elif vo_score < 0.33:
                vo_css = "vo-cell vo-low"
            else:
                vo_css = "vo-cell vo-mid"
            html_parts.append(f'<td class="{vo_css}" data-value="{vo_score:.3f}">{vo_score:.2f}</td>\n')
        else:
            html_parts.append('<td class="na-cell" data-value="">—</td>\n')
        
        html_parts.append(f'<td class="group-cell">{group}</td>\n')
        
        # Generate log-log plots and get effect scores (using only filtered data with sufficient counts)
        # Plot 1: Regression from 1 to max
        svg1, effect1 = generate_loglog_svg(mal_data_filtered, start_n=1, width=120, height=50, lang_name=lang_name, lang_code=lang, mal_label=mal_label)
        # Plot 2: Regression from 2 to max
        svg2, effect2 = generate_loglog_svg(mal_data_filtered, start_n=2, width=120, height=50, lang_name=lang_name, lang_code=lang, mal_label=mal_label)
        
        # Effect score 1→max column with plot
        if effect1 is not None:
            if effect1 > 0.1:
                css_class = "effect-cell score-positive"
            elif effect1 < -0.1:
                css_class = "effect-cell score-negative"
            else:
                css_class = "effect-cell score-neutral"
            html_parts.append(f'<td class="{css_class}" data-value="{effect1:.6f}" style="vertical-align:middle;">{svg1}<br><strong>β= {effect1:.3f}</strong></td>\n')
        else:
            html_parts.append(f'<td class="na-cell" data-value="" style="vertical-align:middle;">{svg1}</td>\n')
        
        # Effect score 2→max column with plot
        if effect2 is not None:
            if effect2 > 0.1:
                css_class = "effect-cell score-positive"
            elif effect2 < -0.1:
                css_class = "effect-cell score-negative"
            else:
                css_class = "effect-cell score-neutral"
            html_parts.append(f'<td class="{css_class}" data-value="{effect2:.6f}" style="vertical-align:middle;">{svg2}<br><strong>β= {effect2:.3f}</strong></td>\n')
        else:
            html_parts.append(f'<td class="na-cell" data-value="" style="vertical-align:middle;">{svg2}</td>\n')
        
        # Decrease ratio column - proportion of consecutive pairs where MAL decreases
        decrease_ratio = compute_decrease_ratio(mal_data_filtered)
        if decrease_ratio is not None:
            # Higher ratio means more MAL-conformant (more consecutive decreases)
            if decrease_ratio >= 0.7:
                css_class = "conform-cell score-positive"
            elif decrease_ratio <= 0.3:
                css_class = "conform-cell score-negative"
            else:
                css_class = "conform-cell score-neutral"
            html_parts.append(f'<td class="{css_class}" data-value="{decrease_ratio:.6f}">{decrease_ratio:.2f}</td>\n')
        else:
            html_parts.append('<td class="na-cell" data-value="">—</td>\n')
        
        for n in range(1, max_n + 1):
            # MAL value and count
            if n in mal_data:
                mal_val = mal_data[n]
                count_val = count_data.get(n, 0)
                # Grey out cells with low counts (below min_count threshold)
                if count_val >= min_count:
                    html_parts.append(f'<td class="mal-cell" data-value="{mal_val:.6f}">{mal_val:.3f}<br>({count_val})</td>\n')
                else:
                    html_parts.append(f'<td class="mal-cell-lowcount" data-value="{mal_val:.6f}" title="Low count (n={count_val}, threshold={min_count})">{mal_val:.3f}<br>({count_val})</td>\n')
            else:
                html_parts.append('<td class="na-cell" data-value="">—</td>\n')
            
            # Local change score
            if n < max_n:
                score_key = f"{n}→{n+1}"
                if score_key in score_data and not np.isnan(score_data[score_key]):
                    score = score_data[score_key]
                    # Check if both n and n+1 have sufficient counts
                    count_n = count_data.get(n, 0)
                    count_n1 = count_data.get(n+1, 0)
                    is_lowcount = count_n < min_count or count_n1 < min_count
                    
                    if is_lowcount:
                        css_class = "score-cell-lowcount"
                    elif score > 0.1:
                        css_class = "score-cell score-positive"
                    elif score < -0.1:
                        css_class = "score-cell score-negative"
                    else:
                        css_class = "score-cell score-neutral"
                    html_parts.append(f'<td class="{css_class}" data-value="{score:.6f}">{score:.3f}</td>\n')
                else:
                    html_parts.append('<td class="na-cell" data-value="">—</td>\n')
        
        html_parts.append('</tr>\n')
    
    html_parts.append('</tbody>\n</table>\n')
    
    # Add sorting JavaScript only once (for the first table)
    if include_sort_script:
        html_parts.append('''
<script>
var sortDirections = {};

function sortTable(tableId, colIndex, type) {
    const table = document.getElementById(tableId);
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);
    
    // Use composite key for sort direction (tableId + colIndex)
    const sortKey = tableId + '_' + colIndex;
    sortDirections[sortKey] = !sortDirections[sortKey];
    const ascending = sortDirections[sortKey];
    
    rows.sort((a, b) => {
        let aVal, bVal;
        
        if (type === 'string') {
            aVal = a.cells[colIndex].textContent.trim().toLowerCase();
            bVal = b.cells[colIndex].textContent.trim().toLowerCase();
            return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
        } else {
            // Use data-value attribute for numeric sorting
            aVal = a.cells[colIndex].getAttribute('data-value');
            bVal = b.cells[colIndex].getAttribute('data-value');
            
            // Handle empty values (sort to end)
            if (aVal === '' || aVal === null) return 1;
            if (bVal === '' || bVal === null) return -1;
            
            aVal = parseFloat(aVal);
            bVal = parseFloat(bVal);
            
            return ascending ? aVal - bVal : bVal - aVal;
        }
    });
    
    // Re-append rows in new order
    rows.forEach(row => tbody.appendChild(row));
}
</script>
''');
    
    return ''.join(html_parts)


def _get_html_header(min_count):
    """Generate HTML header with styles and Chart.js."""
    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>MAL_n Analysis - Full Language Table</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; max-width: 1400px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #333; }}
h2 {{ color: #555; margin-top: 30px; }}
h3 {{ color: #666; margin-top: 20px; }}
.info-box {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
.info-box p {{ margin: 5px 0; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; font-size: 12px; }}
th {{ background-color: #4CAF50; color: white; position: sticky; top: 0; z-index: 10; }}
th.mal-col {{ background-color: #2196F3; }}
th.score-col {{ background-color: #FF9800; }}
th.effect-col {{ background-color: #9C27B0; }}
th.conform-col {{ background-color: #00BCD4; }}
th.group-col {{ background-color: #607D8B; }}
.effect-cell {{ font-weight: bold; }}
.conform-cell {{ font-weight: bold; }}
.group-cell {{ font-size: 11px; color: #555; white-space: nowrap; }}
tr:nth-child(even) {{ background-color: #f9f9f9; }}
tr:hover {{ background-color: #f1f1f1; }}
.lang-name {{ text-align: left; font-weight: bold; white-space: nowrap; }}
.mal-cell {{ background-color: #e3f2fd; }}
.mal-cell-lowcount {{ background-color: #f5f5f5; color: #999; font-style: italic; }}
.score-cell {{ font-weight: bold; }}
.score-cell-lowcount {{ color: #bbb; font-style: italic; }}
.score-positive {{ background-color: #c8e6c9; }}
.score-negative {{ background-color: #ffcdd2; }}
.score-neutral {{ background-color: #fff9c4; }}
.na-cell {{ color: #999; }}
.explanation {{ background: #fff3e0; padding: 15px; border-left: 4px solid #ff9800; margin: 20px 0; }}
.chart-container {{ margin: 30px 0; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
.chart-row {{ display: flex; flex-wrap: wrap; gap: 20px; }}
.chart-half {{ flex: 1; min-width: 400px; }}
canvas {{ max-width: 100%; }}

/* Log-Log Popup Modal */
.loglog-modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; }}
.loglog-modal-content {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 10px; max-width: 700px; width: 90%; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
.loglog-modal-close {{ position: absolute; top: 10px; right: 15px; font-size: 28px; cursor: pointer; color: #666; }}
.loglog-modal-close:hover {{ color: #000; }}
.loglog-modal-title {{ margin: 0 0 15px 0; color: #333; }}
.loglog-modal-stats {{ background: #f5f5f5; padding: 10px 15px; border-radius: 5px; margin-top: 15px; font-size: 14px; }}
.loglog-modal-stats span {{ margin-right: 20px; }}
.loglog-svg-plot {{ cursor: pointer; }}
.loglog-svg-plot:hover {{ opacity: 0.8; }}

/* VO Column */
th.vo-col {{ background-color: #795548; }}
.vo-cell {{ font-weight: bold; font-size: 11px; }}
.vo-high {{ background-color: #c8e6c9; }}
.vo-low {{ background-color: #ffcdd2; }}
.vo-mid {{ background-color: #fff9c4; }}

</style>
</head>
<body>

<!-- Log-Log Popup Modal -->
<div id="loglogModal" class="loglog-modal" onclick="if(event.target===this) closeLogLogModal();">
<div class="loglog-modal-content">
<span class="loglog-modal-close" onclick="closeLogLogModal()">&times;</span>
<h3 class="loglog-modal-title" id="loglogModalTitle">Log-Log Regression</h3>
<canvas id="loglogModalChart" width="600" height="400"></canvas>
<div class="loglog-modal-stats" id="loglogModalStats"></div>
</div>
</div>

<script>
let loglogChart = null;

function showLogLogPopup(jsonStr) {{
    // Decode HTML-escaped quotes
    const decodedStr = jsonStr.replace(/&quot;/g, '"');
    const data = JSON.parse(decodedStr);
    const modal = document.getElementById('loglogModal');
    const title = document.getElementById('loglogModalTitle');
    const stats = document.getElementById('loglogModalStats');
    const canvas = document.getElementById('loglogModalChart');
    
    // Set title
    const malLabel = data.mal_label || 'MAL';
    title.textContent = data.lang_name + ' — ' + malLabel + ' Log-Log Regression (n≥' + data.start_n + ')';
    
    // Prepare chart data
    const scatterData = data.points.map(p => ({{ x: p[0], y: p[1] }}));
    const regLineData = data.reg_line.map(p => ({{ x: p[0], y: p[1] }}));
    
    // Destroy existing chart
    if (loglogChart) {{
        loglogChart.destroy();
    }}
    
    // Create chart
    loglogChart = new Chart(canvas.getContext('2d'), {{
        type: 'scatter',
        data: {{
            datasets: [
                {{
                    label: 'Data points: log(n) vs log(' + malLabel + '_n)',
                    data: scatterData,
                    backgroundColor: 'rgba(33, 150, 243, 0.8)',
                    borderColor: 'rgba(33, 150, 243, 1)',
                    pointRadius: 8,
                    pointHoverRadius: 10
                }},
                {{
                    label: 'Regression line',
                    data: regLineData,
                    type: 'line',
                    borderColor: 'rgba(244, 67, 54, 1)',
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 0,
                    tension: 0
                }}
            ]
        }},
        options: {{
            responsive: true,
            plugins: {{
                legend: {{
                    display: true,
                    position: 'top'
                }},
                title: {{
                    display: false
                }}
            }},
            scales: {{
                x: {{
                    title: {{
                        display: true,
                        text: 'log(n) — Number of dependents',
                        font: {{ size: 14 }}
                    }}
                }},
                y: {{
                    title: {{
                        display: true,
                        text: 'log(' + malLabel + '_n) — Mean constituent size',
                        font: {{ size: 14 }}
                    }}
                }}
            }}
        }}
    }});
    
    // Set stats
    const beta = -data.slope;
    const betaColor = beta > 0.1 ? '#4CAF50' : (beta < -0.1 ? '#f44336' : '#ff9800');
    stats.innerHTML = '<span><strong>Equation:</strong> log(' + malLabel + '_n) = ' + data.intercept.toFixed(3) + ' + (' + data.slope.toFixed(3) + ') · log(n)</span>' +
        '<span><strong style="color:' + betaColor + '">β = ' + beta.toFixed(3) + '</strong></span>' +
        '<span><strong>R² = ' + data.r_squared.toFixed(3) + '</strong></span>' +
        '<span><strong>n range:</strong> ' + Math.min(...data.n_values) + '–' + Math.max(...data.n_values) + ' (' + data.n_values.length + ' points)</span>';
    
    // Show modal
    modal.style.display = 'block';
}}

function closeLogLogModal() {{
    document.getElementById('loglogModal').style.display = 'none';
}}

// Close on Escape key
document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') closeLogLogModal();
}});
</script>

<h1>MAL_n Analysis: Constituent Size by Number of Dependents</h1>

<div class="info-box" style="background: #e3f2fd; border-left: 4px solid #1976d2; padding: 15px; margin-bottom: 20px;">
<h3 style="margin-top: 0; color: #1976d2;">⚙️ Statistical Threshold: MIN_COUNT = {min_count}</h3>
<p>A configuration (specific n value) is only included in <strong>regression calculations and averages</strong> if it has at least <strong>{min_count} occurrences</strong>.</p>
<p>Configurations with fewer occurrences are shown in <span style="color: #999;">grey</span> for reference but are <strong>not used</strong> for computing slopes (β) or decrease ratios.</p>
</div>

<div class="info-box">
<p><strong>Data source:</strong> Bilateral dependency configurations from Universal Dependencies treebanks</p>
<p><strong>MAL_n:</strong> Arithmetic mean of constituent sizes for heads with n total dependents</p>
<p><strong>Count:</strong> Number of observations contributing to the MAL_n value</p>

<h4 style="margin-top:15px;">Log-Log Regression (β = MAL Effect Score)</h4>
<p>Each language has two inline plots showing log(n) vs log(MAL_n) with linear regression:</p>
<p><strong>Regression 1→max:</strong> Uses all available data points (n=1 to max) <em>where count ≥ {min_count}</em></p>
<p><strong>Regression 2→max:</strong> Excludes n=1 (starts from n=2 to max) <em>where count ≥ {min_count}</em></p>
<p><strong>β (slope):</strong> The negative of the log-log regression slope. Under MAL: log(MAL_n) = a - β·log(n)</p>
<p style="margin-left: 20px;">• <span style="background:#c8e6c9;padding:2px 6px;">β &gt; 0.1 (green)</span>: MAL compliance</p>
<p style="margin-left: 20px;">• <span style="background:#ffcdd2;padding:2px 6px;">β &lt; -0.1 (red)</span>: Anti-MAL</p>
<p style="margin-left: 20px;">• <span style="background:#fff9c4;padding:2px 6px;">|β| ≤ 0.1 (yellow)</span>: Weak effect</p>

<h4 style="margin-top:15px;">Decrease Ratio</h4>
<p><strong>Decrease Ratio:</strong> Proportion of consecutive pairs where MAL decreases (e.g., MAL_{{n+1}} &lt; MAL_n). A simple, regression-free measure.</p>
<p style="margin-left: 20px;">• <span style="background:#c8e6c9;padding:2px 6px;">Ratio ≥ 0.7 (green)</span>: Most transitions show decrease — MAL holds</p>
<p style="margin-left: 20px;">• <span style="background:#ffcdd2;padding:2px 6px;">Ratio ≤ 0.3 (red)</span>: Few transitions show decrease — Anti-MAL</p>
<p style="margin-left: 20px;">• <span style="background:#fff9c4;padding:2px 6px;">0.3 < Ratio < 0.7 (yellow)</span>: Mixed behavior</p>

<h4 style="margin-top:15px;">Local Change Scores (n→n+1)</h4>
<p><strong>Score:</strong> [ln(MAL_n) - ln(MAL_{{n+1}})] / [ln(n+1) - ln(n)]</p>
<p><em>Only computed between consecutive n values that both have count ≥ {min_count}</em></p>
</div>
'''


def _get_html_header_with_nav(min_count, has_directional=False):
    """Generate HTML header with styles, Chart.js, and optional navigation links."""
    nav_html = ""
    
    # VO column styles
    vo_styles = '''
th.vo-col {{ background-color: #795548; }}
.vo-cell {{ font-weight: bold; font-size: 11px; }}
.vo-high {{ background-color: #c8e6c9; }}  /* VO > 0.66 = green */
.vo-low {{ background-color: #ffcdd2; }}   /* OV < 0.33 = red */
.vo-mid {{ background-color: #fff9c4; }}   /* Mixed = yellow */
'''
    
    nav_style = ""
    if has_directional:
        nav_style = '''
.nav-links { position: sticky; top: 0; background: #333; padding: 10px; z-index: 100; margin: -20px -20px 20px -20px; }
.nav-links a { color: white; margin-right: 20px; text-decoration: none; }
.nav-links a:hover { text-decoration: underline; }
'''
    
    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>MAL_n Analysis - Full Language Table</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; max-width: 1400px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #333; }}
h2 {{ color: #555; margin-top: 30px; }}
h3 {{ color: #666; margin-top: 20px; }}
.info-box {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
.info-box p {{ margin: 5px 0; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; font-size: 12px; }}
th {{ background-color: #4CAF50; color: white; position: sticky; top: 0; z-index: 10; }}
th.mal-col {{ background-color: #2196F3; }}
th.score-col {{ background-color: #FF9800; }}
th.effect-col {{ background-color: #9C27B0; }}
th.conform-col {{ background-color: #00BCD4; }}
th.group-col {{ background-color: #607D8B; }}
.effect-cell {{ font-weight: bold; }}
.conform-cell {{ font-weight: bold; }}
.group-cell {{ font-size: 11px; color: #555; white-space: nowrap; }}
tr:nth-child(even) {{ background-color: #f9f9f9; }}
tr:hover {{ background-color: #f1f1f1; }}
.lang-name {{ text-align: left; font-weight: bold; white-space: nowrap; }}
.mal-cell {{ background-color: #e3f2fd; }}
.mal-cell-lowcount {{ background-color: #f5f5f5; color: #999; font-style: italic; }}
.score-cell {{ font-weight: bold; }}
.score-cell-lowcount {{ color: #bbb; font-style: italic; }}
.score-positive {{ background-color: #c8e6c9; }}
.score-negative {{ background-color: #ffcdd2; }}
.score-neutral {{ background-color: #fff9c4; }}
.na-cell {{ color: #999; }}
.explanation {{ background: #fff3e0; padding: 15px; border-left: 4px solid #ff9800; margin: 20px 0; }}
.chart-container {{ margin: 30px 0; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
.chart-row {{ display: flex; flex-wrap: wrap; gap: 20px; }}
.chart-half {{ flex: 1; min-width: 400px; }}
canvas {{ max-width: 100%; }}

/* Log-Log Popup Modal */
.loglog-modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 1000; }}
.loglog-modal-content {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 30px; border-radius: 10px; max-width: 700px; width: 90%; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }}
.loglog-modal-close {{ position: absolute; top: 10px; right: 15px; font-size: 28px; cursor: pointer; color: #666; }}
.loglog-modal-close:hover {{ color: #000; }}
.loglog-modal-title {{ margin: 0 0 15px 0; color: #333; }}
.loglog-modal-stats {{ background: #f5f5f5; padding: 10px 15px; border-radius: 5px; margin-top: 15px; font-size: 14px; }}
.loglog-modal-stats span {{ margin-right: 20px; }}
.loglog-svg-plot {{ cursor: pointer; }}
.loglog-svg-plot:hover {{ opacity: 0.8; }}

{vo_styles}{nav_style}
</style>
</head>
<body>

<!-- Log-Log Popup Modal -->
<div id="loglogModal" class="loglog-modal" onclick="if(event.target===this) closeLogLogModal();">
<div class="loglog-modal-content">
<span class="loglog-modal-close" onclick="closeLogLogModal()">&times;</span>
<h3 class="loglog-modal-title" id="loglogModalTitle">Log-Log Regression</h3>
<canvas id="loglogModalChart" width="600" height="400"></canvas>
<div class="loglog-modal-stats" id="loglogModalStats"></div>
</div>
</div>

<script>
let loglogChart = null;

function showLogLogPopup(jsonStr) {{
    // Decode HTML-escaped quotes
    const decodedStr = jsonStr.replace(/&quot;/g, '"');
    const data = JSON.parse(decodedStr);
    const modal = document.getElementById('loglogModal');
    const title = document.getElementById('loglogModalTitle');
    const stats = document.getElementById('loglogModalStats');
    const canvas = document.getElementById('loglogModalChart');
    
    // Set title
    const malLabel = data.mal_label || 'MAL';
    title.textContent = data.lang_name + ' — ' + malLabel + ' Log-Log Regression (n≥' + data.start_n + ')';
    
    // Prepare chart data
    const scatterData = data.points.map(p => ({{ x: p[0], y: p[1] }}));
    const regLineData = data.reg_line.map(p => ({{ x: p[0], y: p[1] }}));
    
    // Destroy existing chart
    if (loglogChart) {{
        loglogChart.destroy();
    }}
    
    // Create chart
    loglogChart = new Chart(canvas.getContext('2d'), {{
        type: 'scatter',
        data: {{
            datasets: [
                {{
                    label: 'Data points: log(n) vs log(' + malLabel + '_n)',
                    data: scatterData,
                    backgroundColor: 'rgba(33, 150, 243, 0.8)',
                    borderColor: 'rgba(33, 150, 243, 1)',
                    pointRadius: 8,
                    pointHoverRadius: 10
                }},
                {{
                    label: 'Regression line',
                    data: regLineData,
                    type: 'line',
                    borderColor: 'rgba(244, 67, 54, 1)',
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 0,
                    tension: 0
                }}
            ]
        }},
        options: {{
            responsive: true,
            plugins: {{
                legend: {{
                    display: true,
                    position: 'top'
                }},
                title: {{
                    display: false
                }}
            }},
            scales: {{
                x: {{
                    title: {{
                        display: true,
                        text: 'log(n) — Number of dependents',
                        font: {{ size: 14 }}
                    }}
                }},
                y: {{
                    title: {{
                        display: true,
                        text: 'log(' + malLabel + '_n) — Mean constituent size',
                        font: {{ size: 14 }}
                    }}
                }}
            }}
        }}
    }});
    
    // Set stats
    const beta = -data.slope;
    const betaColor = beta > 0.1 ? '#4CAF50' : (beta < -0.1 ? '#f44336' : '#ff9800');
    stats.innerHTML = '<span><strong>Equation:</strong> log(' + malLabel + '_n) = ' + data.intercept.toFixed(3) + ' + (' + data.slope.toFixed(3) + ') · log(n)</span>' +
        '<span><strong style="color:' + betaColor + '">β = ' + beta.toFixed(3) + '</strong></span>' +
        '<span><strong>R² = ' + data.r_squared.toFixed(3) + '</strong></span>' +
        '<span><strong>n range:</strong> ' + Math.min(...data.n_values) + '–' + Math.max(...data.n_values) + ' (' + data.n_values.length + ' points)</span>';
    
    // Show modal
    modal.style.display = 'block';
}}

function closeLogLogModal() {{
    document.getElementById('loglogModal').style.display = 'none';
}}

// Close on Escape key
document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') closeLogLogModal();
}});
</script>

{nav_html}
<h1>MAL_n Analysis: Constituent Size by Number of Dependents</h1>

<div class="info-box" style="background: #e3f2fd; border-left: 4px solid #1976d2; padding: 15px; margin-bottom: 20px;">
<h3 style="margin-top: 0; color: #1976d2;">⚙️ Statistical Threshold: MIN_COUNT = {min_count}</h3>
<p>A configuration (specific n value) is only included in <strong>regression calculations and averages</strong> if it has at least <strong>{min_count} occurrences</strong>.</p>
<p>Configurations with fewer occurrences are shown in <span style="color: #999;">grey</span> for reference but are <strong>not used</strong> for computing slopes (β) or decrease ratios.</p>
</div>

<div class="info-box">
<p><strong>Data source:</strong> Bilateral dependency configurations from Universal Dependencies treebanks</p>
<p><strong>MAL_n:</strong> Arithmetic mean of constituent sizes for heads with n total dependents</p>
<p><strong>Count:</strong> Number of observations contributing to the MAL_n value</p>

<h4 style="margin-top:15px;">Log-Log Regression (β = MAL Effect Score)</h4>
<p>Each language has two inline plots showing log(n) vs log(MAL_n) with linear regression:</p>
<p><strong>Regression 1→max:</strong> Uses all available data points (n=1 to max) <em>where count ≥ {min_count}</em></p>
<p><strong>Regression 2→max:</strong> Excludes n=1 (starts from n=2 to max) <em>where count ≥ {min_count}</em></p>
<p><strong>β (slope):</strong> The negative of the log-log regression slope. Under MAL: log(MAL_n) = a - β·log(n)</p>
<p style="margin-left: 20px;">• <span style="background:#c8e6c9;padding:2px 6px;">β &gt; 0.1 (green)</span>: MAL compliance</p>
<p style="margin-left: 20px;">• <span style="background:#ffcdd2;padding:2px 6px;">β &lt; -0.1 (red)</span>: Anti-MAL</p>
<p style="margin-left: 20px;">• <span style="background:#fff9c4;padding:2px 6px;">|β| ≤ 0.1 (yellow)</span>: Weak effect</p>

<h4 style="margin-top:15px;">Decrease Ratio</h4>
<p><strong>Decrease Ratio:</strong> Proportion of consecutive pairs where MAL decreases (e.g., MAL_{{n+1}} &lt; MAL_n). A simple, regression-free measure.</p>
<p style="margin-left: 20px;">• <span style="background:#c8e6c9;padding:2px 6px;">Ratio ≥ 0.7 (green)</span>: Most transitions show decrease — MAL holds</p>
<p style="margin-left: 20px;">• <span style="background:#ffcdd2;padding:2px 6px;">Ratio ≤ 0.3 (red)</span>: Few transitions show decrease — Anti-MAL</p>
<p style="margin-left: 20px;">• <span style="background:#fff9c4;padding:2px 6px;">0.3 < Ratio < 0.7 (yellow)</span>: Mixed behavior</p>

<h4 style="margin-top:15px;">Local Change Scores (n→n+1)</h4>
<p><strong>Score:</strong> [ln(MAL_n) - ln(MAL_{{n+1}})] / [ln(n+1) - ln(n)]</p>
<p><em>Only computed between consecutive n values that both have count ≥ {min_count}</em></p>
</div>
'''


def _get_table_explanation(min_count):
    """Generate table explanation section."""
    return f'''
<div class="explanation">
<h2>Understanding the Table</h2>
<p><strong>Log-Log Regression Plots:</strong> Each language has two inline plots showing the log-log relationship 
between n (number of dependents) and MAL_n (mean constituent size). The data points (blue circles) and regression 
line are shown. The slope β is displayed in each plot — this is the negative of the regression slope, so positive β 
indicates MAL compliance.</p>

<p><strong>Regression 1→max:</strong> Linear regression using all available data points from n=1 to the maximum n.</p>
<p><strong>Regression 2→max:</strong> Linear regression starting from n=2, which may give a more stable estimate 
by excluding the potentially atypical n=1 configuration.</p>

<p><strong>Decrease Ratio:</strong> The proportion of consecutive n values where MAL decreases (MAL_{{n+1}} &lt; MAL_n).
A value of 1.0 indicates perfect MAL compliance (all consecutive pairs show decrease).
A value of 0.0 indicates anti-MAL behavior (no consecutive pairs show decrease).
A value around 0.5 indicates mixed behavior. This is a simple, regression-free measure of local MAL compliance.</p>

<p><strong>MAL_n values (blue columns):</strong> These represent the arithmetic mean size of constituents 
(dependents) for verb heads with exactly n total dependents. Under the Menzerath-Altmann Law, we expect 
MAL_n to decrease as n increases — heads with more dependents should have shorter individual dependents.</p>

<p><strong>Local Change Scores (orange columns):</strong> These measure the "elasticity" of the MAL effect 
between consecutive n values. The formula normalizes the log-change in constituent size by the log-change 
in n, making scores comparable across different transitions.</p>

<p><strong>Color coding:</strong></p>
<ul>
<li><span style="background:#c8e6c9; padding: 2px 8px;">Green</span>: Strong MAL compliance — for β &gt; 0.1 or decrease ratio ≥ 0.7</li>
<li><span style="background:#fff9c4; padding: 2px 8px;">Yellow</span>: Weak effect — for |β| ≤ 0.1 or decrease ratio between 0.3 and 0.7</li>
<li><span style="background:#ffcdd2; padding: 2px 8px;">Red</span>: Anti-MAL — for β &lt; -0.1 or decrease ratio ≤ 0.3</li>
<li><span style="background:#f5f5f5; color:#999; padding: 2px 8px; font-style:italic;">Grey italic</span>: Low sample count — values with fewer than {min_count} occurrences are shown but excluded from regressions and statistics</li>
</ul>

<p><strong>Missing values (—):</strong> Indicate no data available for that language/n combination.</p>
</div>
'''


def _generate_slope_summary_table(lang2MAL_filtered, lang2local_scores, max_n=5):
    """
    Generate an HTML table counting languages per slope category.
    
    Columns: β(1→max), β(2→max), 1→2, 2→3, ..., (max_n-1)→max_n
    Rows: green (>0.1), yellow-high (0 to 0.1), yellow-low (-0.1 to 0), red (<-0.1), total
    """
    # Define columns
    columns = []
    # Regression slopes
    for start_n in [1, 2]:
        col_label = f"β({start_n}→max)"
        values = []
        for lang, mal_data in lang2MAL_filtered.items():
            reg = compute_loglog_regression(mal_data, start_n=start_n)
            if reg is not None:
                values.append(reg['slope'])
        columns.append((col_label, values))
    
    # Local change scores
    for n in range(1, max_n):
        col_label = f"{n}→{n+1}"
        values = []
        for lang, scores in lang2local_scores.items():
            key = f"{n}→{n+1}"
            if key in scores and not np.isnan(scores[key]):
                values.append(scores[key])
        columns.append((col_label, values))
    
    # Define row categories
    categories = [
        ("β > 0.1",   "#c8e6c9", lambda v: v > 0.1),
        ("0 < β ≤ 0.1", "#fff9c4", lambda v: 0 < v <= 0.1),
        ("-0.1 ≤ β ≤ 0", "#fff9c4", lambda v: -0.1 <= v <= 0),
        ("β < -0.1",  "#ffcdd2", lambda v: v < -0.1),
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
    html.append('<p><strong>Note:</strong> β(1→max) and β(2→max) are log-log regression slopes (negative = MAL compliance). ')
    html.append('Local change scores (1→2, 2→3, ...) are positive when MAL holds (constituent size decreases).</p>')
    html.append('</div>')
    html.append('</div>')
    
    return '\n'.join(html)


def _get_charts_section(viz_data, min_count, viz_data_left=None, viz_data_right=None):
    """Generate all charts using Chart.js and SVG."""
    
    chart_data_json = json.dumps(viz_data['chart_data'])
    normalized_curve_json = json.dumps(viz_data['normalized_curve'])
    language_curves_json = json.dumps(viz_data['language_curves'])
    data_availability_json = json.dumps(viz_data['data_availability'])
    beta_scatter_json = json.dumps(viz_data['beta_scatter'])
    effect_scores_json = json.dumps(viz_data['effect_scores'])
    family_stats_json = json.dumps(viz_data['family_stats'])
    geo_data_json = json.dumps(viz_data.get('geo_data', []))
    r2_distribution_json = json.dumps(viz_data.get('r2_distribution', []))
    family_transition_json = json.dumps(viz_data.get('family_transition_stats', {}))
    max_n = viz_data['max_n']
    
    # Generate combined LMAL/MAL/RMAL box plot if directional data is available
    if viz_data_left and viz_data_right:
        svg_combined_box_plot = _generate_svg_combined_box_plot(
            viz_data['box_plot_data'],
            viz_data_left.get('box_plot_data', {}),
            viz_data_right.get('box_plot_data', {}),
            max_transition=5
        )
        combined_chart_html = f'''
<!-- Chart 3b: Combined LMAL/MAL/RMAL Box Plot -->
<div class="chart-container">
<h3>2b. Comparing LMAL, MAL, and RMAL Effect by Transition</h3>
{svg_combined_box_plot}
<div class="explanation">
<p><strong>Interpretation:</strong> This chart compares local change scores for <strong>left-side dependents (LMAL)</strong>, 
<strong>total dependents (MAL)</strong>, and <strong>right-side dependents (RMAL)</strong> at each transition from n to n+1.</p>
<p><strong>Color coding:</strong> Blue = LMAL (left dependents), Purple = MAL (total), Orange = RMAL (right dependents).</p>
<p><strong>Key insight:</strong> Differences between LMAL and RMAL may reveal asymmetric processing constraints. 
If RMAL shows stronger effects, it might suggest different planning for post-verbal material.</p>
<p><strong>Note:</strong> Only transitions up to 5→6 are shown, as higher n values have fewer languages with sufficient data.</p>
</div>
</div>
'''
    else:
        combined_chart_html = ''
    
    # Generate SVG effect by family chart
    svg_effect_by_family = _generate_svg_effect_by_family(viz_data['family_stats'], viz_data['effect_scores'])
    
    # Generate SVG world map
    svg_world_map = _generate_svg_world_map(viz_data.get('geo_data', []))
    
    # Generate SVG family × transition heatmap
    svg_family_transition_heatmap = _generate_svg_family_transition_heatmap(viz_data.get('family_transition_stats', {}))
    
    return f'''
<h2>Visualizations</h2>

<!-- Chart 1: Normalized Constituent Size (log-log, normalized by MAL_2, up to n=5) -->
<div class="chart-container">
<h3>1. Normalized MAL Curve in Log-Log Space (MAL_n / MAL_2)</h3>
<canvas id="normalizedCurveChart" height="100"></canvas>
<div class="explanation">
<p><strong>Interpretation:</strong> This chart shows the relative change in constituent size in log-log space, 
normalized by each language's MAL_2 value. This allows direct comparison of the <em>rate of decline</em> across 
languages, independent of their initial constituent sizes.</p>
<p><strong>Key insight:</strong> All languages start at 1.0 for n=2; the steeper the decline, the stronger the MAL effect.
Only data up to n=5 is shown, as higher n values have insufficient language coverage.</p>
</div>
</div>

<!-- Chart 2: Data Availability -->
<div class="chart-container">
<h3>2. Data Availability by Number of Dependents</h3>
<canvas id="availabilityChart" height="80"></canvas>
<div class="explanation">
<p><strong>Interpretation:</strong> This chart shows how many languages have sufficient data (≥{min_count} occurrences) 
at each value of n (up to n=5). The number above each bar indicates the language count.</p>
</div>
</div>

{combined_chart_html}

<!-- Chart 3: Individual Language Trajectories -->
<div class="chart-container">
<h3>3. Individual Language MAL_n Trajectories</h3>
<canvas id="trajectoriesChart" height="120"></canvas>
<div class="explanation">
<p><strong>Interpretation:</strong> Each line represents one language's MAL_n trajectory. 
The thick black line shows the cross-linguistic mean. Most languages show a downward trend (MAL compliance), 
but there is considerable variation in both the starting point (MAL_1) and the slope of decline.</p>
<p><strong>Interactive:</strong> Hover over lines to see language names.</p>
</div>
</div>

<!-- Chart 4: Histogram of Local Change Scores -->
<div class="chart-container">
<h3>4. Histogram of All Local Change Scores</h3>
<canvas id="histogramChart" height="80"></canvas>
<div class="explanation">
<p><strong>Interpretation:</strong> This histogram shows the overall distribution of local change scores 
across all languages and transitions. A distribution centered above zero indicates general MAL compliance.
The spread shows how consistent the MAL effect is across the dataset.</p>
</div>
</div>

<!-- Chart 5: β(2→max) vs β(1→2) Scatter Plot -->
<div class="chart-container">
<h3>5. β(2→max) vs. β(1→2) — Regression Slope vs. Initial Transition</h3>
<canvas id="betaScatterChart" height="120"></canvas>
<div class="explanation">
<p><strong>Interpretation:</strong> Each point represents one language. The x-axis shows β(1→2) — the local change 
score for the first transition (n=1 to n=2). The y-axis shows β(2→max) — the log-log regression slope 
from n=2 onward, capturing the overall rate of decline.</p>
<p><strong>Key insight:</strong> A correlation between these two measures would suggest that languages with a strong 
initial MAL effect also maintain a steep decline for higher n. A lack of correlation might indicate that the 
initial transition is governed by different factors than the subsequent ones.</p>
<p><strong>Color coding:</strong> Points are colored by language family. Hover for details.</p>
</div>
</div>

<!-- Chart 6: MAL Effect Score by Family -->
<div class="chart-container">
<h3>6. MAL Effect β(1→max) by Language Family</h3>
{svg_effect_by_family}
<div class="explanation">
<p><strong>Interpretation:</strong> The MAL effect β(1→max) is the slope of the log-log regression of MAL_n on n, 
starting from n=1. Negative values indicate MAL compliance (constituent size decreases with n); 
positive values indicate anti-MAL behavior.</p>
<p><strong>Family comparison:</strong> This chart groups languages by family to reveal whether MAL strength 
varies systematically across genealogical groups. Box plots show the distribution within each family.</p>
<p><strong>Key insight:</strong> If MAL is a universal constraint, we expect negative slopes across all families.
Systematic differences might indicate structural factors that modulate MAL strength.</p>
</div>
</div>

<!-- Chart 7: World Map of MAL Effect -->
<div class="chart-container">
<h3>7. World Map: Geographic Distribution of MAL Effect β(1→max)</h3>
{svg_world_map}
<div class="explanation">
<p><strong>Interpretation:</strong> Each dot represents a language positioned at its geographic location. 
The color indicates the MAL effect β(1→max) — the log-log regression slope from n=1.</p>
<p><strong>Color scale:</strong> Green = strong MAL compliance (negative slope, constituent size decreases with n), 
Yellow = weak/neutral effect, Red = anti-MAL (positive slope, constituent size increases with n).</p>
<p><strong>Geographic patterns:</strong> If MAL is truly universal, we expect green dots distributed across 
all continents. Clustering of colors might suggest areal effects or shared structural features.</p>
<p><strong>Note:</strong> Only languages with geographic coordinates available in WALS are shown.</p>
</div>
</div>

<!-- Chart 8: R² Goodness-of-Fit Distribution -->
<div class="chart-container">
<h3>8. R² Goodness-of-Fit Distribution for β(1→max) Regressions</h3>
<canvas id="r2DistributionChart" height="80"></canvas>
<div class="explanation">
<p><strong>Interpretation:</strong> This histogram shows the distribution of R² values from the log-log regressions 
that produce each language's β(1→max) slope. R² measures how well a straight line in log-log space fits 
a language's MAL_n trajectory — in other words, how closely the relationship between log(n) and log(MAL_n) 
follows the power-law form predicted by Menzerath-Altmann's Law.</p>
<p><strong>Note on color:</strong> The blue shading here indicates <em>regression fit quality</em>, not MAL compliance direction. 
Darker blue = better fit (higher R²), lighter blue = poorer fit (lower R²). 
This is deliberately distinct from the green/red color scheme used in Charts 6–7, which encodes the <em>sign</em> of β.</p>
<p><strong>High R² (close to 1.0):</strong> The log-log regression captures nearly all the variance in the data, 
meaning the MAL_n values follow a regular power-law decay. This indicates that the Menzerath-Altmann relationship 
is well-described by a single regression slope β for that language.</p>
<p><strong>Low R² (close to 0):</strong> The log-log regression is a poor fit, suggesting that the language's 
MAL_n trajectory does not follow a simple power-law pattern. This could indicate non-monotonic behavior, 
structural noise, or insufficient data at certain n values.</p>
<p><strong>Key insight:</strong> If most languages cluster at high R² values, it supports the universality 
of the power-law form of MAL. A bimodal or dispersed distribution would suggest that MAL operates differently 
across language types, and that the single-slope summary β may be misleading for some languages.</p>
<p><strong>Threshold line:</strong> The dashed vertical line at R²=0.90 marks a conventional threshold for 
a "good" fit. Languages above this threshold have highly predictable MAL trajectories.</p>
</div>
</div>

<!-- Chart 9: Family × Transition Heatmap -->
<div class="chart-container">
<h3>9. Negated Mean Local Change Scores by Language Family × Transition</h3>
{svg_family_transition_heatmap}
<div class="explanation">
<p><strong>Interpretation:</strong> This heatmap shows the <em>negated</em> mean local change score for each combination of 
language family (rows) and transition (columns: 1→2, 2→3, 3→4, 4→5). The original local change score at transition 
n→n+1 is (MAL_n − MAL_{'{'}n+1{'}'}) / MAL_n; here it is negated so that <strong>negative values = MAL compliance</strong>, 
consistent with the β slope convention used throughout this report.</p>
<p><strong>Color coding:</strong> Green cells indicate negative values (MAL-compliant: constituent 
size decreases with more dependents), red cells indicate positive values (anti-MAL: size increases), 
and white/near-white cells indicate near-zero change. This matches the green/red convention 
of Charts 6 and 7 where negative β = MAL compliance.</p>
<p><strong>Key insight:</strong> This chart reveals whether the MAL effect is uniform across all transitions 
within a family, or whether certain transitions are more "critical" than others. For instance, if the 
1→2 transition consistently shows the most negative values across families, this would suggest that 
the compression of constituents is most pronounced when going from one to two dependents.</p>
<p><strong>Family variation:</strong> Rows are sorted by the overall mean (most negative = strongest MAL compliance at top). 
Families at the top show the strongest MAL compliance across transitions, while those at the bottom may show weaker or 
anti-MAL patterns. Large differences between columns within a row indicate that MAL strength is 
transition-dependent for that family.</p>
<p><strong>Cell annotations:</strong> Each cell shows the mean score and the number of languages (n=...) 
contributing to that mean. Cells with very few languages should be interpreted with caution.</p>
</div>
</div>

<script>
// Data from Python
const chartData = {chart_data_json};
const normalizedCurve = {normalized_curve_json};
const languageCurves = {language_curves_json};
const dataAvailability = {data_availability_json};
const betaScatter = {beta_scatter_json};
const effectScores = {effect_scores_json};
const familyStats = {family_stats_json};
const geoData = {geo_data_json};
const r2Distribution = {r2_distribution_json};
const familyTransition = {family_transition_json};
const maxN = {max_n};

// Color palette
const colors = {{
    primary: 'rgba(33, 150, 243, 1)',
    primaryLight: 'rgba(33, 150, 243, 0.2)',
    positive: 'rgba(76, 175, 80, 0.7)',
    negative: 'rgba(244, 67, 54, 0.7)',
    neutral: 'rgba(255, 193, 7, 0.7)',
    gray: 'rgba(158, 158, 158, 0.5)'
}};

// Chart 1: Normalized MAL Curve in Log-Log space (MAL_n / MAL_2, up to n=5)
// Filter normalized curve to n=2..5
const normEntries = Object.entries(normalizedCurve).filter(([n, d]) => parseInt(n) <= 5);
const normLabels = normEntries.map(([n, d]) => 'n=' + n);
const normMeanValues = normEntries.map(([n, d]) => Math.log(d.mean));
const normQ1Values = normEntries.map(([n, d]) => Math.log(d.q1));
const normQ3Values = normEntries.map(([n, d]) => Math.log(d.q3));
const normLogN = normEntries.map(([n, d]) => Math.log(parseInt(n)));

new Chart(document.getElementById('normalizedCurveChart'), {{
    type: 'scatter',
    data: {{
        datasets: [
            {{
                label: 'Mean log(MAL_n / MAL_2)',
                data: normLogN.map((x, i) => ({{ x: x, y: normMeanValues[i] }})),
                borderColor: 'rgba(156, 39, 176, 1)',
                backgroundColor: 'rgba(156, 39, 176, 1)',
                borderWidth: 3,
                showLine: true,
                fill: false,
                tension: 0.1,
                pointRadius: 5
            }},
            {{
                label: 'Q3 (75th percentile)',
                data: normLogN.map((x, i) => ({{ x: x, y: normQ3Values[i] }})),
                borderColor: 'rgba(156, 39, 176, 0.3)',
                backgroundColor: 'rgba(156, 39, 176, 0.2)',
                borderWidth: 1,
                showLine: true,
                fill: '+1',
                tension: 0.1,
                pointRadius: 0
            }},
            {{
                label: 'Q1 (25th percentile)',
                data: normLogN.map((x, i) => ({{ x: x, y: normQ1Values[i] }})),
                borderColor: 'rgba(156, 39, 176, 0.3)',
                backgroundColor: 'transparent',
                borderWidth: 1,
                showLine: true,
                fill: false,
                tension: 0.1,
                pointRadius: 0
            }}
        ]
    }},
    options: {{
        responsive: true,
        plugins: {{
            title: {{ display: false }},
            legend: {{ position: 'top' }},
            tooltip: {{
                callbacks: {{
                    label: function(context) {{
                        const n = Math.round(Math.exp(context.parsed.x));
                        const ratio = Math.exp(context.parsed.y).toFixed(3);
                        return context.dataset.label + ': n=' + n + ', MAL_n/MAL_2=' + ratio;
                    }}
                }}
            }}
        }},
        scales: {{
            y: {{
                title: {{ display: true, text: 'log(MAL_n / MAL_2)' }},
                beginAtZero: false
            }},
            x: {{
                title: {{ display: true, text: 'log(n)' }},
                ticks: {{
                    callback: function(value) {{
                        return 'n=' + Math.round(Math.exp(value));
                    }}
                }}
            }}
        }}
    }}
}});

// Chart 2: Data Availability (up to n=5)
const availEntries = Object.entries(dataAvailability).filter(([n]) => parseInt(n) <= 5);
const availLabels = availEntries.map(([n]) => 'n=' + n);
const availValues = availEntries.map(([, c]) => c);

new Chart(document.getElementById('availabilityChart'), {{
    type: 'bar',
    data: {{
        labels: availLabels,
        datasets: [{{
            label: 'Number of Languages',
            data: availValues,
            backgroundColor: colors.primary,
            borderColor: colors.primary,
            borderWidth: 1
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{
            legend: {{ display: false }},
            datalabels: {{
                anchor: 'end',
                align: 'top',
                formatter: (value) => value,
                font: {{ weight: 'bold' }}
            }}
        }},
        scales: {{
            y: {{
                title: {{ display: true, text: 'Number of Languages (with \u2265{min_count} occurrences)' }},
                beginAtZero: true
            }},
            x: {{
                title: {{ display: true, text: 'Number of Dependents (n)' }}
            }}
        }}
    }},
    plugins: [{{
        // Inline plugin to show values on top of bars
        afterDatasetsDraw(chart) {{
            const ctx = chart.ctx;
            chart.data.datasets.forEach((dataset, i) => {{
                const meta = chart.getDatasetMeta(i);
                meta.data.forEach((bar, index) => {{
                    const value = dataset.data[index];
                    ctx.fillStyle = '#333';
                    ctx.font = 'bold 12px sans-serif';
                    ctx.textAlign = 'center';
                    ctx.fillText(value, bar.x, bar.y - 5);
                }});
            }});
        }}
    }}]
}});

// Chart 3: Individual Language Trajectories (up to n=5)
const maxNtraj = Math.min(maxN, 5);
const trajDatasets = [];

// Compute mean values for n=1..maxNtraj
const meanValuesForTraj = [];
for (let n = 1; n <= maxNtraj; n++) {{
    const vals = languageCurves
        .map(lang => lang.values[n])
        .filter(v => v !== undefined && v !== null);
    meanValuesForTraj.push(vals.length > 0 ? vals.reduce((a, b) => a + b, 0) / vals.length : null);
}}

// Add individual language lines (semi-transparent)
languageCurves.forEach((lang, i) => {{
    const values = [];
    for (let n = 1; n <= maxNtraj; n++) {{
        values.push(lang.values[n] !== undefined ? lang.values[n] : null);
    }}
    trajDatasets.push({{
        label: lang.name,
        data: values,
        borderColor: 'rgba(100, 100, 100, 0.15)',
        backgroundColor: 'transparent',
        borderWidth: 1,
        fill: false,
        tension: 0.1,
        pointRadius: 0,
        hidden: false
    }});
}});

// Add mean line (prominent)
trajDatasets.push({{
    label: 'Cross-linguistic Mean',
    data: meanValuesForTraj,
    borderColor: 'black',
    backgroundColor: 'black',
    borderWidth: 3,
    fill: false,
    tension: 0.1,
    pointRadius: 4
}});

new Chart(document.getElementById('trajectoriesChart'), {{
    type: 'line',
    data: {{
        labels: Array.from({{length: maxNtraj}}, (_, i) => 'n=' + (i + 1)),
        datasets: trajDatasets
    }},
    options: {{
        responsive: true,
        plugins: {{
            legend: {{ 
                display: true,
                labels: {{
                    filter: (item) => item.text === 'Cross-linguistic Mean'
                }}
            }},
            tooltip: {{
                mode: 'nearest',
                intersect: true
            }}
        }},
        scales: {{
            y: {{
                title: {{ display: true, text: 'MAL_n (Constituent Size)' }},
                beginAtZero: false
            }},
            x: {{
                title: {{ display: true, text: 'Number of Dependents (n)' }}
            }}
        }},
        interaction: {{
            mode: 'nearest',
            axis: 'x',
            intersect: false
        }}
    }}
}});

// Chart 4: Histogram of All Scores
const allScores = Object.values(chartData).flat();
const binWidth = 0.2;
const minBin = Math.floor(Math.min(...allScores) / binWidth) * binWidth;
const maxBin = Math.ceil(Math.max(...allScores) / binWidth) * binWidth;
const bins = [];
const binLabels = [];

for (let b = minBin; b < maxBin; b += binWidth) {{
    const count = allScores.filter(s => s >= b && s < b + binWidth).length;
    bins.push(count);
    binLabels.push(b.toFixed(1));
}}

new Chart(document.getElementById('histogramChart'), {{
    type: 'bar',
    data: {{
        labels: binLabels,
        datasets: [{{
            label: 'Frequency',
            data: bins,
            backgroundColor: binLabels.map(b => {{
                const v = parseFloat(b);
                if (v >= 0.1) return colors.positive;
                if (v <= -0.1) return colors.negative;
                return colors.neutral;
            }}),
            borderColor: 'rgba(0,0,0,0.3)',
            borderWidth: 1
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{
            legend: {{ display: false }}
        }},
        scales: {{
            y: {{
                type: 'logarithmic',
                title: {{ display: true, text: 'Frequency (log scale)' }},
                beginAtZero: false,
                ticks: {{
                    callback: function(value) {{
                        if (Number.isInteger(Math.log10(value))) return value;
                        return null;
                    }}
                }}
            }},
            x: {{
                title: {{ display: true, text: 'Local Change Score' }}
            }}
        }}
    }}
}});

// Chart 5: β(2→max) vs β(1→2) Scatter Plot
const families = [...new Set(betaScatter.map(d => d.group))].sort();
const familyColors = {{}};
const colorPalette = [
    'rgba(33, 150, 243, 0.7)',   // Blue
    'rgba(76, 175, 80, 0.7)',    // Green
    'rgba(244, 67, 54, 0.7)',    // Red
    'rgba(156, 39, 176, 0.7)',   // Purple
    'rgba(255, 152, 0, 0.7)',    // Orange
    'rgba(0, 188, 212, 0.7)',    // Cyan
    'rgba(233, 30, 99, 0.7)',    // Pink
    'rgba(139, 195, 74, 0.7)',   // Light Green
    'rgba(121, 85, 72, 0.7)',    // Brown
    'rgba(63, 81, 181, 0.7)',    // Indigo
    'rgba(255, 87, 34, 0.7)',    // Deep Orange
    'rgba(0, 150, 136, 0.7)',    // Teal
    'rgba(158, 158, 158, 0.7)'   // Gray for "Other"
];
families.forEach((family, i) => {{
    familyColors[family] = colorPalette[i % colorPalette.length];
}});

// Group data by family for the scatter plot
const scatterDatasets = families.map(family => {{
    const points = betaScatter.filter(d => d.group === family);
    return {{
        label: family,
        data: points.map(d => ({{
            x: d.beta_1_2,
            y: d.beta_2max,
            name: d.name,
            r2: d.r_squared
        }})),
        backgroundColor: familyColors[family],
        borderColor: familyColors[family].replace('0.7', '1'),
        pointRadius: 6,
        pointHoverRadius: 8
    }};
}});

// Compute linear regression for trendline
const xVals = betaScatter.map(d => d.beta_1_2);
const yVals = betaScatter.map(d => d.beta_2max);
const nPts = xVals.length;
const sumX = xVals.reduce((a, b) => a + b, 0);
const sumY = yVals.reduce((a, b) => a + b, 0);
const sumXY = xVals.reduce((total, x, i) => total + x * yVals[i], 0);
const sumX2 = xVals.reduce((total, x) => total + x * x, 0);
const sumY2 = yVals.reduce((total, y) => total + y * y, 0);

const regSlope = (nPts * sumXY - sumX * sumY) / (nPts * sumX2 - sumX * sumX);
const regIntercept = (sumY - regSlope * sumX) / nPts;
const correlation = (nPts * sumXY - sumX * sumY) / 
    Math.sqrt((nPts * sumX2 - sumX * sumX) * (nPts * sumY2 - sumY * sumY));

const minX = Math.min(...xVals);
const maxX = Math.max(...xVals);
const trendlineData = [
    {{ x: minX, y: regSlope * minX + regIntercept }},
    {{ x: maxX, y: regSlope * maxX + regIntercept }}
];

scatterDatasets.push({{
    label: 'Trendline (r=' + correlation.toFixed(3) + ')',
    data: trendlineData,
    type: 'line',
    borderColor: 'rgba(0, 0, 0, 0.7)',
    borderWidth: 2,
    borderDash: [5, 5],
    pointRadius: 0,
    fill: false,
    order: 0
}});

new Chart(document.getElementById('betaScatterChart'), {{
    type: 'scatter',
    data: {{
        datasets: scatterDatasets
    }},
    options: {{
        responsive: true,
        plugins: {{
            legend: {{
                display: true,
                position: 'right',
                labels: {{
                    usePointStyle: true,
                    padding: 10
                }}
            }},
            tooltip: {{
                callbacks: {{
                    label: function(context) {{
                        const point = context.raw;
                        if (point.name) {{
                            return [
                                point.name,
                                '\u03b2(1\u21922): ' + point.x.toFixed(3),
                                '\u03b2(2\u2192max): ' + point.y.toFixed(3),
                                'R\u00b2: ' + point.r2.toFixed(3)
                            ];
                        }}
                        return 'Trendline: y = ' + regSlope.toFixed(4) + 'x + ' + regIntercept.toFixed(4);
                    }}
                }}
            }}
        }},
        scales: {{
            x: {{
                title: {{ display: true, text: '\u03b2(1\u21922) \u2014 Local Change Score (n=1 to n=2)' }},
                grid: {{
                    color: function(context) {{
                        if (context.tick.value === 0) return 'rgba(0, 0, 0, 0.5)';
                        return 'rgba(0, 0, 0, 0.1)';
                    }},
                    lineWidth: function(context) {{
                        if (context.tick.value === 0) return 2;
                        return 1;
                    }}
                }}
            }},
            y: {{
                title: {{ display: true, text: '\u03b2(2\u2192max) \u2014 Log-Log Regression Slope' }},
                grid: {{
                    color: function(context) {{
                        if (context.tick.value === 0) return 'rgba(0, 0, 0, 0.5)';
                        return 'rgba(0, 0, 0, 0.1)';
                    }},
                    lineWidth: function(context) {{
                        if (context.tick.value === 0) return 2;
                        return 1;
                    }}
                }}
            }}
        }}
    }}
}});

// Add correlation annotation
const betaChart = Chart.getChart('betaScatterChart');
if (betaChart) {{
    const canvas = document.getElementById('betaScatterChart');
    const annotationDiv = document.createElement('div');
    annotationDiv.style.cssText = 'position: relative; top: -80px; left: 70px; font-size: 14px; font-weight: bold; background: rgba(255,255,255,0.8); padding: 4px 8px; border-radius: 4px; display: inline-block;';
    annotationDiv.innerHTML = 'r = ' + correlation.toFixed(3) + ' | y = ' + regSlope.toFixed(3) + 'x + ' + regIntercept.toFixed(3);
    canvas.parentNode.insertBefore(annotationDiv, canvas.nextSibling);
}}

// Chart 8: R² Goodness-of-Fit Distribution
if (document.getElementById('r2DistributionChart') && r2Distribution.length > 0) {{
    const r2Values = r2Distribution.map(d => d.r_squared);
    
    // Create histogram bins: 0.0-0.1, 0.1-0.2, ..., 0.9-1.0
    const numBins = 20;
    const binWidth = 1.0 / numBins;
    const bins = Array(numBins).fill(0);
    const binLabels = [];
    for (let i = 0; i < numBins; i++) {{
        const lo = (i * binWidth).toFixed(2);
        const hi = ((i + 1) * binWidth).toFixed(2);
        binLabels.push(lo + '-' + hi);
    }}
    r2Values.forEach(v => {{
        let idx = Math.floor(v / binWidth);
        if (idx >= numBins) idx = numBins - 1;
        bins[idx]++;
    }});
    
    // Color bins by R² quality: dark blue (excellent) to light blue (poor)
    const binColors = bins.map((_, i) => {{
        const midpoint = (i + 0.5) * binWidth;
        if (midpoint >= 0.9) return 'rgba(13, 71, 161, 0.85)';
        if (midpoint >= 0.7) return 'rgba(30, 136, 229, 0.8)';
        if (midpoint >= 0.5) return 'rgba(100, 181, 246, 0.75)';
        return 'rgba(187, 222, 251, 0.7)';
    }});
    
    const r2Ctx = document.getElementById('r2DistributionChart').getContext('2d');
    new Chart(r2Ctx, {{
        type: 'bar',
        data: {{
            labels: binLabels,
            datasets: [{{
                label: 'Number of languages',
                data: bins,
                backgroundColor: binColors,
                borderColor: binColors.map(c => c.replace('0.8', '1.0')),
                borderWidth: 1
            }}]
        }},
        options: {{
            responsive: true,
            plugins: {{
                title: {{ display: false }},
                legend: {{ display: false }},
                annotation: {{
                    annotations: {{
                        thresholdLine: {{
                            type: 'line',
                            xMin: 18,
                            xMax: 18,
                            borderColor: 'rgba(0, 0, 0, 0.6)',
                            borderWidth: 2,
                            borderDash: [6, 4],
                            label: {{
                                display: true,
                                content: 'R²=0.90',
                                position: 'start',
                                backgroundColor: 'rgba(255,255,255,0.8)',
                                color: '#333',
                                font: {{ size: 11 }}
                            }}
                        }}
                    }}
                }}
            }},
            scales: {{
                x: {{
                    title: {{ display: true, text: 'R² value' }},
                    ticks: {{
                        maxRotation: 45,
                        callback: function(value, index) {{
                            // Show every other label to avoid crowding
                            return index % 2 === 0 ? this.getLabelForValue(value) : '';
                        }}
                    }}
                }},
                y: {{
                    title: {{ display: true, text: 'Number of languages' }},
                    beginAtZero: true,
                    ticks: {{ stepSize: 1 }}
                }}
            }}
        }}
    }});
    
    // Add summary stats below chart
    const meanR2 = (r2Values.reduce((a, b) => a + b, 0) / r2Values.length).toFixed(3);
    const medianR2 = r2Values.sort((a, b) => a - b)[Math.floor(r2Values.length / 2)].toFixed(3);
    const aboveThreshold = r2Values.filter(v => v >= 0.9).length;
    const pctAbove = ((aboveThreshold / r2Values.length) * 100).toFixed(1);
    
    const r2Canvas = document.getElementById('r2DistributionChart');
    const r2StatsDiv = document.createElement('div');
    r2StatsDiv.style.cssText = 'margin-top: 8px; padding: 8px 12px; background: #f5f5f5; border-radius: 4px; font-size: 13px;';
    r2StatsDiv.innerHTML = '<strong>Summary:</strong> n=' + r2Values.length + ' languages | Mean R²=' + meanR2 + ' | Median R²=' + medianR2 + ' | ' + aboveThreshold + ' languages (' + pctAbove + '%) with R²≥0.90';
    r2Canvas.parentNode.insertBefore(r2StatsDiv, r2Canvas.nextSibling);
}}

</script>
'''


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


def _generate_svg_effect_by_family(family_stats, effect_scores):
    """Generate an SVG chart showing MAL effect scores by language family."""
    
    
    if not family_stats or not effect_scores:
        return "<p>No effect data available.</p>"
    
    # Sort families by mean β (ascending = most negative/strongest MAL first)
    sorted_families = sorted(family_stats.items(), key=lambda x: x[1]['mean'])
    
    # Filter to families with at least 2 languages
    sorted_families = [(f, s) for f, s in sorted_families if s['count'] >= 2]
    
    if not sorted_families:
        return "<p>Not enough data for family comparison.</p>"
    
    # SVG dimensions
    width = 900
    height = max(400, len(sorted_families) * 35 + 100)
    margin_left = 180
    margin_right = 50
    margin_top = 40
    margin_bottom = 60
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    
    # Y range is -0.5 to 0.5 for effect scores
    x_min, x_max = -0.4, 0.4
    def scale_x(val):
        return margin_left + (val - x_min) / (x_max - x_min) * plot_width
    
    bar_height = min(25, (plot_height / len(sorted_families)) * 0.7)
    bar_spacing = plot_height / len(sorted_families)
    
    # Get individual scores by family for jittered points
    family_scores = {}
    for item in effect_scores:
        family = item['group']
        if family not in family_scores:
            family_scores[family] = []
        family_scores[family].append({
            'name': item['name'],
            'effect': item['effect']
        })
    
    svg_parts = []
    svg_parts.append(f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg" style="background: white; font-family: Arial, sans-serif;">')
    
    # Title
    svg_parts.append(f'<text x="{width/2}" y="25" text-anchor="middle" font-size="14" font-weight="bold">MAL Effect β(1→max) by Language Family</text>')
    
    # X-axis
    svg_parts.append(f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}" stroke="#333" stroke-width="1"/>')
    
    # X-axis ticks and labels (from -0.4 to 0.4)
    for i in range(-4, 5):
        x_val = i / 10
        x_pos = scale_x(x_val)
        svg_parts.append(f'<line x1="{x_pos}" y1="{margin_top + plot_height}" x2="{x_pos}" y2="{margin_top + plot_height + 5}" stroke="#333" stroke-width="1"/>')
        svg_parts.append(f'<text x="{x_pos}" y="{margin_top + plot_height + 20}" text-anchor="middle" font-size="10">{x_val:.1f}</text>')
        # Grid lines
        svg_parts.append(f'<line x1="{x_pos}" y1="{margin_top}" x2="{x_pos}" y2="{margin_top + plot_height}" stroke="#eee" stroke-width="1"/>')
    
    # X-axis label
    svg_parts.append(f'<text x="{margin_left + plot_width/2}" y="{height - 15}" text-anchor="middle" font-size="12">β(1→max) — Log-Log Regression Slope</text>')
    
    # Color palette for families
    color_palette = [
        '#2196F3', '#4CAF50', '#F44336', '#9C27B0', '#FF9800',
        '#00BCD4', '#E91E63', '#8BC34A', '#795548', '#3F51B5',
        '#FF5722', '#009688', '#673AB7', '#CDDC39', '#607D8B'
    ]
    
    # Draw bars and points for each family
    for i, (family, stats) in enumerate(sorted_families):
        y_center = margin_top + (i + 0.5) * bar_spacing
        y_top = y_center - bar_height / 2
        
        color = color_palette[i % len(color_palette)]
        
        # Family name
        svg_parts.append(f'<text x="{margin_left - 10}" y="{y_center + 4}" text-anchor="end" font-size="11">{family} (n={stats["count"]})</text>')
        
        # Background bar (full range)
        svg_parts.append(f'<rect x="{margin_left}" y="{y_top}" width="{plot_width}" height="{bar_height}" fill="#f5f5f5" stroke="#ddd" stroke-width="1"/>')
        
        # Mean bar (from zero line)
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
        if family in family_scores:
            np.random.seed(hash(family) % 2**32)  # Reproducible jitter
            for j, lang_item in enumerate(family_scores[family]):
                x_pos = scale_x(lang_item['effect'])
                # Clamp to visible range
                x_pos = max(margin_left, min(width - margin_right, x_pos))
                # Jitter within bar height
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
    
    // Color scale for β(1→max) scores: negative = MAL compliance (green), positive = anti-MAL (red)
    function scoreToColor(score) {{
        if (score < -0.1) {{
            // Green for MAL compliance (negative slope means size decreases with n)
            const t = Math.min(1, Math.abs(score) / 0.3);
            return d3.interpolateRgb("#b8e6b8", "#2e7d32")(t);
        }} else if (score > 0.1) {{
            // Red for anti-MAL (positive slope)
            const t = Math.min(1, score / 0.3);
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
                           β(1→max): ${{d.mal_score.toFixed(3)}}<br/>
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
            {{ label: "Strong MAL (<-0.2)", score: -0.3 }},
            {{ label: "Moderate MAL", score: -0.15 }},
            {{ label: "Weak/Neutral", score: 0 }},
            {{ label: "Anti-MAL (>0.1)", score: 0.2 }}
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
            .text("β(1→max)");
        
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


def generate_directional_mal_html_report(
    lang2MAL,
    lang2counts_left,
    lang2counts_right,
    langNames,
    output_path,
    min_count=None,
    langnameGroup=None,
    wals_languages_path=None,
    title_suffix="",
    description="",
    lang_to_vo=None
):
    """
    Generate an interactive HTML report for MAL analysis with directional (left/right) breakdowns.
    
    This extends the standard report by adding separate analyses for:
    - Left dependents (n left deps, regardless of right side)
    - Right dependents (n right deps, regardless of left side)
    
    Args:
        lang2MAL: Dict mapping lang -> {'total': {n: MAL}, 'left': {n: MAL}, 'right': {n: MAL}}
        lang2counts_left: Dict mapping lang -> n -> count for left configs
        lang2counts_right: Dict mapping lang -> n -> count for right configs
        langNames: Dict mapping lang code -> full language name
        output_path: Path to save the HTML file
        min_count: Minimum count threshold used in the analysis. Defaults to DEFAULT_MIN_COUNT.
        langnameGroup: Optional dict mapping language name -> language family/group
        wals_languages_path: Optional path to WALS languages.csv for geographic data
        title_suffix: String to append to the title (e.g., "VO Languages")
        description: Additional description for the report header
        lang_to_vo: Optional dict mapping lang code -> VO score (0-1)
        
    Returns:
        Dict with statistics about the generated report
    """
    if min_count is None:
        min_count = DEFAULT_MIN_COUNT
    # Extract total, left, right MAL data
    lang2MAL_total = {lang: data['total'] for lang, data in lang2MAL.items() if data.get('total')}
    lang2MAL_left = {lang: data['left'] for lang, data in lang2MAL.items() if data.get('left')}
    lang2MAL_right = {lang: data['right'] for lang, data in lang2MAL.items() if data.get('right')}
    
    # Get total counts (sum of all positions for each n)
    lang2counts_total = {}
    for lang in lang2MAL_total:
        n_to_count = defaultdict(int)
        for side_counts in [lang2counts_left.get(lang, {}), lang2counts_right.get(lang, {})]:
            for n, count in side_counts.items():
                n_to_count[n] += count
        lang2counts_total[lang] = dict(n_to_count)
    
    # Filter by min_count to exclude unreliable data points
    lang2MAL_total_f = _filter_mal_by_count(lang2MAL_total, lang2counts_total, min_count)
    lang2MAL_left_f = _filter_mal_by_count(lang2MAL_left, lang2counts_left, min_count)
    lang2MAL_right_f = _filter_mal_by_count(lang2MAL_right, lang2counts_right, min_count)
    
    # Compute local change scores for all three
    lang2local_scores_total = compute_local_scores_for_all_languages(lang2MAL_total_f)
    lang2local_scores_left = compute_local_scores_for_all_languages(lang2MAL_left_f)
    lang2local_scores_right = compute_local_scores_for_all_languages(lang2MAL_right_f)
    
    # Compute chart data for all three
    viz_data_total = _compute_chart_data(lang2MAL_total_f, lang2local_scores_total, langNames, langnameGroup)
    viz_data_left = _compute_chart_data(lang2MAL_left_f, lang2local_scores_left, langNames, langnameGroup)
    viz_data_right = _compute_chart_data(lang2MAL_right_f, lang2local_scores_right, langNames, langnameGroup)
    
    max_n = viz_data_total['max_n']
    
    # Add geographic data if WALS path provided
    if wals_languages_path and os.path.exists(wals_languages_path):
        geo_data = _load_geographic_data(wals_languages_path, lang2MAL_total, lang2local_scores_total, langNames)
        viz_data_total['geo_data'] = geo_data
    else:
        viz_data_total['geo_data'] = []
    
    # Sort languages alphabetically by name
    lang_names_sorted = sorted(
        [(lang, langNames.get(lang, lang)) for lang in lang2MAL_total.keys()],
        key=lambda x: x[1].lower()
    )
    
    # Build HTML
    html_parts = []
    html_parts.append(_get_directional_html_header(min_count, title_suffix, description))
    
    # Section 1: Total (bilateral) analysis
    html_parts.append('<h2 id="total-section">1. Total Dependents Analysis (Bilateral)</h2>')
    html_parts.append('<p>This section shows MAL analysis for total dependents (left + right combined).</p>')
    html_parts.append(_build_table(
        lang_names_sorted, lang2MAL_total, lang2counts_total, 
        lang2local_scores_total, viz_data_total['effect_by_lang'], 
        viz_data_total['group_by_lang'], max_n, min_count,
        table_id="malTable_total", include_sort_script=True, lang_to_vo=lang_to_vo, mal_label="MAL"
    ))
    html_parts.append(_get_charts_section(viz_data_total, min_count))
    
    # Section 2: Left Dependents
    html_parts.append('<h2 id="left-section">2. Left Dependents Analysis</h2>')
    html_parts.append('<p>MAL analysis for <strong>left-side dependents</strong> (n dependents to the left of the verb, regardless of how many are on the right).</p>')
    
    left_lang_names = [(l, n) for l, n in lang_names_sorted if l in lang2MAL_left and lang2MAL_left[l]]
    if left_lang_names:
        max_n_left = max(max(d.keys()) for d in lang2MAL_left.values() if d) if lang2MAL_left else 6
        html_parts.append(_build_table(
            left_lang_names, lang2MAL_left, lang2counts_left,
            lang2local_scores_left, viz_data_left.get('effect_by_lang', {}),
            viz_data_left.get('group_by_lang', {}), max_n_left, min_count,
            table_id="malTable_left", include_sort_script=False, lang_to_vo=lang_to_vo, mal_label="Left MAL"
        ))
        html_parts.append(_get_directional_charts_section(viz_data_left, "Left", min_count))
    else:
        html_parts.append('<p><em>No left dependent data available for this subset.</em></p>')
    
    # Section 3: Right Dependents
    html_parts.append('<h2 id="right-section">3. Right Dependents Analysis</h2>')
    html_parts.append('<p>MAL analysis for <strong>right-side dependents</strong> (n dependents to the right of the verb, regardless of how many are on the left).</p>')
    
    right_lang_names = [(l, n) for l, n in lang_names_sorted if l in lang2MAL_right and lang2MAL_right[l]]
    if right_lang_names:
        max_n_right = max(max(d.keys()) for d in lang2MAL_right.values() if d) if lang2MAL_right else 6
        html_parts.append(_build_table(
            right_lang_names, lang2MAL_right, lang2counts_right,
            lang2local_scores_right, viz_data_right.get('effect_by_lang', {}),
            viz_data_right.get('group_by_lang', {}), max_n_right, min_count,
            table_id="malTable_right", include_sort_script=False, lang_to_vo=lang_to_vo, mal_label="Right MAL"
        ))
        html_parts.append(_get_directional_charts_section(viz_data_right, "Right", min_count))
    else:
        html_parts.append('<p><em>No right dependent data available for this subset.</em></p>')
    
    # Footer
    html_parts.append('</body>\n</html>')
    
    # Write HTML file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    html_content = ''.join(html_parts)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Return statistics
    return {
        'output_path': output_path,
        'n_languages': len(lang_names_sorted),
        'n_languages_left': len(left_lang_names),
        'n_languages_right': len(right_lang_names),
        'max_n': max_n,
        'chart_data': viz_data_total['chart_data']
    }


def _get_directional_html_header(min_count, title_suffix="", description=""):
    """Generate HTML header for directional report."""
    title = f"MAL_n Analysis: {title_suffix}" if title_suffix else "MAL_n Analysis"
    desc_html = f'<p style="color: #1565c0; font-weight: bold;">{description}</p>' if description else ''
    
    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; max-width: 1600px; margin: 0 auto; padding: 20px; }}
h1 {{ color: #333; }}
h2 {{ color: #1565c0; margin-top: 50px; padding-top: 20px; border-top: 3px solid #1565c0; }}
h3 {{ color: #666; margin-top: 20px; }}
.info-box {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
.info-box p {{ margin: 5px 0; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: center; font-size: 12px; }}
th {{ background-color: #4CAF50; color: white; position: sticky; top: 0; z-index: 10; }}
th.mal-col {{ background-color: #2196F3; }}
th.score-col {{ background-color: #FF9800; }}
th.effect-col {{ background-color: #9C27B0; }}
th.group-col {{ background-color: #607D8B; }}
th.vo-col {{ background-color: #795548; }}
.vo-cell {{ font-weight: bold; font-size: 11px; }}
.vo-high {{ background-color: #c8e6c9; }}  /* VO > 0.66 = green */
.vo-low {{ background-color: #ffcdd2; }}   /* OV < 0.33 = red */
.vo-mid {{ background-color: #fff9c4; }}   /* Mixed = yellow */
.effect-cell {{ font-weight: bold; }}
.group-cell {{ font-size: 11px; color: #555; white-space: nowrap; }}
tr:nth-child(even) {{ background-color: #f9f9f9; }}
tr:hover {{ background-color: #f1f1f1; }}
.lang-name {{ text-align: left; font-weight: bold; white-space: nowrap; }}
.mal-cell {{ background-color: #e3f2fd; }}
.score-cell {{ font-weight: bold; }}
.score-positive {{ background-color: #c8e6c9; }}
.score-negative {{ background-color: #ffcdd2; }}
.score-neutral {{ background-color: #fff9c4; }}
.na-cell {{ color: #999; }}
.mal-cell-lowcount {{ background-color: #f5f5f5; color: #999; font-style: italic; }}
.explanation {{ background: #fff3e0; padding: 15px; border-left: 4px solid #ff9800; margin: 20px 0; }}
.chart-container {{ margin: 30px 0; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
.chart-row {{ display: flex; flex-wrap: wrap; gap: 20px; }}
.chart-half {{ flex: 1; min-width: 400px; }}
canvas {{ max-width: 100%; }}
.nav-links {{ position: sticky; top: 0; background: #333; padding: 10px; z-index: 100; margin: -20px -20px 20px -20px; }}
.nav-links a {{ color: white; margin-right: 20px; text-decoration: none; }}
.nav-links a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>

<h1>{title}</h1>

{desc_html}

<div class="info-box" style="background: #e3f2fd; border-left: 4px solid #1976d2; padding: 15px; margin-bottom: 20px;">
<h3 style="margin-top: 0; color: #1976d2;">⚙️ Statistical Threshold: MIN_COUNT = {min_count}</h3>
<p>A configuration (specific n value) is only included in <strong>regression calculations and averages</strong> if it has at least <strong>{min_count} occurrences</strong>.</p>
<p>Configurations with fewer occurrences are shown in <span style="color: #999;">grey</span> for reference but are <strong>not used</strong> for computing slopes (β) or decrease ratios.</p>
</div>

<div class="info-box">
<p><strong>Data source:</strong> Bilateral dependency configurations from Universal Dependencies treebanks</p>
<p><strong>MAL_n:</strong> Arithmetic mean of constituent sizes for heads with n total dependents</p>

<h4 style="margin-top:15px;">Log-Log Regression (β = MAL Effect Score)</h4>
<p>Each language has two inline plots showing log(n) vs log(MAL_n) with linear regression:</p>
<p><strong>Regression 1→max:</strong> Uses all available data points (n=1 to max) <em>where count ≥ {min_count}</em></p>
<p><strong>Regression 2→max:</strong> Excludes n=1 (starts from n=2 to max) <em>where count ≥ {min_count}</em></p>
<p><strong>β (slope):</strong> The negative of the log-log regression slope. Under MAL: log(MAL_n) = a - β·log(n)</p>
<p style="margin-left: 20px;">• <span style="background:#c8e6c9;padding:2px 6px;">β &gt; 0.1 (green)</span>: MAL compliance</p>
<p style="margin-left: 20px;">• <span style="background:#ffcdd2;padding:2px 6px;">β &lt; -0.1 (red)</span>: Anti-MAL</p>
<p style="margin-left: 20px;">• <span style="background:#fff9c4;padding:2px 6px;">|β| ≤ 0.1 (yellow)</span>: Weak effect</p>

<h4 style="margin-top:15px;">Local Change Scores (n→n+1)</h4>
<p><strong>Score:</strong> [ln(MAL_n) - ln(MAL_{{n+1}})] / [ln(n+1) - ln(n)]</p>
<p><em>Only computed between consecutive n values that both have count ≥ {min_count}</em></p>
</div>
'''


def _get_directional_charts_section(viz_data, direction, min_count):
    """Generate a simplified charts section for left/right directional analysis."""
    
    if not viz_data.get('mean_curve'):
        return '<p><em>Insufficient data for charts.</em></p>'
    
    chart_data_json = json.dumps(viz_data.get('chart_data', {}))
    mean_curve_json = json.dumps(viz_data.get('mean_curve', {}))
    normalized_curve_json = json.dumps(viz_data.get('normalized_curve', {}))
    box_plot_data_json = json.dumps(viz_data.get('box_plot_data', {}))
    max_n = viz_data.get('max_n', 6)
    
    # Generate unique chart IDs for this direction
    dir_id = direction.lower()
    
    # Generate SVG box plot
    svg_box_plot = _generate_svg_box_plot(viz_data.get('box_plot_data', {}))
    
    return f'''
<h3>{direction}-Side Mean MAL Curve</h3>
<div class="chart-container">
<canvas id="meanCurveChart_{dir_id}" height="100"></canvas>
<div class="explanation">
<p><strong>Mean MAL_n trajectory for {direction.lower()}-side dependents.</strong> 
Under MAL, we expect this curve to decrease monotonically.</p>
</div>
</div>

<h3>{direction}-Side Local Change Score Distribution</h3>
<div class="chart-container">
{svg_box_plot}
<div class="explanation">
<p><strong>Distribution of local change scores</strong> for {direction.lower()}-side dependents.
Positive values indicate MAL compliance at that transition.</p>
</div>
</div>

<script>
(function() {{
    const meanCurve_{dir_id} = {mean_curve_json};
    const maxN_{dir_id} = {max_n};
    
    // Colors
    const colors = {{
        primary: 'rgba(33, 150, 243, 1)',
        primaryLight: 'rgba(33, 150, 243, 0.2)'
    }};
    
    // Mean MAL Curve Chart
    const meanLabels_{dir_id} = Object.keys(meanCurve_{dir_id}).map(n => 'n=' + n);
    const meanValues_{dir_id} = Object.values(meanCurve_{dir_id}).map(d => d.mean);
    const q1Values_{dir_id} = Object.values(meanCurve_{dir_id}).map(d => d.q1);
    const q3Values_{dir_id} = Object.values(meanCurve_{dir_id}).map(d => d.q3);
    
    new Chart(document.getElementById('meanCurveChart_{dir_id}'), {{
        type: 'line',
        data: {{
            labels: meanLabels_{dir_id},
            datasets: [
                {{
                    label: 'IQR (Q1-Q3)',
                    data: q3Values_{dir_id},
                    fill: '+1',
                    backgroundColor: colors.primaryLight,
                    borderColor: 'transparent',
                    pointRadius: 0
                }},
                {{
                    label: 'Q1',
                    data: q1Values_{dir_id},
                    fill: false,
                    borderColor: 'transparent',
                    pointRadius: 0
                }},
                {{
                    label: 'Mean MAL_n ({direction})',
                    data: meanValues_{dir_id},
                    borderColor: colors.primary,
                    backgroundColor: colors.primary,
                    borderWidth: 3,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    fill: false
                }}
            ]
        }},
        options: {{
            responsive: true,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: function(context) {{
                            const n = context.dataIndex + 1;
                            const stats = meanCurve_{dir_id}[n];
                            if (stats) {{
                                return [
                                    `Mean: ${{stats.mean.toFixed(3)}}`,
                                    `Median: ${{stats.median.toFixed(3)}}`,
                                    `IQR: ${{stats.q1.toFixed(3)}} - ${{stats.q3.toFixed(3)}}`,
                                    `n languages: ${{stats.count}}`
                                ];
                            }}
                            return context.formattedValue;
                        }}
                    }}
                }}
            }},
            scales: {{
                y: {{
                    title: {{ display: true, text: 'Mean Constituent Size' }},
                    beginAtZero: false
                }},
                x: {{
                    title: {{ display: true, text: 'Number of {direction} Dependents' }}
                }}
            }}
        }}
    }});
}})();
</script>
'''

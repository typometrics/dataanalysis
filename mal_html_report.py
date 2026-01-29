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


def get_sample_counts_per_n(all_langs_position2num, min_count=10):
    """
    Get total sample count for each (language, n) combination from bilateral keys.
    
    Args:
        all_langs_position2num: Dict mapping lang -> key -> count
        min_count: Minimum count threshold for inclusion
        
    Returns:
        Dict mapping lang -> n -> total_count
    """
    lang2counts = {}
    for lang in all_langs_position2num:
        n_to_count = defaultdict(int)
        for key, count in all_langs_position2num[lang].items():
            if count < min_count:
                continue
            match = re.match(r'bilateral_L(\d+)_R(\d+)_pos_(\d+)_(left|right)$', key)
            if match:
                n_left = int(match.group(1))
                n_right = int(match.group(2))
                total_n = n_left + n_right
                n_to_count[total_n] += count
        lang2counts[lang] = dict(n_to_count)
    return lang2counts


def get_directional_counts(all_langs_position2num, min_count=10):
    """
    Get sample counts for pure left and pure right dependent configurations.
    
    Pure left: bilateral_L{n}_R0_* (n left dependents, 0 right)
    Pure right: bilateral_L0_R{n}_* (0 left dependents, n right)
    
    Args:
        all_langs_position2num: Dict mapping lang -> key -> count
        min_count: Minimum count threshold for inclusion
        
    Returns:
        Tuple of (lang2counts_left, lang2counts_right)
    """
    lang2counts_left = {}
    lang2counts_right = {}
    
    for lang in all_langs_position2num:
        left_counts = defaultdict(int)
        right_counts = defaultdict(int)
        
        for key, count in all_langs_position2num[lang].items():
            if count < min_count:
                continue
            match = re.match(r'bilateral_L(\d+)_R(\d+)_pos_(\d+)_(left|right)$', key)
            if match:
                n_left = int(match.group(1))
                n_right = int(match.group(2))
                
                # Pure left: L{n}_R0
                if n_right == 0 and n_left > 0:
                    left_counts[n_left] += count
                
                # Pure right: L0_R{n}
                if n_left == 0 and n_right > 0:
                    right_counts[n_right] += count
        
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
    
    # Normalized MAL curve (MAL_n / MAL_1)
    normalized_curve = {}
    for n in range(1, max_n + 1):
        normalized_values = []
        for lang in lang2MAL_total:
            if 1 in lang2MAL_total[lang] and n in lang2MAL_total[lang]:
                mal_1 = lang2MAL_total[lang][1]
                mal_n = lang2MAL_total[lang][n]
                if mal_1 > 0:
                    normalized_values.append(mal_n / mal_1)
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
    
    # MAL_1 vs Slope scatter plot data
    # Compute average slope (mean of local change scores) for each language
    mal1_vs_slope = []
    for lang, mal_data in lang2MAL_total.items():
        if 1 not in mal_data:
            continue
        mal_1 = mal_data[1]
        lang_name = langNames.get(lang, lang)
        group = langnameGroup.get(lang_name, 'Other') if langnameGroup else 'Other'
        
        # Get all local change scores for this language
        scores = lang2local_scores.get(lang, {})
        valid_scores = [s for s in scores.values() if not np.isnan(s)]
        if valid_scores:
            mean_slope = float(np.mean(valid_scores))
            mal1_vs_slope.append({
                'name': lang_name,
                'code': lang,
                'group': group,
                'mal_1': float(mal_1),
                'mean_slope': mean_slope,
                'n_transitions': len(valid_scores)
            })
    
    # Effect score: mean of all local change scores (positive = MAL compliance)
    effect_scores = []
    for lang, mal_data in lang2MAL_total.items():
        lang_name = langNames.get(lang, lang)
        group = langnameGroup.get(lang_name, 'Other') if langnameGroup else 'Other'
        
        scores = lang2local_scores.get(lang, {})
        valid_scores = [s for s in scores.values() if not np.isnan(s)]
        if valid_scores:
            effect = float(np.mean(valid_scores))
            n_compliant = sum(1 for s in valid_scores if s > 0)
            effect_scores.append({
                'name': lang_name,
                'code': lang,
                'group': group,
                'effect': effect,
                'n_compliant': n_compliant,
                'n_transitions': len(valid_scores)
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
    
    return {
        'chart_data': {k: v for k, v in sorted(chart_data.items())},
        'mean_curve': mean_curve,
        'normalized_curve': normalized_curve,
        'box_plot_data': box_plot_data,
        'language_curves': language_curves,
        'data_availability': data_availability,
        'mal1_vs_slope': mal1_vs_slope,
        'effect_scores': effect_scores,
        'effect_by_lang': effect_by_lang,
        'group_by_lang': group_by_lang,
        'family_stats': family_stats,
        'max_n': max_n
    }


def _load_geographic_data(wals_path, lang2MAL_total, lang2local_scores, langNames):
    """
    Load WALS language coordinates and match with UD languages.
    
    Returns list of dicts with: name, code, lat, lon, mal_score, family
    """
    try:
        wals_df = pd.read_csv(wals_path)
    except Exception as e:
        print(f"Warning: Could not load WALS data: {e}")
        return []
    
    geo_data = []
    
    for lang_code, mal_data in lang2MAL_total.items():
        lang_name = langNames.get(lang_code, lang_code)
        
        # Try to find matching WALS language by ISO code
        # UD language codes are typically ISO 639-1 or ISO 639-3
        match = None
        
        # First try exact ISO639P3code match
        if 'ISO639P3code' in wals_df.columns:
            matches = wals_df[wals_df['ISO639P3code'] == lang_code]
            if len(matches) > 0:
                match = matches.iloc[0]
        
        # Try matching by name (clean up language names)
        if match is None and 'Name' in wals_df.columns:
            # Clean language name (remove parenthetical parts, lowercase)
            clean_name = lang_name.split('(')[0].strip().lower()
            for _, row in wals_df.iterrows():
                wals_name = str(row['Name']).split('(')[0].strip().lower()
                if clean_name == wals_name or clean_name in wals_name or wals_name in clean_name:
                    match = row
                    break
        
        if match is not None and pd.notna(match.get('Latitude')) and pd.notna(match.get('Longitude')):
            # Compute global MAL score (mean of local change scores)
            scores = lang2local_scores.get(lang_code, {})
            valid_scores = [s for s in scores.values() if not np.isnan(s)]
            mal_score = float(np.mean(valid_scores)) if valid_scores else 0.0
            
            family = str(match.get('Family', 'Unknown')) if pd.notna(match.get('Family')) else 'Unknown'
            
            geo_data.append({
                'name': lang_name,
                'code': lang_code,
                'lat': float(match['Latitude']),
                'lon': float(match['Longitude']),
                'mal_score': mal_score,
                'family': family,
                'n_transitions': len(valid_scores)
            })
    
    return geo_data


def generate_mal_html_report(
    lang2MAL_total,
    lang2counts,
    langNames,
    output_path,
    min_count=10,
    langnameGroup=None,
    wals_languages_path=None
):
    """
    Generate an interactive HTML report for MAL analysis.
    
    Args:
        lang2MAL_total: Dict mapping lang -> n -> MAL value
        lang2counts: Dict mapping lang -> n -> count
        langNames: Dict mapping lang code -> full language name
        output_path: Path to save the HTML file
        min_count: Minimum count threshold used in the analysis
        langnameGroup: Optional dict mapping language name -> language family/group
        wals_languages_path: Optional path to WALS languages.csv for geographic data
        
    Returns:
        Dict with statistics about the generated report
    """
    # Compute local change scores
    lang2local_scores = compute_local_scores_for_all_languages(lang2MAL_total)
    
    # Compute chart data
    viz_data = _compute_chart_data(lang2MAL_total, lang2local_scores, langNames, langnameGroup)
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
    
    # Build HTML
    html_parts = []
    html_parts.append(_get_html_header(min_count))
    
    # Table
    html_parts.append(_build_table(lang_names_sorted, lang2MAL_total, lang2counts, lang2local_scores, viz_data['effect_by_lang'], viz_data['group_by_lang'], max_n))
    
    # Table explanation
    html_parts.append(_get_table_explanation(min_count))
    
    # Charts section
    html_parts.append(_get_charts_section(viz_data, min_count))
    
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
        'max_n': max_n,
        'n_transitions': len(viz_data['chart_data']),
        'chart_data': viz_data['chart_data']
    }


def _build_table(lang_names_sorted, lang2MAL_total, lang2counts, lang2local_scores, effect_by_lang, group_by_lang, max_n):
    """Build the HTML table with sortable columns."""
    html_parts = []
    
    # Table header with sortable columns
    html_parts.append('<table id="malTable">\n<thead>\n<tr>\n')
    html_parts.append('<th onclick="sortTable(0, \'string\')" style="cursor:pointer">Language ⇅</th>\n')
    html_parts.append('<th class="group-col" onclick="sortTable(1, \'string\')" style="cursor:pointer">Family ⇅</th>\n')
    html_parts.append('<th class="effect-col" onclick="sortTable(2, \'number\')" style="cursor:pointer">MAL Effect ⇅</th>\n')
    col_idx = 3
    for n in range(1, max_n + 1):
        html_parts.append(f'<th class="mal-col" onclick="sortTable({col_idx}, \'number\')" style="cursor:pointer">MAL_{n}<br>(count) ⇅</th>\n')
        col_idx += 1
        if n < max_n:
            html_parts.append(f'<th class="score-col" onclick="sortTable({col_idx}, \'number\')" style="cursor:pointer">{n}→{n+1} ⇅</th>\n')
            col_idx += 1
    html_parts.append('</tr>\n</thead>\n<tbody>\n')
    
    # Table rows
    for lang, lang_name in lang_names_sorted:
        mal_data = lang2MAL_total[lang]
        count_data = lang2counts.get(lang, {})
        score_data = lang2local_scores.get(lang, {})
        effect = effect_by_lang.get(lang)
        group = group_by_lang.get(lang, 'Unknown')
        
        html_parts.append(f'<tr>\n<td class="lang-name">{lang_name}</td>\n')
        html_parts.append(f'<td class="group-cell">{group}</td>\n')
        
        # MAL Effect score column
        if effect is not None:
            if effect > 0.1:
                css_class = "effect-cell score-positive"
            elif effect < -0.1:
                css_class = "effect-cell score-negative"
            else:
                css_class = "effect-cell score-neutral"
            html_parts.append(f'<td class="{css_class}" data-value="{effect:.6f}">{effect:.3f}</td>\n')
        else:
            html_parts.append('<td class="na-cell" data-value="">—</td>\n')
        
        for n in range(1, max_n + 1):
            # MAL value and count
            if n in mal_data:
                mal_val = mal_data[n]
                count_val = count_data.get(n, 0)
                html_parts.append(f'<td class="mal-cell" data-value="{mal_val:.6f}">{mal_val:.3f}<br>({count_val})</td>\n')
            else:
                html_parts.append('<td class="na-cell" data-value="">—</td>\n')
            
            # Local change score
            if n < max_n:
                score_key = f"{n}→{n+1}"
                if score_key in score_data and not np.isnan(score_data[score_key]):
                    score = score_data[score_key]
                    if score > 0.1:
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
    
    # Add sorting JavaScript
    html_parts.append('''
<script>
let sortDirections = {};

function sortTable(colIndex, type) {
    const table = document.getElementById("malTable");
    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);
    
    // Toggle sort direction
    sortDirections[colIndex] = !sortDirections[colIndex];
    const ascending = sortDirections[colIndex];
    
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
''')
    
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
th.group-col {{ background-color: #607D8B; }}
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
.explanation {{ background: #fff3e0; padding: 15px; border-left: 4px solid #ff9800; margin: 20px 0; }}
.chart-container {{ margin: 30px 0; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
.chart-row {{ display: flex; flex-wrap: wrap; gap: 20px; }}
.chart-half {{ flex: 1; min-width: 400px; }}
canvas {{ max-width: 100%; }}
</style>
</head>
<body>
<h1>MAL_n Analysis: Constituent Size by Number of Dependents</h1>

<div class="info-box">
<p><strong>Data source:</strong> Bilateral dependency configurations from Universal Dependencies treebanks</p>
<p><strong>Minimum occurrences:</strong> {min_count} per configuration (to ensure statistical reliability)</p>
<p><strong>MAL_n:</strong> Geometric mean of constituent sizes for heads with n total dependents</p>
<p><strong>Count:</strong> Number of observations contributing to the MAL_n value</p>
<p><strong>MAL Effect Score:</strong> Mean of all local change scores for a language (positive = MAL compliance)</p>
<p><strong>Local Change Score (n→n+1):</strong> [ln(MAL_n) - ln(MAL_{{n+1}})] / [ln(n+1) - ln(n)]</p>
<p style="margin-left: 20px;">• Positive values (green): MAL compliance - constituent size decreases as n increases</p>
<p style="margin-left: 20px;">• Negative values (red): Anti-MAL - constituent size increases with n</p>
<p style="margin-left: 20px;">• Values near 0 (yellow): Weak or no effect</p>
</div>
'''


def _get_table_explanation(min_count):
    """Generate table explanation section."""
    return f'''
<div class="explanation">
<h2>Understanding the Table</h2>
<p><strong>MAL_n values (blue columns):</strong> These represent the geometric mean size of constituents 
(dependents) for verb heads with exactly n total dependents. Under the Menzerath-Altmann Law, we expect 
MAL_n to decrease as n increases — heads with more dependents should have shorter individual dependents.</p>

<p><strong>Local Change Scores (orange columns):</strong> These measure the "elasticity" of the MAL effect 
between consecutive n values. The formula normalizes the log-change in constituent size by the log-change 
in n, making scores comparable across different transitions. A score of 1.0 would indicate that a 1% 
increase in n corresponds to a 1% decrease in constituent size.</p>

<p><strong>Color coding:</strong></p>
<ul>
<li><span style="background:#c8e6c9; padding: 2px 8px;">Green (&gt; 0.1)</span>: Strong MAL compliance — constituent size decreases meaningfully</li>
<li><span style="background:#fff9c4; padding: 2px 8px;">Yellow (-0.1 to 0.1)</span>: Weak effect — little change in constituent size</li>
<li><span style="background:#ffcdd2; padding: 2px 8px;">Red (&lt; -0.1)</span>: Anti-MAL — constituent size increases (unexpected)</li>
</ul>

<p><strong>Missing values (—):</strong> Indicate insufficient data (fewer than {min_count} occurrences) 
for that language/n combination, or non-consecutive n values in the data.</p>
</div>
'''


def _get_charts_section(viz_data, min_count):
    """Generate all charts using Chart.js and SVG."""
    
    chart_data_json = json.dumps(viz_data['chart_data'])
    mean_curve_json = json.dumps(viz_data['mean_curve'])
    normalized_curve_json = json.dumps(viz_data['normalized_curve'])
    box_plot_data_json = json.dumps(viz_data['box_plot_data'])
    language_curves_json = json.dumps(viz_data['language_curves'])
    data_availability_json = json.dumps(viz_data['data_availability'])
    mal1_vs_slope_json = json.dumps(viz_data['mal1_vs_slope'])
    effect_scores_json = json.dumps(viz_data['effect_scores'])
    family_stats_json = json.dumps(viz_data['family_stats'])
    geo_data_json = json.dumps(viz_data.get('geo_data', []))
    max_n = viz_data['max_n']
    
    # Generate SVG box plot
    svg_box_plot = _generate_svg_box_plot(viz_data['box_plot_data'])
    
    # Generate SVG effect by family chart
    svg_effect_by_family = _generate_svg_effect_by_family(viz_data['family_stats'], viz_data['effect_scores'])
    
    # Generate SVG world map
    svg_world_map = _generate_svg_world_map(viz_data.get('geo_data', []))
    
    return f'''
<h2>Visualizations</h2>

<!-- Chart 1: Mean MAL Curve -->
<div class="chart-container">
<h3>1. Mean MAL_n Curve Across Languages</h3>
<canvas id="meanCurveChart" height="100"></canvas>
<div class="explanation">
<p><strong>Interpretation:</strong> This chart shows the average MAL_n trajectory across all languages. 
The shaded area represents the interquartile range (25th-75th percentile), showing cross-linguistic variation.
A downward trend confirms MAL: as n increases, constituent size decreases on average.</p>
<p><strong>Note:</strong> The number of contributing languages decreases at higher n values (see Data Availability chart), 
which may affect the reliability of the mean at those points.</p>
</div>
</div>

<!-- Chart 2: Normalized Constituent Size -->
<div class="chart-container">
<h3>2. Normalized MAL Curve (MAL_n / MAL_1)</h3>
<canvas id="normalizedCurveChart" height="100"></canvas>
<div class="explanation">
<p><strong>Interpretation:</strong> This chart shows the relative change in constituent size, normalized by each language's 
starting point (MAL_1 = 1.0 for all languages). This allows direct comparison of the <em>rate of decline</em> across 
languages, independent of their initial constituent sizes.</p>
<p><strong>Key insight:</strong> All languages start at 1.0; the steeper the decline, the stronger the MAL effect.
A value of 0.8 at n=3 means constituents are 80% of their size at n=1.</p>
</div>
</div>

<!-- Chart 3: Data Availability -->
<div class="chart-container">
<h3>3. Data Availability by Number of Dependents</h3>
<canvas id="availabilityChart" height="80"></canvas>
<div class="explanation">
<p><strong>Interpretation:</strong> This chart shows how many languages have sufficient data (≥{min_count} occurrences) 
at each value of n. The sharp decline at higher n values explains why mean curves may become less reliable 
and potentially show unexpected patterns (survivor bias).</p>
</div>
</div>

<!-- Chart 4: SVG Box Plot of Local Change Scores -->
<div class="chart-container">
<h3>4. Distribution of Local Change Scores by Transition</h3>
{svg_box_plot}
<div class="explanation">
<p><strong>Interpretation:</strong> True box plot showing the distribution of local change scores across languages for each transition.
The box spans the interquartile range (Q1 to Q3), with the median marked. Whiskers extend to the most extreme points within 1.5×IQR, and outliers are shown as individual dots.</p>
<p><strong>Color coding:</strong> Green boxes indicate median > 0.1 (MAL compliant), yellow = near zero, red = median < -0.1 (anti-MAL).</p>
<p><strong>Key insight:</strong> Values above the dashed zero line indicate MAL compliance — constituent size decreases as n increases.</p>
</div>
</div>

<!-- Chart 5: Individual Language Trajectories -->
<div class="chart-container">
<h3>5. Individual Language MAL_n Trajectories</h3>
<canvas id="trajectoriesChart" height="120"></canvas>
<div class="explanation">
<p><strong>Interpretation:</strong> Each line represents one language's MAL_n trajectory. 
The thick black line shows the cross-linguistic mean. Most languages show a downward trend (MAL compliance), 
but there is considerable variation in both the starting point (MAL_1) and the slope of decline.</p>
<p><strong>Interactive:</strong> Hover over lines to see language names.</p>
</div>
</div>

<!-- Chart 6: Histogram of Local Change Scores -->
<div class="chart-container">
<h3>6. Histogram of All Local Change Scores</h3>
<canvas id="histogramChart" height="80"></canvas>
<div class="explanation">
<p><strong>Interpretation:</strong> This histogram shows the overall distribution of local change scores 
across all languages and transitions. A distribution centered above zero indicates general MAL compliance.
The spread shows how consistent the MAL effect is across the dataset.</p>
</div>
</div>

<!-- Chart 7: MAL_1 vs Mean Slope Scatter Plot -->
<div class="chart-container">
<h3>7. MAL_1 vs. Average Slope (Initial Size vs. Decline Rate)</h3>
<canvas id="mal1SlopeChart" height="120"></canvas>
<div class="explanation">
<p><strong>Interpretation:</strong> Each point represents one language. The x-axis shows MAL_1 (initial constituent size 
when there's only 1 dependent), and the y-axis shows the mean local change score (average slope of the MAL curve).</p>
<p><strong>Key questions:</strong></p>
<ul>
<li>Is there a relationship between starting size and rate of decline?</li>
<li>Do languages with larger initial constituents show stronger or weaker MAL effects?</li>
<li>A negative correlation would suggest a ceiling effect; a positive correlation would suggest compound effects.</li>
</ul>
<p><strong>Color coding:</strong> Points are colored by language family. Hover for details.</p>
</div>
</div>

<!-- Chart 8: MAL Effect Score by Family -->
<div class="chart-container">
<h3>8. MAL Effect Score by Language Family</h3>
{svg_effect_by_family}
<div class="explanation">
<p><strong>Interpretation:</strong> The MAL effect score is the mean of all local change scores for a language. 
Positive values indicate MAL compliance (constituent size decreases with n); negative values indicate anti-MAL behavior.</p>
<p><strong>Family comparison:</strong> This chart groups languages by family to reveal whether MAL strength 
varies systematically across genealogical groups. Box plots show the distribution within each family.</p>
<p><strong>Key insight:</strong> If MAL is a universal constraint, we expect positive effect scores across all families.
Systematic differences might indicate structural factors that modulate MAL strength.</p>
</div>
</div>

<!-- Chart 9: World Map of MAL Effect -->
<div class="chart-container">
<h3>9. World Map: Geographic Distribution of MAL Effect</h3>
{svg_world_map}
<div class="explanation">
<p><strong>Interpretation:</strong> Each dot represents a language positioned at its geographic location. 
The color indicates the global MAL effect score (mean of all local change scores for that language).</p>
<p><strong>Color scale:</strong> Green = strong MAL compliance (constituent size decreases with n), 
Yellow = weak/neutral effect, Red = anti-MAL (constituent size increases with n).</p>
<p><strong>Geographic patterns:</strong> If MAL is truly universal, we expect green dots distributed across 
all continents. Clustering of colors might suggest areal effects or shared structural features.</p>
<p><strong>Note:</strong> Only languages with geographic coordinates available in WALS are shown.</p>
</div>
</div>

<script>
// Data from Python
const chartData = {chart_data_json};
const meanCurve = {mean_curve_json};
const normalizedCurve = {normalized_curve_json};
const languageCurves = {language_curves_json};
const dataAvailability = {data_availability_json};
const mal1VsSlope = {mal1_vs_slope_json};
const effectScores = {effect_scores_json};
const familyStats = {family_stats_json};
const geoData = {geo_data_json};
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

// Chart 1: Mean MAL Curve
const meanLabels = Object.keys(meanCurve).map(n => 'n=' + n);
const meanValues = Object.values(meanCurve).map(d => d.mean);
const q1Values = Object.values(meanCurve).map(d => d.q1);
const q3Values = Object.values(meanCurve).map(d => d.q3);

new Chart(document.getElementById('meanCurveChart'), {{
    type: 'line',
    data: {{
        labels: meanLabels,
        datasets: [
            {{
                label: 'Mean MAL_n',
                data: meanValues,
                borderColor: colors.primary,
                backgroundColor: colors.primary,
                borderWidth: 3,
                fill: false,
                tension: 0.1
            }},
            {{
                label: 'Q3 (75th percentile)',
                data: q3Values,
                borderColor: 'rgba(33, 150, 243, 0.3)',
                backgroundColor: colors.primaryLight,
                borderWidth: 1,
                fill: '+1',
                tension: 0.1,
                pointRadius: 0
            }},
            {{
                label: 'Q1 (25th percentile)',
                data: q1Values,
                borderColor: 'rgba(33, 150, 243, 0.3)',
                backgroundColor: 'transparent',
                borderWidth: 1,
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
            legend: {{ position: 'top' }}
        }},
        scales: {{
            y: {{
                title: {{ display: true, text: 'MAL_n (Geometric Mean Constituent Size)' }},
                beginAtZero: false
            }},
            x: {{
                title: {{ display: true, text: 'Number of Dependents (n)' }}
            }}
        }}
    }}
}});

// Chart 2: Normalized MAL Curve
const normLabels = Object.keys(normalizedCurve).map(n => 'n=' + n);
const normMeanValues = Object.values(normalizedCurve).map(d => d.mean);
const normQ1Values = Object.values(normalizedCurve).map(d => d.q1);
const normQ3Values = Object.values(normalizedCurve).map(d => d.q3);

new Chart(document.getElementById('normalizedCurveChart'), {{
    type: 'line',
    data: {{
        labels: normLabels,
        datasets: [
            {{
                label: 'Mean (MAL_n / MAL_1)',
                data: normMeanValues,
                borderColor: 'rgba(156, 39, 176, 1)',
                backgroundColor: 'rgba(156, 39, 176, 1)',
                borderWidth: 3,
                fill: false,
                tension: 0.1
            }},
            {{
                label: 'Q3 (75th percentile)',
                data: normQ3Values,
                borderColor: 'rgba(156, 39, 176, 0.3)',
                backgroundColor: 'rgba(156, 39, 176, 0.2)',
                borderWidth: 1,
                fill: '+1',
                tension: 0.1,
                pointRadius: 0
            }},
            {{
                label: 'Q1 (25th percentile)',
                data: normQ1Values,
                borderColor: 'rgba(156, 39, 176, 0.3)',
                backgroundColor: 'transparent',
                borderWidth: 1,
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
            legend: {{ position: 'top' }}
        }},
        scales: {{
            y: {{
                title: {{ display: true, text: 'Relative Constituent Size (MAL_n / MAL_1)' }},
                beginAtZero: false,
                suggestedMin: 0.5,
                suggestedMax: 1.1
            }},
            x: {{
                title: {{ display: true, text: 'Number of Dependents (n)' }}
            }}
        }}
    }}
}});

// Chart 3: Data Availability
new Chart(document.getElementById('availabilityChart'), {{
    type: 'bar',
    data: {{
        labels: Object.keys(dataAvailability).map(n => 'n=' + n),
        datasets: [{{
            label: 'Number of Languages',
            data: Object.values(dataAvailability),
            backgroundColor: colors.primary,
            borderColor: colors.primary,
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
                title: {{ display: true, text: 'Number of Languages' }},
                beginAtZero: true
            }},
            x: {{
                title: {{ display: true, text: 'Number of Dependents (n)' }}
            }}
        }}
    }}
}});

// Chart 5: Individual Language Trajectories
const trajDatasets = [];

// Add individual language lines (semi-transparent)
languageCurves.forEach((lang, i) => {{
    const values = [];
    for (let n = 1; n <= maxN; n++) {{
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
    data: meanValues,
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
        labels: Array.from({{length: maxN}}, (_, i) => 'n=' + (i + 1)),
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

// Chart 6: Histogram of All Scores
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
                title: {{ display: true, text: 'Frequency' }},
                beginAtZero: true
            }},
            x: {{
                title: {{ display: true, text: 'Local Change Score' }}
            }}
        }}
    }}
}});

// Chart 7: MAL_1 vs Mean Slope Scatter Plot
// Create unique color for each family
const families = [...new Set(mal1VsSlope.map(d => d.group))].sort();
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
    const points = mal1VsSlope.filter(d => d.group === family);
    return {{
        label: family,
        data: points.map(d => ({{
            x: d.mal_1,
            y: d.mean_slope,
            name: d.name,
            transitions: d.n_transitions
        }})),
        backgroundColor: familyColors[family],
        borderColor: familyColors[family].replace('0.7', '1'),
        pointRadius: 6,
        pointHoverRadius: 8
    }};
}});

new Chart(document.getElementById('mal1SlopeChart'), {{
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
                        return [
                            point.name,
                            'MAL_1: ' + point.x.toFixed(2),
                            'Mean slope: ' + point.y.toFixed(3),
                            'Transitions: ' + point.transitions
                        ];
                    }}
                }}
            }}
        }},
        scales: {{
            x: {{
                title: {{ display: true, text: 'MAL_1 (Initial Constituent Size)' }},
                beginAtZero: false
            }},
            y: {{
                title: {{ display: true, text: 'Mean Local Change Score (Slope)' }},
                grid: {{
                    color: function(context) {{
                        if (context.tick.value === 0) {{
                            return 'rgba(0, 0, 0, 0.5)';
                        }}
                        return 'rgba(0, 0, 0, 0.1)';
                    }},
                    lineWidth: function(context) {{
                        if (context.tick.value === 0) {{
                            return 2;
                        }}
                        return 1;
                    }}
                }}
            }}
        }}
    }}
}});

// Compute correlation coefficient for MAL_1 vs Slope
const mal1Values = mal1VsSlope.map(d => d.mal_1);
const slopeValues = mal1VsSlope.map(d => d.mean_slope);
const n = mal1Values.length;
const sumX = mal1Values.reduce((a, b) => a + b, 0);
const sumY = slopeValues.reduce((a, b) => a + b, 0);
const sumXY = mal1Values.reduce((total, x, i) => total + x * slopeValues[i], 0);
const sumX2 = mal1Values.reduce((total, x) => total + x * x, 0);
const sumY2 = slopeValues.reduce((total, y) => total + y * y, 0);
const correlation = (n * sumXY - sumX * sumY) / 
    Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));
console.log('Correlation between MAL_1 and mean slope: ' + correlation.toFixed(3));

// Add correlation annotation to chart
const mal1SlopeChart = Chart.getChart('mal1SlopeChart');
if (mal1SlopeChart) {{
    const annotationText = 'r = ' + correlation.toFixed(3);
    const canvas = document.getElementById('mal1SlopeChart');
    const annotationDiv = document.createElement('div');
    annotationDiv.style.cssText = 'position: relative; top: -80px; left: 70px; font-size: 14px; font-weight: bold; background: rgba(255,255,255,0.8); padding: 4px 8px; border-radius: 4px; display: inline-block;';
    annotationDiv.innerHTML = 'Correlation: r = ' + correlation.toFixed(3);
    canvas.parentNode.insertBefore(annotationDiv, canvas.nextSibling);
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


def _generate_svg_effect_by_family(family_stats, effect_scores):
    """Generate an SVG chart showing MAL effect scores by language family."""
    
    if not family_stats or not effect_scores:
        return "<p>No effect data available.</p>"
    
    # Sort families by mean consistency (descending)
    sorted_families = sorted(family_stats.items(), key=lambda x: -x[1]['mean'])
    
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
    svg_parts.append(f'<text x="{width/2}" y="25" text-anchor="middle" font-size="14" font-weight="bold">MAL Effect Score by Language Family</text>')
    
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
    svg_parts.append(f'<text x="{margin_left + plot_width/2}" y="{height - 15}" text-anchor="middle" font-size="12">MAL Effect Score (mean of local change scores)</text>')
    
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
    
    // Color scale for MAL scores
    function scoreToColor(score) {{
        if (score > 0.1) {{
            // Green for MAL compliance (interpolate intensity)
            const t = Math.min(1, score / 0.3);
            return d3.interpolateRgb("#b8e6b8", "#2e7d32")(t);
        }} else if (score < -0.1) {{
            // Red for anti-MAL
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
                           MAL Score: ${{d.mal_score.toFixed(3)}}<br/>
                           Family: ${{d.family}}<br/>
                           Transitions: ${{d.n_transitions}}`);
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
            .text("MAL Effect Score");
        
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
    min_count=10,
    langnameGroup=None,
    wals_languages_path=None,
    title_suffix="",
    description=""
):
    """
    Generate an interactive HTML report for MAL analysis with directional (left/right) breakdowns.
    
    This extends the standard report by adding separate analyses for:
    - Pure left dependents (L_n, 0 right)
    - Pure right dependents (R_n, 0 left)
    
    Args:
        lang2MAL: Dict mapping lang -> {'total': {n: MAL}, 'left': {n: MAL}, 'right': {n: MAL}}
        lang2counts_left: Dict mapping lang -> n -> count for pure left
        lang2counts_right: Dict mapping lang -> n -> count for pure right
        langNames: Dict mapping lang code -> full language name
        output_path: Path to save the HTML file
        min_count: Minimum count threshold used in the analysis
        langnameGroup: Optional dict mapping language name -> language family/group
        wals_languages_path: Optional path to WALS languages.csv for geographic data
        title_suffix: String to append to the title (e.g., "VO Languages")
        description: Additional description for the report header
        
    Returns:
        Dict with statistics about the generated report
    """
    # Extract total, left, right MAL data
    lang2MAL_total = {lang: data['total'] for lang, data in lang2MAL.items() if data.get('total')}
    lang2MAL_left = {lang: data['left'] for lang, data in lang2MAL.items() if data.get('left')}
    lang2MAL_right = {lang: data['right'] for lang, data in lang2MAL.items() if data.get('right')}
    
    # Compute local change scores for all three
    lang2local_scores_total = compute_local_scores_for_all_languages(lang2MAL_total)
    lang2local_scores_left = compute_local_scores_for_all_languages(lang2MAL_left)
    lang2local_scores_right = compute_local_scores_for_all_languages(lang2MAL_right)
    
    # Compute chart data for all three
    viz_data_total = _compute_chart_data(lang2MAL_total, lang2local_scores_total, langNames, langnameGroup)
    viz_data_left = _compute_chart_data(lang2MAL_left, lang2local_scores_left, langNames, langnameGroup)
    viz_data_right = _compute_chart_data(lang2MAL_right, lang2local_scores_right, langNames, langnameGroup)
    
    max_n = viz_data_total['max_n']
    
    # Get total counts (sum of all positions for each n)
    lang2counts_total = {}
    for lang in lang2MAL_total:
        n_to_count = defaultdict(int)
        for side_counts in [lang2counts_left.get(lang, {}), lang2counts_right.get(lang, {})]:
            for n, count in side_counts.items():
                n_to_count[n] += count
        lang2counts_total[lang] = dict(n_to_count)
    
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
        viz_data_total['group_by_lang'], max_n
    ))
    html_parts.append(_get_charts_section(viz_data_total, min_count))
    
    # Section 2: Pure Left Dependents
    html_parts.append('<h2 id="left-section">2. Pure Left Dependents Analysis</h2>')
    html_parts.append('<p>MAL analysis for <strong>pure left-side dependents only</strong> (verb-final configurations with 0 right dependents).</p>')
    
    left_lang_names = [(l, n) for l, n in lang_names_sorted if l in lang2MAL_left and lang2MAL_left[l]]
    if left_lang_names:
        max_n_left = max(max(d.keys()) for d in lang2MAL_left.values() if d) if lang2MAL_left else 6
        html_parts.append(_build_table(
            left_lang_names, lang2MAL_left, lang2counts_left,
            lang2local_scores_left, viz_data_left.get('effect_by_lang', {}),
            viz_data_left.get('group_by_lang', {}), max_n_left
        ))
        html_parts.append(_get_directional_charts_section(viz_data_left, "Left", min_count))
    else:
        html_parts.append('<p><em>No pure left dependent data available for this subset.</em></p>')
    
    # Section 3: Pure Right Dependents
    html_parts.append('<h2 id="right-section">3. Pure Right Dependents Analysis</h2>')
    html_parts.append('<p>MAL analysis for <strong>pure right-side dependents only</strong> (verb-initial configurations with 0 left dependents).</p>')
    
    right_lang_names = [(l, n) for l, n in lang_names_sorted if l in lang2MAL_right and lang2MAL_right[l]]
    if right_lang_names:
        max_n_right = max(max(d.keys()) for d in lang2MAL_right.values() if d) if lang2MAL_right else 6
        html_parts.append(_build_table(
            right_lang_names, lang2MAL_right, lang2counts_right,
            lang2local_scores_right, viz_data_right.get('effect_by_lang', {}),
            viz_data_right.get('group_by_lang', {}), max_n_right
        ))
        html_parts.append(_get_directional_charts_section(viz_data_right, "Right", min_count))
    else:
        html_parts.append('<p><em>No pure right dependent data available for this subset.</em></p>')
    
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
<div class="nav-links">
<a href="#total-section">📊 Total (Bilateral)</a>
<a href="#left-section">⬅️ Pure Left</a>
<a href="#right-section">➡️ Pure Right</a>
</div>

<h1>{title}</h1>

{desc_html}

<div class="info-box">
<p><strong>Data source:</strong> Bilateral dependency configurations from Universal Dependencies treebanks</p>
<p><strong>Minimum occurrences:</strong> {min_count} per configuration (to ensure statistical reliability)</p>
<p><strong>MAL_n:</strong> Geometric mean of constituent sizes for heads with n total dependents</p>
<p><strong>MAL Effect Score:</strong> Mean of all local change scores for a language (positive = MAL compliance)</p>
<p><strong>Local Change Score (n→n+1):</strong> [ln(MAL_n) - ln(MAL_{{n+1}})] / [ln(n+1) - ln(n)]</p>
<p style="margin-left: 20px;">• Positive values (green): MAL compliance - constituent size decreases as n increases</p>
<p style="margin-left: 20px;">• Negative values (red): Anti-MAL - constituent size increases with n</p>
<p style="margin-left: 20px;">• Values near 0 (yellow): Weak or no effect</p>
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

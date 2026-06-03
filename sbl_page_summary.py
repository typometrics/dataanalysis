import os
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
from sbl_html_utils import get_header, get_nav, get_footer

def generate(out_dir):
    try:
        from mal_html_report import _load_geographic_data
    except ImportError:
        print("Warning: mal_html_report not found. Skipping summary chart generation.")
        return

    csv_path = "data/sbl_laws_summary.csv"
    if not os.path.exists(csv_path):
        return

    df = pd.read_csv(csv_path)
    df_std = df[df['Table_Type'] == 'Standard']
    
    lang2MAL = {}
    langNames = {}
    for _, row in df_std.iterrows():
        lang_full = row['Language']
        if '_' in lang_full:
            code = lang_full.split('_')[-1]
            lang2MAL[code] = {1: 1, 2: 1}
            langNames[code] = lang_full
        else:
            lang2MAL[lang_full] = {1: 1, 2: 1}
            langNames[lang_full] = lang_full

    wals_path = 'data/wals/languages.csv'
    if not os.path.exists(wals_path):
        geo_raw = []
    else:
        geo_raw = _load_geographic_data(wals_path, lang2MAL, {}, langNames)

    name2beta_r = {row['Language']: row['R_Complex_Beta'] for _, row in df_std.iterrows() if pd.notna(row['R_Complex_Beta'])}
    name2beta_l = {row['Language']: -row['L_Complex_Beta'] for _, row in df_std.iterrows() if pd.notna(row['L_Complex_Beta'])} # Negated so positive=compliant

    def create_chart(name2beta, title, xlabel, out_svg):
        family_buckets = defaultdict(list)
        for geo in geo_raw:
            lname = geo['name']
            if lname in name2beta:
                fam = geo.get('family', 'Unknown')
                if pd.isna(fam) or not fam.strip(): fam = 'Unknown'
                family_buckets[fam].append(name2beta[lname])

        MIN_LANGS = 3
        avg_fam = []
        for fam, scores in family_buckets.items():
            if len(scores) >= MIN_LANGS and fam != 'Unknown':
                avg_fam.append((fam, sum(scores)/len(scores), len(scores)))
                
        avg_fam.sort(key=lambda x: x[1], reverse=False)
        
        if not avg_fam:
            return None
            
        labels = [f"{x[0]} (n={x[2]})" for x in avg_fam]
        values = [x[1] for x in avg_fam]
        
        plt.figure(figsize=(8, max(4, len(labels) * 0.35)))
        colors = ['#4CAF50' if v > 0.1 else ('#f39c12' if v >= 0 else '#e74c3c') for v in values]
        
        plt.barh(labels, values, color=colors, edgecolor='black')
        plt.axvline(0, color='black', lw=1, ls='-')
        plt.axvline(0.1, color='gray', lw=1, ls='--')
        plt.title(title)
        plt.xlabel(xlabel)
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        
        plt.savefig(os.path.join(out_dir, out_svg), format='svg')
        plt.close()
        return out_svg

    svg_r = create_chart(name2beta_r, 'Average Right SbL $\\beta$ by Language Family', 'Average Right SbL $\\beta$', 'summary_family_r.svg')
    svg_l = create_chart(name2beta_l, 'Average Left SbL Effect by Language Family', 'Average Left Effect (-$\\beta$)', 'summary_family_l.svg')

    html = [
        get_header("Global Summary"),
        get_nav("sbl_summary.html"),
        "<h1>Global Summary by Language Family</h1>",
        "<div class='explanation'>",
        "<p>This chart aggregates the Short-Before-Long principle across WALS language families. ",
        "For the Left side, slopes are negated so that a positive value consistently means compliance with the SbL principle. ",
        "Only families with at least 3 languages are shown.</p>",
        "</div>",
        "<div style='display:flex; gap:20px; flex-wrap:wrap;'>"
    ]
    
    if svg_r:
        html.append(f"<div style='flex:1; min-width:400px;'><img src='{svg_r}' alt='Right Family averages chart' style='max-width:100%; border:1px solid #ddd;'></div>")
    
    if svg_l:
        html.append(f"<div style='flex:1; min-width:400px;'><img src='{svg_l}' alt='Left Family averages chart' style='max-width:100%; border:1px solid #ddd;'></div>")
        
    if not svg_r and not svg_l:
        html.append("<p>Insufficient data to generate family charts.</p>")
        
    html.append("</div>")
    html.append(get_footer())
    
    with open(os.path.join(out_dir, "sbl_summary.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))

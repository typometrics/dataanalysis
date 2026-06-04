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
    df_std = df[df['Table_Type'] == 'AnyOtherSide']
    
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

    import numpy as np
    name2_r_outer = {row['Language']: np.log(row['R_Outer_Effect']) for _, row in df_std.iterrows() if pd.notna(row['R_Outer_Effect']) and row['R_Outer_Effect'] > 0}
    name2_l_outer = {row['Language']: np.log(row['L_Outer_Effect']) for _, row in df_std.iterrows() if pd.notna(row['L_Outer_Effect']) and row['L_Outer_Effect'] > 0}
    name2_horiz = {row['Language']: np.log(row['Horizontal_Right_Left_Effect']) for _, row in df_std.iterrows() if pd.notna(row['Horizontal_Right_Left_Effect']) and row['Horizontal_Right_Left_Effect'] > 0}
    

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
        colors = ['#4CAF50' if v > 0.05 else ('#f39c12' if v >= -0.05 else '#e74c3c') for v in values]
        
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

    svg_r = create_chart(name2_r_outer, "Right Outer Constituent Ratio Effect", "Log(Effect Ratio) [>0 is compliant]", "summary_family_r_outer.svg")
    svg_l = create_chart(name2_l_outer, "Left Outer Constituent Ratio Effect", "Log(Effect Ratio) [>0 is compliant]", "summary_family_l_outer.svg")
    svg_h = create_chart(name2_horiz, "Horizontal Right-Left Effect", "Log(Effect Ratio) [>0 means Right > Left]", "summary_family_horiz.svg")

    html = [
        get_header("Global Summary"),
        get_nav("sbl_summary.html"),
        "<h1 title='Global aggregates and language family breakdowns of SBL metrics.'>Global Summary by Language Family</h1>",
        "<div class='explanation'>",
        "<p>These charts aggregate the new Short-Before-Long metrics across WALS language families. ",
        "Because these metrics are geometric mean ratios, we plot their Natural Logarithm ($\\ln$). This centers neutral effects at 0, making compliant effects positive (Green) and anti-compliant effects negative (Red). ",
        "Families with at least 3 analyzed languages are included.</p>",
        "</div>",
        "<div style='display:flex; flex-direction:column; gap:20px; align-items:center;'>"
    ]
    
    if svg_r:
        html.append(f"<div style='width:100%; max-width:800px;'><h3>Right Outer Constituent Ratio Effect</h3><img src='{svg_r}' alt='Right Outer Summary' style='width:100%; border:1px solid #ddd;'></div>")
    
    if svg_l:
        html.append(f"<div style='width:100%; max-width:800px;'><h3>Left Outer Constituent Ratio Effect</h3><img src='{svg_l}' alt='Left Outer Summary' style='width:100%; border:1px solid #ddd;'></div>")

    if svg_h:
        html.append(f"<div style='width:100%; max-width:800px;'><h3>Horizontal Right-Left Effect</h3><img src='{svg_h}' alt='Horizontal Effect Summary' style='width:100%; border:1px solid #ddd;'></div>")

    if not svg_r and not svg_l and not svg_h:
        html.append("<p>Insufficient data to generate family charts.</p>")
        
    html.append("</div>")
    html.append(get_footer())
    
    with open(os.path.join(out_dir, "sbl_summary.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))

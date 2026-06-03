import os
import pandas as pd
from sbl_html_utils import get_header, get_nav, get_footer

def generate(out_dir):
    try:
        from mal_html_report import _load_geographic_data, _generate_svg_world_map
    except ImportError:
        print("Warning: mal_html_report not found. Skipping typological map generation.")
        return

    csv_path = "data/sbl_laws_summary.csv"
    if not os.path.exists(csv_path):
        print("Warning: CSV not found for typology page.")
        return

    df = pd.read_csv(csv_path)
    df_std = df[df['Table_Type'] == 'Standard']
    
    # Create fake dicts to pass to _load_geographic_data to get the geo framework
    lang2MAL = {}
    langNames = {}
    
    # We will map "French_fr" -> "fr" for the matching
    # since mal_html_report expects standard UD shortcodes or ISO codes.
    for _, row in df_std.iterrows():
        lang_full = row['Language']
        if '_' in lang_full:
            code = lang_full.split('_')[-1]
            lang2MAL[code] = {1: 1, 2: 1} # Fake data to satisfy the regression checker
            langNames[code] = lang_full
        else:
            lang2MAL[lang_full] = {1: 1, 2: 1}
            langNames[lang_full] = lang_full

    wals_path = 'data/wals/languages.csv'
    if not os.path.exists(wals_path):
        print("Warning: wals/languages.csv not found. Map will be empty.")
        geo_raw = []
    else:
        geo_raw = _load_geographic_data(wals_path, lang2MAL, {}, langNames)

    import copy

    html = [
        get_header("Typological Maps"),
        get_nav("sbl_typology.html"),
        "<h1>Geographic Distribution of the Short-Before-Long Principle</h1>",
        "<div class='explanation'>",
        "<p>These maps visualize various Short-Before-Long measures across the globe. ",
        "The standard color scale indicates compliance with the Short-Before-Long principle:",
        "<ul>",
        "<li><span style='color:green;font-weight:bold;'>Green</span>: Strong compliance (Score &gt; 0.1)</li>",
        "<li><span style='color:#f39c12;font-weight:bold;'>Yellow</span>: Weak or neutral compliance (0 &le; Score &le; 0.1)</li>",
        "<li><span style='color:red;font-weight:bold;'>Red</span>: Inverse tendency (Long-Before-Short) (Score &lt; 0)</li>",
        "</ul></p>",
        "</div>"
    ]

    map_configs = [
        {
            "title": "1. Right SbL &beta; Slope",
            "desc": "Compliance with Short-Before-Long on the Right side.",
            "score_func": lambda row: row['R_Complex_Beta']
        },
        {
            "title": "2. Left SbL &beta; Slope (Inverted)",
            "desc": "Compliance with Short-Before-Long on the Left side. Left slopes are negated so Green means compliant.",
            "score_func": lambda row: -row['L_Complex_Beta']
        },
        {
            "title": "3. Joint Average SbL &beta;",
            "desc": "The average of the Right and (inverted) Left SbL &beta; slopes. Green indicates overall bilateral compliance.",
            "score_func": lambda row: (row['R_Complex_Beta'] - row['L_Complex_Beta']) / 2
        },
        {
            "title": "4. Right Horizontal Law Strict Compliance",
            "desc": "Percentage of verb dependencies that strictly obey the Right Horizontal Law. Mapped to the color scale such that &gt;60% is Green, and &lt;50% is Red.",
            "score_func": lambda row: (row['R_Horiz_Pct_Lt'] - 50) / 100
        }
    ]

    for config in map_configs:
        name2score = {}
        for _, row in df_std.iterrows():
            try:
                val = config['score_func'](row)
                if pd.notna(val):
                    name2score[row['Language']] = val
            except Exception:
                pass
                
        geo_copy = copy.deepcopy(geo_raw)
        for geo in geo_copy:
            lname = geo['name']
            if lname in name2score:
                geo['mal_score'] = name2score[lname]
            else:
                geo['mal_score'] = 0.0
                
        svg_map = _generate_svg_world_map(geo_copy)
        
        html.append(f"<h2>{config['title']}</h2>")
        html.append(f"<p>{config['desc']}</p>")
        html.append("<div style='max-width:1200px; margin: 0 auto; overflow-x: auto; border: 1px solid #ddd; margin-bottom: 40px; background: #fff;'>")
        html.append(svg_map)
        html.append("</div>")

    html.append(get_footer())
    
    with open(os.path.join(out_dir, "sbl_typology.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))

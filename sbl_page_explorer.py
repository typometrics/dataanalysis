import os
import numpy as np
import pandas as pd
from sbl_html_utils import get_header, get_nav, get_footer

def tsv_to_html_table(tsv_path):
    if not os.path.exists(tsv_path):
        return "<p><i>File not found.</i></p>"
    
    html = ["<table class='tsv-table border-table'>"]
    try:
        with open(tsv_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                parts = line.strip('\n').split('\t')
                tag = "th" if i == 0 else "td"
                html.append("<tr>")
                for p in parts:
                    html.append(f"<{tag}>{p}</{tag}>")
                html.append("</tr>")
        html.append("</table>")
    except Exception as e:
        return f"<p>Error loading TSV: {e}</p>"
        
    return "".join(html)

def generate(out_dir):
    csv_path = "data/sbl_laws_summary.csv"
    if not os.path.exists(csv_path):
        return
        
    df = pd.read_csv(csv_path)
    df_std = df[df['Table_Type'] == 'AnyOtherSide']
    
    html = [
        get_header("Interactive Explorer"),
        get_nav("sbl_explorer.html"),
        "<h1 title='Interactive tool for exploring raw Helix Tables and dependencies across all languages.'>Interactive SBL Explorer</h1>",
        "<div class='explanation'>",
        "<p>This module allows you to click on any language to expand its full raw Helix Table and AnyOtherSide Table.</p>",
        "</div>",
        "<table id='explorerTable'>",
        "<thead><tr>",
        "<th onclick=\"sortTable('explorerTable', 0, 'string')\">Language Name</th>",
        "<th onclick=\"sortTable('explorerTable', 1, 'string')\">Language Code</th>",
        "<th onclick=\"sortTable('explorerTable', 2, 'number')\" title='Geometric mean of right horizontal ratios'>Right Horiz GM</th>",
        "<th onclick=\"sortTable('explorerTable', 3, 'number')\" title='Geometric mean of left horizontal ratios'>Left Horiz GM</th>",
        "<th onclick=\"sortTable('explorerTable', 4, 'number')\" title='Weighted mean of < on right'>R &lt; %</th>",
        "<th onclick=\"sortTable('explorerTable', 5, 'number')\" title='Weighted mean of = on right'>R = %</th>",
        "<th onclick=\"sortTable('explorerTable', 6, 'number')\" title='Weighted mean of > on right'>R &gt; %</th>",
        "<th onclick=\"sortTable('explorerTable', 7, 'number')\" title='Weighted mean of < on left'>L &lt; %</th>",
        "<th onclick=\"sortTable('explorerTable', 8, 'number')\" title='Weighted mean of = on left'>L = %</th>",
        "<th onclick=\"sortTable('explorerTable', 9, 'number')\" title='Weighted mean of > on left'>L &gt; %</th>",
        "<th onclick=\"sortTable('explorerTable', 10, 'number')\" title='Geometric mean of right horizontal ratios / geometric mean of left horizontal ratios'>Horizontal Right-Left effect</th>",
        "<th onclick=\"sortTable('explorerTable', 11, 'number')\" title='Geometric mean of outer right ratios / remaining right horizontal ratios'>Right Outer Constituent Ratio Effect</th>",
        "<th onclick=\"sortTable('explorerTable', 12, 'number')\" title='Geometric mean of outer left ratios / remaining left horizontal ratios'>Left Outer Constituent Ratio Effect</th>",
        "<th onclick=\"sortTable('explorerTable', 13, 'string')\" title='Dominant Object-Verb Order'>OV Value</th>",
        "<th onclick=\"sortTable('explorerTable', 14, 'number')\" title='Head-Initiality Score'>Head-Initiality</th>",
        "<th>Outer Effects Graph</th>",
        "</tr></thead><tbody>"
    ]
    
    modals = []
    
    for _, row in df_std.iterrows():
        lang = row['Language']
        if '_' in lang:
            name, code = lang.rsplit('_', 1)
        else:
            name, code = lang, lang
            
        r_horiz_gm = row.get('R_Horiz_All_GM', np.nan)
        l_horiz_gm = row.get('L_Horiz_All_GM', np.nan)
        r_lt = row.get('R_Weighted_Lt', np.nan)
        r_eq = row.get('R_Weighted_Eq', np.nan)
        r_gt = row.get('R_Weighted_Gt', np.nan)
        l_lt = row.get('L_Weighted_Lt', np.nan)
        l_eq = row.get('L_Weighted_Eq', np.nan)
        l_gt = row.get('L_Weighted_Gt', np.nan)
        
        hrl_effect = row.get('Horizontal_Right_Left_Effect', np.nan)
        r_outer = row.get('R_Outer_Effect', np.nan)
        l_outer = row.get('L_Outer_Effect', np.nan)
        ov_val = row.get('ov_value', '-')
        head_init = row.get('head_initiality', np.nan)
        
        # Link to modal
        html.append("<tr>")
        html.append(f"<td class='lang-name'>{name}</td>")
        html.append(f"<td>{code}</td>")
        html.append(f"<td>{r_horiz_gm:.3f}</td>" if pd.notna(r_horiz_gm) else "<td>-</td>")
        html.append(f"<td>{l_horiz_gm:.3f}</td>" if pd.notna(l_horiz_gm) else "<td>-</td>")
        html.append(f"<td>{r_lt:.1f}</td>" if pd.notna(r_lt) else "<td>-</td>")
        html.append(f"<td>{r_eq:.1f}</td>" if pd.notna(r_eq) else "<td>-</td>")
        html.append(f"<td>{r_gt:.1f}</td>" if pd.notna(r_gt) else "<td>-</td>")
        html.append(f"<td>{l_lt:.1f}</td>" if pd.notna(l_lt) else "<td>-</td>")
        html.append(f"<td>{l_eq:.1f}</td>" if pd.notna(l_eq) else "<td>-</td>")
        html.append(f"<td>{l_gt:.1f}</td>" if pd.notna(l_gt) else "<td>-</td>")
        html.append(f"<td>{hrl_effect:.3f}</td>" if pd.notna(hrl_effect) else "<td>-</td>")
        html.append(f"<td>{r_outer:.3f}</td>" if pd.notna(r_outer) else "<td>-</td>")
        html.append(f"<td>{l_outer:.3f}</td>" if pd.notna(l_outer) else "<td>-</td>")
        html.append(f"<td>{ov_val}</td>" if pd.notna(ov_val) else "<td>-</td>")
        html.append(f"<td>{head_init:.3f}</td>" if pd.notna(head_init) else "<td>-</td>")
        plot_url = f"outer_plots/{code}_outer_effects.svg"
        html.append(f"<td><img src='{plot_url}' onclick=\"openModal('modal_{lang}')\" alt='{lang} Outer Effect Curves' style='width: 300px; height: auto; border: 1px solid #eee; cursor: pointer;' title='Click to open full analysis'></td>")
        html.append("</tr>")
        
        # Build modal content
        modals.append(f"<div id='modal_{lang}' class='modal'>")
        modals.append("<div class='modal-content'>")
        modals.append(f"<span class='close-modal' onclick=\"closeModal('modal_{lang}')\">&times;</span>")
        modals.append(f"<h2>{lang} Helix Analysis</h2>")
        
        # Add graph at the top of the modal
        modals.append(f"<div style='text-align: center; margin-bottom: 20px;'><img src='{plot_url}' alt='{lang} Outer Effect Curves' style='max-width: 100%; height: auto;'></div>")
        
        # AnyOtherSide TSV (placed first as requested)
        any_path = f"data/helix_tables/{lang}/Helix_{lang}_AnyOtherSide.tsv"
        modals.append("<h3>unconstrained on opposite side</h3>")
        modals.append(tsv_to_html_table(any_path))
        
        # Standard TSV
        std_path = f"data/helix_tables/{lang}/Helix_{lang}.tsv"
        modals.append("<h3>strict - nothing on opposite side</h3>")
        modals.append(tsv_to_html_table(std_path))
        
        modals.append("</div></div>")
        
    html.append("</tbody></table>")
    html.append("\n".join(modals))
    html.append("""
<script>
document.addEventListener('keydown', function(event) {
    if (event.key === "Escape") {
        var modals = document.getElementsByClassName('modal');
        for (var i = 0; i < modals.length; i++) {
            modals[i].style.display = "none";
        }
    }
});
</script>
""")
    html.append(get_footer())
    
    # We add a bit of inline CSS for the TSV table border specifically here
    css = """
<style>
.border-table { border: 1px solid #ddd; }
.border-table th { background: #f4f4f4; color: #333; position: static; }
.border-table td, .border-table th { border: 1px solid #ccc; text-align: right; }
.border-table td:first-child, .border-table th:first-child { text-align: left; font-weight: bold; }
</style>
"""
    # Insert CSS before closing head
    full_html = "\n".join(html).replace("</head>", f"{css}</head>")
    
    with open(os.path.join(out_dir, "sbl_explorer.html"), "w", encoding="utf-8") as f:
        f.write(full_html)

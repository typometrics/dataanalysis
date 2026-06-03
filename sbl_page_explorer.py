import os
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
    df_std = df[df['Table_Type'] == 'Standard']
    
    html = [
        get_header("Interactive Explorer"),
        get_nav("sbl_explorer.html"),
        "<h1>Interactive SBL Explorer</h1>",
        "<div class='explanation'>",
        "<p>This module allows you to click on any language to expand its full raw Helix Table and AnyOtherSide Table.</p>",
        "</div>",
        "<table id='explorerTable'>",
        "<thead><tr>",
        "<th onclick=\"sortTable('explorerTable', 0, 'string')\">Language Name</th>",
        "<th onclick=\"sortTable('explorerTable', 1, 'string')\">Language Code</th>",
        "<th onclick=\"sortTable('explorerTable', 2, 'number')\" title='Right SbL Slope Beta. Positive means Compliant.'>Right SbL $\\beta$</th>",
        "<th onclick=\"sortTable('explorerTable', 3, 'number')\" title='Left SbL Slope Beta. Negative means Compliant.'>Left SbL $\\beta$</th>",
        "<th>Outer Effects</th>",
        "<th>Action</th>",
        "</tr></thead><tbody>"
    ]
    
    modals = []
    
    for _, row in df_std.iterrows():
        lang = row['Language']
        if '_' in lang:
            name, code = lang.rsplit('_', 1)
        else:
            name, code = lang, lang
            
        beta_r = row['R_Complex_Beta']
        beta_l = row['L_Complex_Beta']
        
        # Link to modal
        html.append("<tr>")
        html.append(f"<td class='lang-name'>{name}</td>")
        html.append(f"<td>{code}</td>")
        html.append(f"<td>{beta_r:.3f}</td>" if pd.notna(beta_r) else "<td>-</td>")
        html.append(f"<td>{beta_l:.3f}</td>" if pd.notna(beta_l) else "<td>-</td>")
        plot_url = f"outer_plots/{code}_outer_effects.svg"
        html.append(f"<td><a href='{plot_url}' target='_blank'><img src='{plot_url}' alt='{lang} Outer Effect Curves' style='width: 300px; height: auto; border: 1px solid #eee;' title='Click to enlarge'></a></td>")
        html.append(f"<td><button onclick=\"openModal('modal_{lang}')\" style='cursor:pointer; padding: 4px 8px;'>View Raw TSVs</button></td>")
        html.append("</tr>")
        
        # Build modal content
        modals.append(f"<div id='modal_{lang}' class='modal'>")
        modals.append("<div class='modal-content'>")
        modals.append(f"<span class='close-modal' onclick=\"closeModal('modal_{lang}')\">&times;</span>")
        modals.append(f"<h2>{lang} Helix Analysis</h2>")
        
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

import os
import pandas as pd
from compute_sbl_laws import parse_helix_tsv
from sbl_html_utils import get_header, get_nav, get_footer

def _check(lang, law, expr, v1, v2, pval=None):
    v1_js = "null" if v1 is None else str(v1)
    v2_js = "null" if v2 is None else str(v2)
    pval_js = "null" if pd.isna(pval) or pval is None else f"{pval:.4e}"
    onclick = f"onclick=\"showDetails('{lang}', '{law}', '{expr}', {v1_js}, {v2_js}, {pval_js})\" style='cursor:pointer;'"
    
    if v1 is None or v2 is None or v2 == 0:
        return f"<td class='na-cell' {onclick}>-</td>"
        
    ratio = v1 / v2
    if ratio < 1.0:
        op = max(0.15, 1.0 - ratio)
        bg = f"rgba(76, 175, 80, {op:.2f})"
        color = "#000" if op < 0.6 else "#fff"
    else:
        op = min(1.0, max(0.15, (ratio - 1.0)))
        bg = f"rgba(244, 67, 54, {op:.2f})"
        color = "#000" if op < 0.6 else "#fff"
        
    return f"<td style='background-color:{bg}; color:{color}; text-align:center;' {onclick}>{ratio:.2f}</td>"

def get_val(d, n, k):
    if n in d and 'sizes' in d[n] and k in d[n]['sizes']:
        return d[n]['sizes'][k]
    return None

def generate(out_dir):
    csv_path = "data/sbl_laws_summary.csv"
    if not os.path.exists(csv_path):
        return
        
    df = pd.read_csv(csv_path)
    df_std = df[df['Table_Type'] == 'AnyOtherSide']
    
    html = [
        get_header("Validation & Diagnostics"),
        get_nav("sbl_validation.html"),
        "<h1 title='Diagnostics on N-sizes, empty fields, and statistical validity across languages.'>Validation & Diagnostics</h1>",
        "<div class='explanation'>",
        "<p>This table provides a transparent, step-by-step trace of how the Sy Laws are scored for all languages (Right Side, Standard Table). Each column represents one of the specific pair comparisons required by the laws.</p>",
        "</div>",
        "<h3>Legend</h3>",
        "<ul>",
        "<li><strong>H1-H6 (Horizontal):</strong> 1: $R_2^1 < R_2^2$, 2: $R_3^1 < R_3^2$, 3: $R_3^2 < R_3^3$, 4: $R_4^1 < R_4^2$, 5: $R_4^2 < R_4^3$, 6: $R_4^3 < R_4^4$</li>",
        "<li><strong>V1-V6 (Vertical):</strong> 1: $R_2^1 < R_1^1$, 2: $R_3^1 < R_2^1$, 3: $R_4^1 < R_3^1$, 4: $R_3^2 < R_2^2$, 5: $R_4^2 < R_3^2$, 6: $R_4^3 < R_3^3$</li>",
        "<li><strong>D1-D6 (Diagonal):</strong> 1: $R_1^1 < R_2^2$, 2: $R_2^2 < R_3^3$, 3: $R_3^3 < R_4^4$, 4: $R_2^1 < R_3^2$, 5: $R_3^2 < R_4^3$, 6: $R_3^1 < R_4^2$</li>",
        "</ul>",
        "<div id='detailsModal' class='modal'>",
        "  <div class='modal-content'>",
        "    <span class='close-modal' onclick=\"closeModal('detailsModal')\">&times;</span>",
        "    <h2 id='modalLang'></h2>",
        "    <p><strong id='modalLaw'></strong></p>",
        "    <p>Rule: <span id='modalExpr' class='formula'></span></p>",
        "    <p>Values: <span id='modalValues'></span></p>",
        "    <p>Result: <span id='modalResult'></span><span id='modalSig'></span></p>",
        "  </div>",
        "</div>",
        "<script>",
        "function showDetails(lang, law, expr, v1, v2, pval) {",
        "    document.getElementById('modalLang').innerText = 'Language: ' + lang;",
        "    document.getElementById('modalLaw').innerText = 'Law: ' + law;",
        "    document.getElementById('modalExpr').innerText = expr;",
        "    let v1str = v1 === null ? 'N/A' : v1.toFixed(3);",
        "    let v2str = v2 === null ? 'N/A' : v2.toFixed(3);",
        "    document.getElementById('modalValues').innerText = v1str + ' vs ' + v2str;",
        "    let resObj = document.getElementById('modalResult');",
        "    if (v1 === null || v2 === null) {",
        "        resObj.innerText = '-';",
        "        resObj.style.color = 'gray';",
        "    } else if (v1 < v2) {",
        "        resObj.innerText = '✅ PASS (' + v1str + ' < ' + v2str + ')';",
        "        resObj.style.color = 'green';",
        "    } else {",
        "        resObj.innerText = '❌ FAIL (' + v1str + ' >= ' + v2str + ')';",
        "        resObj.style.color = 'red';",
        "    }",
        "    let sigObj = document.getElementById('modalSig');",
        "    if (pval !== null) {",
        "        if (pval < 0.001) sigObj.innerText = ' *** (p=' + pval + ')';",
        "        else if (pval < 0.01) sigObj.innerText = ' ** (p=' + pval + ')';",
        "        else if (pval < 0.05) sigObj.innerText = ' * (p=' + pval + ')';",
        "        else sigObj.innerText = ' ns (p=' + pval + ')';",
        "        sigObj.style.fontWeight = 'bold';",
        "    } else {",
        "        sigObj.innerText = '';",
        "    }",
        "    openModal('detailsModal');",
        "}",
        "</script>"
    ]

    fr_tsv = "data/helix_tables/French_fr/Helix_French_fr.tsv"
    if os.path.exists(fr_tsv):
        fdata = parse_helix_tsv(fr_tsv)
        if fdata and 'R' in fdata:
            d_fr = fdata['R']
            def val(n, k): return get_val(d_fr, n, k)
            def _check_fr(v1, v2):
                if v1 is None or v2 is None: return "<td>-</td>"
                if v1 < v2: return f"<td style='color:green;'>✅ PASS ({v1:.3f} &lt; {v2:.3f})</td>"
                return f"<td style='color:red;'>❌ FAIL ({v1:.3f} &ge; {v2:.3f})</td>"
            
            html.extend([
                "<h3>Example: French (Right Side)</h3>",
                "<table style='width: auto; margin-bottom: 30px;'>",
                "<tr><th>Law</th><th>Rule</th><th>Values</th><th>Result</th></tr>",
                f"<tr><td>Horizontal 1</td><td>$R_2^1 < R_2^2$</td><td>{val(2,1):.3f} vs {val(2,2):.3f}</td>{_check_fr(val(2,1), val(2,2))}</tr>",
                f"<tr><td>Horizontal 2</td><td>$R_3^1 < R_3^2$</td><td>{val(3,1):.3f} vs {val(3,2):.3f}</td>{_check_fr(val(3,1), val(3,2))}</tr>",
                f"<tr><td>Horizontal 3</td><td>$R_3^2 < R_3^3$</td><td>{val(3,2):.3f} vs {val(3,3):.3f}</td>{_check_fr(val(3,2), val(3,3))}</tr>",
                f"<tr><td>Vertical 1</td><td>$R_2^1 < R_1^1$</td><td>{val(2,1):.3f} vs {val(1,1):.3f}</td>{_check_fr(val(2,1), val(1,1))}</tr>",
                f"<tr><td>Vertical 2</td><td>$R_3^1 < R_2^1$</td><td>{val(3,1):.3f} vs {val(2,1):.3f}</td>{_check_fr(val(3,1), val(2,1))}</tr>",
                f"<tr><td>Diagonal 1</td><td>$R_1^1 < R_2^2$</td><td>{val(1,1):.3f} vs {val(2,2):.3f}</td>{_check_fr(val(1,1), val(2,2))}</tr>",
                "</table>",
                "<h3>Global Matrix (All Languages)</h3>"
            ])

    html.extend([
        "<div style='overflow-x:auto;'>",
        "<table id='validationTable' style='white-space: nowrap;'>",
        "<thead>",
        "<tr>",
        "<th onclick=\"sortTable('validationTable', 0, 'string')\" style='background:#4CAF50; color:white; cursor:pointer;' title='Sort by Language'>Language</th>"
    ])
    
    # H1-H6
    h_titles_r = ["R_2^1 < R_2^2", "R_3^1 < R_3^2", "R_3^2 < R_3^3", "R_4^1 < R_4^2", "R_4^2 < R_4^3", "R_4^3 < R_4^4"]
    v_titles_r = ["R_2^1 < R_1^1", "R_3^1 < R_2^1", "R_4^1 < R_3^1", "R_3^2 < R_2^2", "R_4^2 < R_3^2", "R_4^3 < R_3^3"]
    d_titles_r = ["R_1^1 < R_2^2", "R_2^2 < R_3^3", "R_3^3 < R_4^4", "R_2^1 < R_3^2", "R_3^2 < R_4^3", "R_3^1 < R_4^2"]
    
    col_idx = 1
    for i in range(1, 7): 
        html.append(f"<th onclick=\"sortTable('validationTable', {col_idx}, 'number')\" style='background:#c8e6c9; color:#333; cursor:pointer;' title='Horizontal {i}: {h_titles_r[i-1]}'>H{i}</th>")
        col_idx += 1
    for i in range(1, 7): 
        html.append(f"<th onclick=\"sortTable('validationTable', {col_idx}, 'number')\" style='background:#bbdefb; color:#333; cursor:pointer;' title='Vertical {i}: {v_titles_r[i-1]}'>V{i}</th>")
        col_idx += 1
    for i in range(1, 7): 
        html.append(f"<th onclick=\"sortTable('validationTable', {col_idx}, 'number')\" style='background:#ffe0b2; color:#333; cursor:pointer;' title='Diagonal {i}: {d_titles_r[i-1]}'>D{i}</th>")
        col_idx += 1
    
    html.append("</tr></thead><tbody>")
    
    for _, row in df_std.iterrows():
        lang = row['Language']
        tsv_path = f"data/helix_tables/{lang}/Helix_{lang}.tsv"
        
        if '_' in lang:
            name, code = lang.rsplit('_', 1)
        else:
            name, code = lang, lang
            
        if not os.path.exists(tsv_path):
            continue
            
        data = parse_helix_tsv(tsv_path)
        if not data:
            continue
            
        d = data['R']
        
        html.append("<tr>")
        html.append(f"<td class='lang-name'>{name}</td>")
        
        # Parse Horiz_Pvals
        r_pvals_str = str(row.get('R_Horiz_Pvals', '')) if pd.notna(row.get('R_Horiz_Pvals')) else ''
        r_pvals = [float(p) for p in r_pvals_str.split('|') if p] if r_pvals_str else []
        def get_pval(lst, idx): return lst[idx] if idx < len(lst) else None
        
        # Horizontal
        html.append(_check(name, 'Horizontal 1', 'R_2^1 < R_2^2', get_val(d,2,1), get_val(d,2,2), get_pval(r_pvals, 0)))
        html.append(_check(name, 'Horizontal 2', 'R_3^1 < R_3^2', get_val(d,3,1), get_val(d,3,2), get_pval(r_pvals, 1)))
        html.append(_check(name, 'Horizontal 3', 'R_3^2 < R_3^3', get_val(d,3,2), get_val(d,3,3), get_pval(r_pvals, 2)))
        html.append(_check(name, 'Horizontal 4', 'R_4^1 < R_4^2', get_val(d,4,1), get_val(d,4,2), get_pval(r_pvals, 3)))
        html.append(_check(name, 'Horizontal 5', 'R_4^2 < R_4^3', get_val(d,4,2), get_val(d,4,3), get_pval(r_pvals, 4)))
        html.append(_check(name, 'Horizontal 6', 'R_4^3 < R_4^4', get_val(d,4,3), get_val(d,4,4), get_pval(r_pvals, 5)))
        
        # Vertical
        html.append(_check(name, 'Vertical 1', 'R_2^1 < R_1^1', get_val(d,2,1), get_val(d,1,1)))
        html.append(_check(name, 'Vertical 2', 'R_3^1 < R_2^1', get_val(d,3,1), get_val(d,2,1)))
        html.append(_check(name, 'Vertical 3', 'R_4^1 < R_3^1', get_val(d,4,1), get_val(d,3,1)))
        html.append(_check(name, 'Vertical 4', 'R_3^2 < R_2^2', get_val(d,3,2), get_val(d,2,2)))
        html.append(_check(name, 'Vertical 5', 'R_4^2 < R_3^2', get_val(d,4,2), get_val(d,3,2)))
        html.append(_check(name, 'Vertical 6', 'R_4^3 < R_3^3', get_val(d,4,3), get_val(d,3,3)))
        
        # Diagonal
        html.append(_check(name, 'Diagonal 1', 'R_1^1 < R_2^2', get_val(d,1,1), get_val(d,2,2)))
        html.append(_check(name, 'Diagonal 2', 'R_2^2 < R_3^3', get_val(d,2,2), get_val(d,3,3)))
        html.append(_check(name, 'Diagonal 3', 'R_3^3 < R_4^4', get_val(d,3,3), get_val(d,4,4)))
        html.append(_check(name, 'Diagonal 4', 'R_2^1 < R_3^2', get_val(d,2,1), get_val(d,3,2)))
        html.append(_check(name, 'Diagonal 5', 'R_3^2 < R_4^3', get_val(d,3,2), get_val(d,4,3)))
        html.append(_check(name, 'Diagonal 6', 'R_3^1 < R_4^2', get_val(d,3,1), get_val(d,4,2)))
        
        html.append("</tr>")
        
    html.append("</tbody></table></div>")
    
    # --- Left Side French Example ---
    if os.path.exists(fr_tsv):
        if fdata and 'L' in fdata:
            d_fr_l = fdata['L']
            def val_l(n, k): return get_val(d_fr_l, n, k)
            def _check_fr_l(v1, v2):
                if v1 is None or v2 is None: return "<td>-</td>"
                if v1 < v2: return f"<td style='color:green;'>✅ PASS ({v1:.3f} &lt; {v2:.3f})</td>"
                return f"<td style='color:red;'>❌ FAIL ({v1:.3f} &ge; {v2:.3f})</td>"
            
            html.extend([
                "<h3>Example: French (Left Side)</h3>",
                "<table style='width: auto; margin-bottom: 30px;'>",
                "<tr><th>Law</th><th>Rule</th><th>Values</th><th>Result</th></tr>",
                f"<tr><td>Horizontal 1</td><td>$L_2^1 < L_2^2$</td><td>{val_l(2,1):.3f} vs {val_l(2,2):.3f}</td>{_check_fr_l(val_l(2,1), val_l(2,2))}</tr>",
                f"<tr><td>Horizontal 2</td><td>$L_3^1 < L_3^2$</td><td>{val_l(3,1):.3f} vs {val_l(3,2):.3f}</td>{_check_fr_l(val_l(3,1), val_l(3,2))}</tr>",
                f"<tr><td>Horizontal 3</td><td>$L_3^2 < L_3^3$</td><td>{val_l(3,2):.3f} vs {val_l(3,3):.3f}</td>{_check_fr_l(val_l(3,2), val_l(3,3))}</tr>",
                f"<tr><td>Vertical 1</td><td>$L_2^1 < L_1^1$</td><td>{val_l(2,1):.3f} vs {val_l(1,1):.3f}</td>{_check_fr_l(val_l(2,1), val_l(1,1))}</tr>",
                f"<tr><td>Vertical 2</td><td>$L_3^1 < L_2^1$</td><td>{val_l(3,1):.3f} vs {val_l(2,1):.3f}</td>{_check_fr_l(val_l(3,1), val_l(2,1))}</tr>",
                f"<tr><td>Diagonal 1</td><td>$L_1^1 < L_2^2$</td><td>{val_l(1,1):.3f} vs {val_l(2,2):.3f}</td>{_check_fr_l(val_l(1,1), val_l(2,2))}</tr>",
                "</table>"
            ])

    # --- Left Side Matrix ---
    html.extend([
        "<h3 style='margin-top: 40px;'>Global Matrix (Left Side)</h3>",
        "<div style='overflow-x:auto;'>",
        "<table id='validationTableLeft' style='white-space: nowrap;'>",
        "<thead>",
        "<tr>",
        "<th onclick=\"sortTable('validationTableLeft', 0, 'string')\" style='background:#4CAF50; color:white; cursor:pointer;' title='Sort by Language'>Language</th>"
    ])
    
    h_titles_l = ["L_2^1 < L_2^2", "L_3^1 < L_3^2", "L_3^2 < L_3^3", "L_4^1 < L_4^2", "L_4^2 < L_4^3", "L_4^3 < L_4^4"]
    v_titles_l = ["L_2^1 < L_1^1", "L_3^1 < L_2^1", "L_4^1 < L_3^1", "L_3^2 < L_2^2", "L_4^2 < L_3^2", "L_4^3 < L_3^3"]
    d_titles_l = ["L_1^1 < L_2^2", "L_2^2 < L_3^3", "L_3^3 < L_4^4", "L_2^1 < L_3^2", "L_3^2 < L_4^3", "L_3^1 < L_4^2"]
    
    col_idx = 1
    for i in range(1, 7): 
        html.append(f"<th onclick=\"sortTable('validationTableLeft', {col_idx}, 'number')\" style='background:#c8e6c9; color:#333; cursor:pointer;' title='Horizontal {i}: {h_titles_l[i-1]}'>H{i}</th>")
        col_idx += 1
    for i in range(1, 7): 
        html.append(f"<th onclick=\"sortTable('validationTableLeft', {col_idx}, 'number')\" style='background:#bbdefb; color:#333; cursor:pointer;' title='Vertical {i}: {v_titles_l[i-1]}'>V{i}</th>")
        col_idx += 1
    for i in range(1, 7): 
        html.append(f"<th onclick=\"sortTable('validationTableLeft', {col_idx}, 'number')\" style='background:#ffe0b2; color:#333; cursor:pointer;' title='Diagonal {i}: {d_titles_l[i-1]}'>D{i}</th>")
        col_idx += 1
    
    html.append("</tr></thead><tbody>")
    
    for _, row in df_std.iterrows():
        lang = row['Language']
        tsv_path = f"data/helix_tables/{lang}/Helix_{lang}.tsv"
        
        if '_' in lang:
            name, code = lang.rsplit('_', 1)
        else:
            name, code = lang, lang
            
        if not os.path.exists(tsv_path):
            continue
            
        data = parse_helix_tsv(tsv_path)
        if not data or 'L' not in data:
            continue
            
        d = data['L']
        
        html.append("<tr>")
        html.append(f"<td class='lang-name'>{name}</td>")
        
        l_pvals_str = str(row.get('L_Horiz_Pvals', '')) if pd.notna(row.get('L_Horiz_Pvals')) else ''
        l_pvals = [float(p) for p in l_pvals_str.split('|') if p] if l_pvals_str else []
        
        # Horizontal
        html.append(_check(name, 'Left Horizontal 1', 'L_2^1 < L_2^2', get_val(d,2,1), get_val(d,2,2), get_pval(l_pvals, 0)))
        html.append(_check(name, 'Left Horizontal 2', 'L_3^1 < L_3^2', get_val(d,3,1), get_val(d,3,2), get_pval(l_pvals, 1)))
        html.append(_check(name, 'Left Horizontal 3', 'L_3^2 < L_3^3', get_val(d,3,2), get_val(d,3,3), get_pval(l_pvals, 2)))
        html.append(_check(name, 'Left Horizontal 4', 'L_4^1 < L_4^2', get_val(d,4,1), get_val(d,4,2), get_pval(l_pvals, 3)))
        html.append(_check(name, 'Left Horizontal 5', 'L_4^2 < L_4^3', get_val(d,4,2), get_val(d,4,3), get_pval(l_pvals, 4)))
        html.append(_check(name, 'Left Horizontal 6', 'L_4^3 < L_4^4', get_val(d,4,3), get_val(d,4,4), get_pval(l_pvals, 5)))
        
        # Vertical
        html.append(_check(name, 'Left Vertical 1', 'L_2^1 < L_1^1', get_val(d,2,1), get_val(d,1,1)))
        html.append(_check(name, 'Left Vertical 2', 'L_3^1 < L_2^1', get_val(d,3,1), get_val(d,2,1)))
        html.append(_check(name, 'Left Vertical 3', 'L_4^1 < L_3^1', get_val(d,4,1), get_val(d,3,1)))
        html.append(_check(name, 'Left Vertical 4', 'L_3^2 < L_2^2', get_val(d,3,2), get_val(d,2,2)))
        html.append(_check(name, 'Left Vertical 5', 'L_4^2 < L_3^2', get_val(d,4,2), get_val(d,3,2)))
        html.append(_check(name, 'Left Vertical 6', 'L_4^3 < L_3^3', get_val(d,4,3), get_val(d,3,3)))
        
        # Diagonal
        html.append(_check(name, 'Left Diagonal 1', 'L_1^1 < L_2^2', get_val(d,1,1), get_val(d,2,2)))
        html.append(_check(name, 'Left Diagonal 2', 'L_2^2 < L_3^3', get_val(d,2,2), get_val(d,3,3)))
        html.append(_check(name, 'Left Diagonal 3', 'L_3^3 < L_4^4', get_val(d,3,3), get_val(d,4,4)))
        html.append(_check(name, 'Left Diagonal 4', 'L_2^1 < L_3^2', get_val(d,2,1), get_val(d,3,2)))
        html.append(_check(name, 'Left Diagonal 5', 'L_3^2 < L_4^3', get_val(d,3,2), get_val(d,4,3)))
        html.append(_check(name, 'Left Diagonal 6', 'L_3^1 < L_4^2', get_val(d,3,1), get_val(d,4,2)))
        
        html.append("</tr>")
        
    html.append("</tbody></table></div>")

    html.append(get_footer())
    
    with open(os.path.join(out_dir, "sbl_validation.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))

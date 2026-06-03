import os
import pandas as pd
from sbl_html_utils import get_header, get_nav, get_footer

def _fmt(val):
    if pd.isna(val): return "-"
    return f"{val:.3f}"

def _sig_stars(pval):
    if pd.isna(pval): return ""
    if pval < 0.001: return "***"
    if pval < 0.01: return "**"
    if pval < 0.05: return "*"
    return ""

def _fmt_beta(beta, pval):
    if pd.isna(beta): return "-"
    return f"{beta:.3f}<sup>{_sig_stars(pval)}</sup>"

def _fmt_pct(val):
    if pd.isna(val): return "-"
    return f"{val:.1f}%"

def generate(out_dir):
    csv_path = "data/sbl_laws_summary.csv"
    if not os.path.exists(csv_path):
        print("Warning: CSV not found for compliance page.")
        return
        
    df = pd.read_csv(csv_path)
    # Filter to Standard table for default view
    df = df[df['Table_Type'] == 'Standard']
    
    html = [
        get_header("SBL Laws Compliance Master Table"),
        get_nav("sbl_laws_compliance.html"),
        "<h1>SBL Laws Compliance</h1>",
        "<p>This table displays the computed compliance for the Horizontal, Vertical, and Diagonal laws up to $n=4$ across all languages (using Standard Helix configurations).</p>",
        "<div class='explanation'>",
        "<p><strong>Left Side Compliance:</strong> For the Left side of the verb, \"Short-Before-Long\" implies that dependents further from the verb (which occur earlier in the sentence) should be shorter than those closer to the verb. Because distance is measured outward from the verb, a perfectly compliant Short-Before-Long language will show decreasing size as distance increases, resulting in a <strong>negative slope</strong> ($\\beta$). Thus, left slopes are naturally negative when compliant, so Green means compliant.</p>",
        "<p><strong>Significance (OLS P-value):</strong> SbL $\\beta$ values are marked with <code>***</code> ($p<0.001$), <code>**</code> ($p<0.01$), or <code>*</code> ($p<0.05$).</p>",
        "</div>",
        "<p>Click on any column header to sort the table.</p>",
        "<table id='complianceTable'>",
        "<thead><tr>",
        "<th onclick=\"sortTable('complianceTable', 0, 'string')\">Language Name</th>",
        "<th onclick=\"sortTable('complianceTable', 1, 'string')\">Language Code</th>",
        "<th onclick=\"sortTable('complianceTable', 2, 'string')\">Examples</th>",
        "<th onclick=\"sortTable('complianceTable', 3, 'number')\" title='Right Horizontal Score out of 6 pairs'>Right H-Score (/6)</th>",
        "<th onclick=\"sortTable('complianceTable', 4, 'number')\" title='Right Vertical Score out of 6 pairs'>Right V-Score (/6)</th>",
        "<th onclick=\"sortTable('complianceTable', 5, 'number')\" title='Right Diagonal Score out of 6 pairs'>Right D-Score (/6)</th>",
        "<th onclick=\"sortTable('complianceTable', 6, 'number')\" title='Right SbL Slope Beta. Positive means Compliant.'>Right SbL $\\beta$</th>",
        "<th onclick=\"sortTable('complianceTable', 7, 'number')\" title='Left Horizontal Score out of 6 pairs'>Left H-Score (/6)</th>",
        "<th onclick=\"sortTable('complianceTable', 8, 'number')\" title='Left Vertical Score out of 6 pairs'>Left V-Score (/6)</th>",
        "<th onclick=\"sortTable('complianceTable', 9, 'number')\" title='Left Diagonal Score out of 6 pairs'>Left D-Score (/6)</th>",
        "<th onclick=\"sortTable('complianceTable', 10, 'number')\" title='Left SbL Slope Beta. Negative means Compliant.'>Left SbL $\\beta$</th>",
        "</tr></thead><tbody>"
    ]
    
    for _, row in df.iterrows():
        lang = row['Language']
        if '_' in lang:
            name, code = lang.rsplit('_', 1)
        else:
            name, code = lang, lang
            
        html.append("<tr>")
        html.append(f"<td class='lang-name'>{name}</td>")
        html.append(f"<td>{code}</td>")
        html.append(f"<td><a href='examples/{code}/index.html' target='_blank' style='text-decoration:none' title='View Sample Sentences'>📄</a></td>")
        html.append(f"<td>{row['R_Horiz_Score']}</td>" if pd.notna(row['R_Horiz_Score']) else "<td class='na-cell'>-</td>")
        html.append(f"<td>{row['R_Vert_Score']}</td>" if pd.notna(row['R_Vert_Score']) else "<td class='na-cell'>-</td>")
        html.append(f"<td>{row['R_Diag_Score']}</td>" if pd.notna(row['R_Diag_Score']) else "<td class='na-cell'>-</td>")
        
        beta_r = row['R_Complex_Beta']
        pval_r = row.get('R_Complex_Pval', float('nan'))
        cls_r = 'score-positive' if pd.notna(beta_r) and beta_r > 0.1 else ('score-negative' if pd.notna(beta_r) and beta_r < -0.1 else 'score-neutral')
        html.append(f"<td class='{cls_r}' title='p={pval_r:.4f}'><strong>{_fmt_beta(beta_r, pval_r)}</strong></td>" if pd.notna(beta_r) else "<td class='na-cell'>-</td>")
        
        html.append(f"<td>{row['L_Horiz_Score']}</td>" if pd.notna(row['L_Horiz_Score']) else "<td class='na-cell'>-</td>")
        html.append(f"<td>{row['L_Vert_Score']}</td>" if pd.notna(row['L_Vert_Score']) else "<td class='na-cell'>-</td>")
        html.append(f"<td>{row['L_Diag_Score']}</td>" if pd.notna(row['L_Diag_Score']) else "<td class='na-cell'>-</td>")
        
        beta_l = row['L_Complex_Beta']
        pval_l = row.get('L_Complex_Pval', float('nan'))
        cls_l = 'score-positive' if pd.notna(beta_l) and beta_l < -0.1 else ('score-negative' if pd.notna(beta_l) and beta_l > 0.1 else 'score-neutral')
        html.append(f"<td class='{cls_l}' title='p={pval_l:.4f}'><strong>{_fmt_beta(beta_l, pval_l)}</strong></td>" if pd.notna(beta_l) else "<td class='na-cell'>-</td>")
        html.append("</tr>")
        
    html.append("</tbody></table>")
    html.append(get_footer())
    
    with open(os.path.join(out_dir, "sbl_laws_compliance.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))

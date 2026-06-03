import os
import pandas as pd
import numpy as np
from sbl_html_utils import get_header, get_nav, get_footer

def _sig_stars(pval):
    if pd.isna(pval): return ""
    if pval < 0.001: return "***"
    if pval < 0.01: return "**"
    if pval < 0.05: return "*"
    return "ns"

def generate(out_dir):
    csv_path = "data/sbl_laws_summary.csv"
    if not os.path.exists(csv_path):
        return
        
    df = pd.read_csv(csv_path)
    df_std = df[df['Table_Type'] == 'Standard']
    
    html = [
        get_header("SBL Significance Analysis"),
        get_nav("sbl_significance.html"),
        "<h1>Significance Analysis of SBL Results</h1>",
        "<p>This page presents statistical significance tests for the different SBL compliance metrics, demonstrating that the observed trends are not merely artifacts of sample size.</p>",
        
        "<h2>1. OLS Regression of the Complex SbL $\\beta$</h2>",
        "<div class='explanation'>",
        "<p><strong>What is measured:</strong> We perform an Ordinary Least Squares (OLS) linear regression of the log-constituent size against the log-distance from the verb (the SbL $\\beta$ slope).</p>",
        "<p><strong>Why it matters:</strong> A slope $\\beta$ might appear compliant, but if the sample size is too small or the variance too high, it might just be noise. The $p$-value tests the null hypothesis that $\\beta = 0$ (distance has no effect on size). A significant $p$-value confirms a robust Short-Before-Long (or Long-Before-Short) effect.</p>",
        "<p><strong>Significance Levels:</strong> <code>***</code> $p<0.001$, <code>**</code> $p<0.01$, <code>*</code> $p<0.05$, <code>ns</code> Not Significant.</p>",
        "</div>",
        
        "<table id='sigTableBeta'>",
        "<thead><tr>",
        "<th onclick=\"sortTable('sigTableBeta', 0, 'string')\">Language</th>",
        "<th onclick=\"sortTable('sigTableBeta', 1, 'number')\">Right SbL $\\beta$</th>",
        "<th onclick=\"sortTable('sigTableBeta', 2, 'number')\">Right $p$-value</th>",
        "<th onclick=\"sortTable('sigTableBeta', 3, 'string')\">Right Sig.</th>",
        "<th onclick=\"sortTable('sigTableBeta', 4, 'number')\">Left SbL $\\beta$</th>",
        "<th onclick=\"sortTable('sigTableBeta', 5, 'number')\">Left $p$-value</th>",
        "<th onclick=\"sortTable('sigTableBeta', 6, 'string')\">Left Sig.</th>",
        "</tr></thead><tbody>"
    ]
    
    html_horiz = [
        "<h2>2. Binomial Test for Intra-Sentence Ordering (Horizontal Law)</h2>",
        "<div class='explanation'>",
        "<p><strong>What is measured:</strong> We perform a two-sided Binomial test (Sign Test) on the raw sentence-level counts. For adjacent dependents in the same sentence, we count how often the inner dependent is shorter than the outer dependent (successes) out of all sentences where their lengths differ (trials).</p>",
        "<p><strong>Why it matters:</strong> The Horizontal Law states that dependents closer to the verb are shorter. By testing the paired intra-sentence occurrences directly, we prove that this effect is highly significant and not just a product of aggregate averages.</p>",
        "<p><strong>Significance Levels:</strong> <code>***</code> $p<0.001$, <code>**</code> $p<0.01$, <code>*</code> $p<0.05$, <code>ns</code> Not Significant.</p>",
        "</div>",
        
        "<table id='sigTableHoriz'>",
        "<thead><tr>",
        "<th onclick=\"sortTable('sigTableHoriz', 0, 'string')\">Language</th>",
        "<th onclick=\"sortTable('sigTableHoriz', 1, 'number')\">Right H-Score (/6)</th>",
        "<th onclick=\"sortTable('sigTableHoriz', 2, 'number')\">Right % Significant Pairs</th>",
        "<th onclick=\"sortTable('sigTableHoriz', 3, 'number')\">Left H-Score (/6)</th>",
        "<th onclick=\"sortTable('sigTableHoriz', 4, 'number')\">Left % Significant Pairs</th>",
        "</tr></thead><tbody>"
    ]
    
    html_vert = [
        "<h2>3. Welch's t-test for Vertical Law</h2>",
        "<div class='explanation'>",
        "<p><strong>What is measured:</strong> We perform Welch's t-test to compare the log-transformed sizes of constituents at the same syntactic depth but belonging to different total lengths. For instance, comparing the size of $R^2$ in a 3-dependent sequence ($R_3^2$) against $R^2$ in a 2-dependent sequence ($R_2^2$).</p>",
        "<p><strong>Why it matters:</strong> The Vertical Law states that as the total number of dependents grows, the size of a dependent at a fixed position shrinks ($R_{n+1}^k < R_n^k$). The Welch's t-test assesses whether the mean log-sizes of these populations are significantly different, accounting for unequal variances and sample sizes.</p>",
        "<p><strong>Significance Levels:</strong> <code>***</code> $p<0.001$, <code>**</code> $p<0.01$, <code>*</code> $p<0.05$, <code>ns</code> Not Significant.</p>",
        "</div>",
        
        "<table id='sigTableVert'>",
        "<thead><tr>",
        "<th onclick=\"sortTable('sigTableVert', 0, 'string')\">Language</th>",
        "<th onclick=\"sortTable('sigTableVert', 1, 'number')\">Right V-Score (/6)</th>",
        "<th onclick=\"sortTable('sigTableVert', 2, 'number')\">Right % Significant Pairs</th>",
        "<th onclick=\"sortTable('sigTableVert', 3, 'number')\">Left V-Score (/6)</th>",
        "<th onclick=\"sortTable('sigTableVert', 4, 'number')\">Left % Significant Pairs</th>",
        "</tr></thead><tbody>"
    ]
    
    html_diag = [
        "<h2>4. Welch's t-test for Diagonal Law</h2>",
        "<div class='explanation'>",
        "<p><strong>What is measured:</strong> We perform Welch's t-test to compare the log-transformed sizes along the diagonal ($R_n^k$ vs $R_{n+1}^{k+1}$). For instance, comparing the size of $R_2^1$ against $R_3^2$.</p>",
        "<p><strong>Why it matters:</strong> The Diagonal Law dictates $R_n^k < R_{n+1}^{k+1}$. This test validates whether the observed growth along this diagonal dimension is statistically robust across sentences of different lengths.</p>",
        "<p><strong>Significance Levels:</strong> <code>***</code> $p<0.001$, <code>**</code> $p<0.01$, <code>*</code> $p<0.05$, <code>ns</code> Not Significant.</p>",
        "</div>",
        
        "<table id='sigTableDiag'>",
        "<thead><tr>",
        "<th onclick=\"sortTable('sigTableDiag', 0, 'string')\">Language</th>",
        "<th onclick=\"sortTable('sigTableDiag', 1, 'number')\">Right D-Score (/6)</th>",
        "<th onclick=\"sortTable('sigTableDiag', 2, 'number')\">Right % Significant Pairs</th>",
        "<th onclick=\"sortTable('sigTableDiag', 3, 'number')\">Left D-Score (/6)</th>",
        "<th onclick=\"sortTable('sigTableDiag', 4, 'number')\">Left % Significant Pairs</th>",
        "</tr></thead><tbody>"
    ]
    
    for _, row in df_std.iterrows():
        lang = row['Language']
        name = lang.rsplit('_', 1)[0] if '_' in lang else lang
        
        beta_r = row.get('R_Complex_Beta', np.nan)
        pval_r = row.get('R_Complex_Pval', np.nan)
        beta_l = row.get('L_Complex_Beta', np.nan)
        pval_l = row.get('L_Complex_Pval', np.nan)
        
        html.append("<tr>")
        html.append(f"<td class='lang-name'>{name}</td>")
        
        if pd.notna(beta_r):
            cls = 'score-positive' if beta_r > 0 else 'score-negative'
            html.append(f"<td class='{cls}'>{beta_r:.3f}</td>")
            html.append(f"<td>{pval_r:.2e}</td>")
            html.append(f"<td><strong>{_sig_stars(pval_r)}</strong></td>")
        else:
            html.extend(["<td class='na-cell'>-</td>"] * 3)
            
        if pd.notna(beta_l):
            cls = 'score-positive' if beta_l < 0 else 'score-negative'
            html.append(f"<td class='{cls}'>{beta_l:.3f}</td>")
            html.append(f"<td>{pval_l:.2e}</td>")
            html.append(f"<td><strong>{_sig_stars(pval_l)}</strong></td>")
        else:
            html.extend(["<td class='na-cell'>-</td>"] * 3)
            
        html.append("</tr>")
        
        # Horizontal Binomial Tests
        pvals_r_str = str(row.get('R_Horiz_Pvals', '')) if pd.notna(row.get('R_Horiz_Pvals')) else ''
        pvals_l_str = str(row.get('L_Horiz_Pvals', '')) if pd.notna(row.get('L_Horiz_Pvals')) else ''
        
        def pct_sig(pval_str):
            if not pval_str: return np.nan
            pvals = [float(p) for p in pval_str.split('|') if p]
            if not pvals: return np.nan
            sig_count = sum(1 for p in pvals if p < 0.05)
            return sig_count / len(pvals) * 100
            
        pct_r = pct_sig(pvals_r_str)
        pct_l = pct_sig(pvals_l_str)
        
        html_horiz.append("<tr>")
        html_horiz.append(f"<td class='lang-name'>{name}</td>")
        
        h_score_r = row.get('R_Horiz_Score', np.nan)
        if pd.notna(h_score_r):
            html_horiz.append(f"<td>{h_score_r}</td>")
            html_horiz.append(f"<td>{pct_r:.1f}%</td>" if pd.notna(pct_r) else "<td class='na-cell'>-</td>")
        else:
            html_horiz.extend(["<td class='na-cell'>-</td>"] * 2)
            
        h_score_l = row.get('L_Horiz_Score', np.nan)
        if pd.notna(h_score_l):
            html_horiz.append(f"<td>{h_score_l}</td>")
            html_horiz.append(f"<td>{pct_l:.1f}%</td>" if pd.notna(pct_l) else "<td class='na-cell'>-</td>")
        else:
            html_horiz.extend(["<td class='na-cell'>-</td>"] * 2)
            
        html_horiz.append("</tr>")
        # Vertical Welch Tests
        pvals_vr_str = str(row.get('R_Vert_Pvals', '')) if pd.notna(row.get('R_Vert_Pvals')) else ''
        pvals_vl_str = str(row.get('L_Vert_Pvals', '')) if pd.notna(row.get('L_Vert_Pvals')) else ''
        
        pct_vr = pct_sig(pvals_vr_str)
        pct_vl = pct_sig(pvals_vl_str)
        
        html_vert.append("<tr>")
        html_vert.append(f"<td class='lang-name'>{name}</td>")
        
        v_score_r = row.get('R_Vert_Score', np.nan)
        if pd.notna(v_score_r):
            html_vert.append(f"<td>{v_score_r}</td>")
            html_vert.append(f"<td>{pct_vr:.1f}%</td>" if pd.notna(pct_vr) else "<td class='na-cell'>-</td>")
        else:
            html_vert.extend(["<td class='na-cell'>-</td>"] * 2)
            
        v_score_l = row.get('L_Vert_Score', np.nan)
        if pd.notna(v_score_l):
            html_vert.append(f"<td>{v_score_l}</td>")
            html_vert.append(f"<td>{pct_vl:.1f}%</td>" if pd.notna(pct_vl) else "<td class='na-cell'>-</td>")
        else:
            html_vert.extend(["<td class='na-cell'>-</td>"] * 2)
        html_vert.append("</tr>")

        # Diagonal Welch Tests
        pvals_dr_str = str(row.get('R_Diag_Pvals', '')) if pd.notna(row.get('R_Diag_Pvals')) else ''
        pvals_dl_str = str(row.get('L_Diag_Pvals', '')) if pd.notna(row.get('L_Diag_Pvals')) else ''
        
        pct_dr = pct_sig(pvals_dr_str)
        pct_dl = pct_sig(pvals_dl_str)
        
        html_diag.append("<tr>")
        html_diag.append(f"<td class='lang-name'>{name}</td>")
        
        d_score_r = row.get('R_Diag_Score', np.nan)
        if pd.notna(d_score_r):
            html_diag.append(f"<td>{d_score_r}</td>")
            html_diag.append(f"<td>{pct_dr:.1f}%</td>" if pd.notna(pct_dr) else "<td class='na-cell'>-</td>")
        else:
            html_diag.extend(["<td class='na-cell'>-</td>"] * 2)
            
        d_score_l = row.get('L_Diag_Score', np.nan)
        if pd.notna(d_score_l):
            html_diag.append(f"<td>{d_score_l}</td>")
            html_diag.append(f"<td>{pct_dl:.1f}%</td>" if pd.notna(pct_dl) else "<td class='na-cell'>-</td>")
        else:
            html_diag.extend(["<td class='na-cell'>-</td>"] * 2)
        html_diag.append("</tr>")
        
    html.append("</tbody></table>")
    
    html.extend(html_horiz)
    html.append("</tbody></table>")
    
    html.extend(html_vert)
    html.append("</tbody></table>")
    
    html.extend(html_diag)
    html.append("</tbody></table>")
    
    html.append(get_footer())
    
    with open(os.path.join(out_dir, "sbl_significance.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))

if __name__ == "__main__":
    generate("html_sbl_analyses")

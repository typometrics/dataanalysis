import os
import pandas as pd
import matplotlib.pyplot as plt
from sbl_html_utils import get_header, get_nav, get_footer

def generate_visualizations(csv_path, out_dir):
    df = pd.read_csv(csv_path)
    df_std = df[df['Table_Type'] == 'Standard'].copy()
    
    # 1. Histogram of Right Complex Beta
    plt.figure(figsize=(8, 4))
    df_std['R_Complex_Beta'].dropna().hist(bins=20, color='#2196F3', edgecolor='black')
    plt.title('Distribution of Right SbL $\\beta$')
    plt.xlabel('SbL $\\beta$ (slope)')
    plt.ylabel('Number of Languages')
    plt.grid(axis='y', alpha=0.75)
    hist_path = os.path.join(out_dir, 'hist_r_beta.svg')
    plt.savefig(hist_path, format='svg')
    plt.close()
    
    # 1b. Histogram of Left Complex Beta
    plt.figure(figsize=(8, 4))
    df_std['L_Complex_Beta'].dropna().hist(bins=20, color='#FF9800', edgecolor='black')
    plt.title('Distribution of Left SbL $\\beta$')
    plt.xlabel('Left SbL $\\beta$ (slope)')
    plt.ylabel('Number of Languages')
    plt.grid(axis='y', alpha=0.75)
    hist_l_path = os.path.join(out_dir, 'hist_l_beta.svg')
    plt.savefig(hist_l_path, format='svg')
    plt.close()
    
    # 2. Histogram of Horizontal Law Scores
    plt.figure(figsize=(6, 4))
    df_std['R_Horiz_Score'].dropna().value_counts().sort_index().plot(kind='bar', color='#4CAF50')
    plt.title('Right Horizontal Law Scores (Out of 6)')
    plt.xlabel('Score')
    plt.ylabel('Count')
    hist_h_path = os.path.join(out_dir, 'hist_r_horiz.svg')
    plt.savefig(hist_h_path, format='svg')
    plt.close()
    
    # 3. Left vs Right Asymmetry Scatter Plot
    plt.figure(figsize=(6, 6))
    df_plot = df_std.dropna(subset=['L_Complex_Beta', 'R_Complex_Beta']).copy()
    # Invert left beta so positive means SBL compliance for both
    df_plot['Left_Effect'] = -df_plot['L_Complex_Beta']
    df_plot['Right_Effect'] = df_plot['R_Complex_Beta']
    plt.scatter(df_plot['Left_Effect'], df_plot['Right_Effect'], alpha=0.6, color='#9C27B0', edgecolor='white')
    
    # Draw quadrant lines at 0
    plt.axhline(0, color='black', lw=1, ls='--')
    plt.axvline(0, color='black', lw=1, ls='--')
    
    # Plot diagonal x=y line for reference
    min_val = min(df_plot['Left_Effect'].min(), df_plot['Right_Effect'].min()) - 0.1
    max_val = max(df_plot['Left_Effect'].max(), df_plot['Right_Effect'].max()) + 0.1
    plt.plot([min_val, max_val], [min_val, max_val], color='gray', linestyle=':', lw=1.5)
    
    plt.title('Left vs. Right SbL Effect Strength')
    plt.xlabel('Left Effect (-$\\beta_{Left}$)')
    plt.ylabel('Right Effect ($\\beta_{Right}$)')
    plt.grid(True, alpha=0.3)
    scatter_path = os.path.join(out_dir, 'scatter_asymmetry.svg')
    plt.savefig(scatter_path, format='svg')
    plt.close()

def generate(out_dir):
    csv_path = "data/sbl_laws_summary.csv"
    if os.path.exists(csv_path):
        generate_visualizations(csv_path, out_dir)
        
    html = [
        get_header("Visualizations"),
        get_nav("sbl_laws_visualizations.html"),
        "<h1>Sy Laws Visualizations</h1>",
        "<div class='explanation'>",
        "<p>This page visualizes the global compliance across the 180 languages for the Standard Helix tables.</p>",
        "</div>",
        "<h2>1. Distribution of the Complex SbL $\\beta$</h2>",
        "<p>These histograms show the distribution of the regression slope (SbL $\\beta$) for both the Right and Left sides. For the Right side, a positive value indicates the expected Short-Before-Long effect (inner dependents are shorter). For the Left side, \"Short-Before-Long\" implies that dependents further from the verb (which occur earlier) are shorter than those closer to the verb. Thus, a <strong>negative slope</strong> ($\\beta$) indicates compliance with the Short-Before-Long effect. On this site, Left slopes are negated in comparative visualizations so that a positive value (Green) consistently means compliant.</p>",
        "<div style='display:flex; gap:20px; flex-wrap:wrap;'>",
        "  <div style='flex:1; min-width:400px;'>",
        "    <h3>Right Side</h3>",
        "    <img src='hist_r_beta.svg' alt='Histogram of Right SbL Beta' style='max-width:100%; border:1px solid #ddd;'>",
        "  </div>",
        "  <div style='flex:1; min-width:400px;'>",
        "    <h3>Left Side</h3>",
        "    <img src='hist_l_beta.svg' alt='Histogram of Left SbL Beta' style='max-width:100%; border:1px solid #ddd;'>",
        "  </div>",
        "</div>",
        "<h2>2. Horizontal Law Compliance</h2>",
        "<p>This chart shows how many languages achieve perfect compliance (6/6) or partial compliance to the strict Horizontal Law ($R_n^k < R_n^{k+1}$).</p>",
        "<img src='hist_r_horiz.svg' alt='Histogram of Horizontal Scores' style='max-width:100%; border:1px solid #ddd;'>",
        "<h2>3. Left vs. Right Asymmetry</h2>",
        "<p>This scatter plot visualizes whether the Short-Before-Long principle is applied symmetrically. The Left SbL slope is negated so that for both axes, a <strong>positive value means compliance</strong> with the SbL principle. The diagonal dotted line represents perfect symmetry.</p>",
        "<img src='scatter_asymmetry.svg' alt='Scatter plot of Left vs Right asymmetry' style='max-width:100%; border:1px solid #ddd;'>",
        get_footer()
    ]
    
    with open(os.path.join(out_dir, "sbl_laws_visualizations.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))

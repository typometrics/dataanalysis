import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from sbl_html_utils import get_header, get_nav, get_footer

try:
    from adjustText import adjust_text
except ImportError:
    adjust_text = None
    print("Warning: adjustText not found. Labels may overlap.")

def _add_labels(df, x_col, y_col, ax, label_col='Language'):
    """Add language labels to scatter points using adjustText."""
    texts = []
    for _, row in df.iterrows():
        if pd.notna(row[x_col]) and pd.notna(row[y_col]):
            # Extract language name from 'Name_code' format
            lang = str(row[label_col])
            name = lang.rsplit('_', 1)[0] if '_' in lang else lang
            texts.append(ax.text(row[x_col], row[y_col], name, fontsize=7, alpha=0.8))
    if texts and adjust_text is not None:
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='-', color='gray', alpha=0.5, lw=0.5), lim=30)

def generate_visualizations(csv_path, out_dir):
    df = pd.read_csv(csv_path)
    df_std = df[df['Table_Type'] == 'AnyOtherSide'].copy()
    
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
    fig, ax = plt.subplots(figsize=(8, 8))
    df_plot = df_std.dropna(subset=['L_Complex_Beta', 'R_Complex_Beta']).copy()
    # Invert left beta so positive means SBL compliance for both
    df_plot['Left_Effect'] = -df_plot['L_Complex_Beta']
    df_plot['Right_Effect'] = df_plot['R_Complex_Beta']
    ax.scatter(df_plot['Left_Effect'], df_plot['Right_Effect'], alpha=0.6, color='#9C27B0', edgecolor='white')
    
    # Draw quadrant lines at 0
    ax.axhline(0, color='black', lw=1, ls='--')
    ax.axvline(0, color='black', lw=1, ls='--')
    
    # Plot diagonal x=y line for reference
    min_val = min(df_plot['Left_Effect'].min(), df_plot['Right_Effect'].min()) - 0.1
    max_val = max(df_plot['Left_Effect'].max(), df_plot['Right_Effect'].max()) + 0.1
    ax.plot([min_val, max_val], [min_val, max_val], color='gray', linestyle=':', lw=1.5)
    
    ax.set_title('Left vs. Right SbL Effect Strength')
    ax.set_xlabel('Left Effect (-$\\beta_{Left}$)')
    ax.set_ylabel('Right Effect ($\\beta_{Right}$)')
    ax.grid(True, alpha=0.3)
    _add_labels(df_plot, 'Left_Effect', 'Right_Effect', ax)
    plt.tight_layout()
    scatter_path = os.path.join(out_dir, 'scatter_asymmetry.svg')
    plt.savefig(scatter_path, format='svg', bbox_inches='tight')
    plt.close()

def generate(out_dir):
    csv_path = "data/sbl_laws_summary.csv"
    if os.path.exists(csv_path):
        generate_visualizations(csv_path, out_dir)
        
    generate_outer_effect_scatters(out_dir)
    generate_ov_vs_hi_scatter(out_dir)
    
    html = [
        get_header("Visualizations"),
        get_nav("sbl_laws_visualizations.html"),
        "<h1 title='Visual exploration of structural symmetries and language typologies.'>SBL Visualizations</h1>",
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
        "<h2>4. Head-Initiality vs. Outer Constituent Effect</h2>",
        "<p>These scatter plots show the relationship between the Head-Initiality score and the Outer Constituent Effect (ratio of outer constituent geometric mean to the remaining horizontal ratios). A ratio &gt; 1 means the outer constituents represent a stronger factor than the internal constituents.</p>",
        "<div style='display:flex; gap:20px; flex-wrap:wrap;'>",
        "  <div style='flex:1; min-width:400px;'>",
        "    <h3>Right Side</h3>",
        "    <img src='scatter_hi_vs_right_outer.svg' alt='Scatter plot of Head-Initiality vs Right Outer Effect' style='max-width:100%; border:1px solid #ddd;'>",
        "  </div>",
        "  <div style='flex:1; min-width:400px;'>",
        "    <h3>Left Side</h3>",
        "    <img src='scatter_hi_vs_left_outer.svg' alt='Scatter plot of Head-Initiality vs Left Outer Effect' style='max-width:100%; border:1px solid #ddd;'>",
        "  </div>",
        "</div>",
        "<h2>5. OV Score vs. Head-Initiality</h2>",
        "<p>This scatter plot shows the relationship between the OV Score (1 = fully OV, 0 = fully VO) and the Head-Initiality score. A strong negative correlation is expected since OV languages tend to be head-final.</p>",
        "<img src='scatter_ov_vs_hi.svg' alt='Scatter plot of OV Score vs Head-Initiality' style='max-width:100%; border:1px solid #ddd;'>",
        get_footer()
    ]
    
    with open(os.path.join(out_dir, "sbl_laws_visualizations.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))

def generate_outer_effect_scatters(out_dir):
    csv_path = "data/sbl_laws_summary.csv"
    if not os.path.exists(csv_path): return
    df = pd.read_csv(csv_path)
    df_std = df[df['Table_Type'] == 'AnyOtherSide'].copy()
    
    # Right side scatter
    df_plot_r = df_std.dropna(subset=['head_initiality', 'R_Outer_Effect']).copy()
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(df_plot_r['head_initiality'], df_plot_r['R_Outer_Effect'], alpha=0.6, color='#2196F3', edgecolor='white')
    ax.axvline(0.5, color='black', lw=1, ls='--')
    ax.axhline(1.0, color='black', lw=1, ls='--')
    ax.set_title('Head-Initiality vs Right Outer Constituent Effect')
    ax.set_xlabel('Head-Initiality Score')
    ax.set_ylabel('Right Outer Constituent Effect (Ratio)')
    ax.grid(True, alpha=0.3)
    _add_labels(df_plot_r, 'head_initiality', 'R_Outer_Effect', ax)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'scatter_hi_vs_right_outer.svg'), format='svg', bbox_inches='tight')
    plt.close()
    
    # Left side scatter
    df_plot_l = df_std.dropna(subset=['head_initiality', 'L_Outer_Effect']).copy()
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(df_plot_l['head_initiality'], df_plot_l['L_Outer_Effect'], alpha=0.6, color='#FF9800', edgecolor='white')
    ax.axvline(0.5, color='black', lw=1, ls='--')
    ax.axhline(1.0, color='black', lw=1, ls='--')
    ax.set_title('Head-Initiality vs Left Outer Constituent Effect')
    ax.set_xlabel('Head-Initiality Score')
    ax.set_ylabel('Left Outer Constituent Effect (Ratio)')
    ax.grid(True, alpha=0.3)
    _add_labels(df_plot_l, 'head_initiality', 'L_Outer_Effect', ax)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'scatter_hi_vs_left_outer.svg'), format='svg', bbox_inches='tight')
    plt.close()

def generate_ov_vs_hi_scatter(out_dir):
    """Generate scatter plot of OV Score vs Head-Initiality."""
    csv_path = "data/sbl_laws_summary.csv"
    if not os.path.exists(csv_path): return
    df = pd.read_csv(csv_path)
    df_std = df[df['Table_Type'] == 'AnyOtherSide'].copy()
    
    df_plot = df_std.dropna(subset=['ov_value', 'head_initiality']).copy()
    if len(df_plot) < 3:
        return
    
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(df_plot['ov_value'], df_plot['head_initiality'], alpha=0.6, color='#4CAF50', edgecolor='white', s=50)
    
    # Regression line
    slope, intercept, r, p, se = stats.linregress(df_plot['ov_value'], df_plot['head_initiality'])
    x_line = np.linspace(df_plot['ov_value'].min(), df_plot['ov_value'].max(), 100)
    ax.plot(x_line, slope * x_line + intercept, 'r-', linewidth=2, alpha=0.7,
            label=f'Regression: r={r:.3f}, p={p:.1e}')
    
    # Correlation info
    from scipy.stats import spearmanr
    r_s, p_s = spearmanr(df_plot['ov_value'], df_plot['head_initiality'])
    ax.text(0.02, 0.98, f'Pearson r={r:.3f} (p={p:.1e})\nSpearman ρ={r_s:.3f} (p={p_s:.1e})\nN={len(df_plot)}',
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax.set_title('OV Score vs Head-Initiality')
    ax.set_xlabel('OV Score (1 = fully OV, 0 = fully VO)')
    ax.set_ylabel('Head-Initiality Score')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right')
    
    _add_labels(df_plot, 'ov_value', 'head_initiality', ax)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, 'scatter_ov_vs_hi.svg'), format='svg', bbox_inches='tight')
    plt.close()


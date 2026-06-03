import os
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sbl_html_utils import get_header, get_nav, get_footer

def get_curve_data(avg_sizes, lang_code, side='right', n=2):
    """
    Get average constituent sizes for n total dependents on one side.
    Returns (x, y) where x is position k (1..n) and y is the size value.
    Uses 'anyother' keys to match the unconstrained matrix.
    """
    x = []
    y = []
    for k in range(1, n + 1):
        if side == 'right':
            key = f"right_{k}_anyother_totright_{n}"
        else:
            key = f"left_{k}_anyother_totleft_{n}"
            
        val = avg_sizes.get(lang_code, {}).get(key)
        if val is not None and not np.isnan(val):
            x.append(k)
            y.append(val)
    return x, y

def generate_language_plots(avg_sizes, lang_code, lang_name, out_dir):
    """
    Generate a single combined SVG plot with Left and Right Outer Effect curves side-by-side.
    """
    os.makedirs(os.path.join(out_dir, 'outer_plots'), exist_ok=True)
    
    # Define styles for n=2, 3, 4
    styles = {
        2: {'color': '#2196F3', 'marker': 'o', 'label': 'n = 2'},
        3: {'color': '#FF9800', 'marker': 's', 'label': 'n = 3'},
        4: {'color': '#4CAF50', 'marker': 'd', 'label': 'n = 4'}
    }
    
    # Collect all y values to determine shared y limits
    all_y = []
    
    left_data = {}
    right_data = {}
    
    for n in [2, 3, 4]:
        lx, ly = get_curve_data(avg_sizes, lang_code, 'left', n)
        rx, ry = get_curve_data(avg_sizes, lang_code, 'right', n)
        
        left_data[n] = (lx, ly)
        right_data[n] = (rx, ry)
        
        all_y.extend(ly)
        all_y.extend(ry)
        
    has_data = len(all_y) > 0
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))
    
    # Custom font style
    plt.rcParams['font.family'] = 'sans-serif'
    
    if has_data:
        min_y = min(all_y)
        max_y = max(all_y)
        y_range = max_y - min_y
        margin = max(0.15, y_range * 0.08)
        ylim_min = max(0.8, min_y - margin)
        ylim_max = max_y + margin
        
        # Set shared limits
        ax1.set_ylim(ylim_min, ylim_max)
        ax2.set_ylim(ylim_min, ylim_max)
        
        # Plot Left side
        for n in [2, 3, 4]:
            lx, ly = left_data[n]
            if lx:
                ax1.plot(lx, ly, styles[n]['marker'] + '-', color=styles[n]['color'], 
                         label=styles[n]['label'], linewidth=2, markersize=6)
        
        # Invert Left side x-axis: ticks from 4 to 1
        ax1.set_xlim(4.5, 0.5)
        ax1.set_xticks([4, 3, 2, 1])
        
        # Plot Right side
        for n in [2, 3, 4]:
            rx, ry = right_data[n]
            if rx:
                ax2.plot(rx, ry, styles[n]['marker'] + '-', color=styles[n]['color'], 
                         label=styles[n]['label'], linewidth=2, markersize=6)
        
        ax2.set_xlim(0.5, 4.5)
        ax2.set_xticks([1, 2, 3, 4])
    else:
        # Placeholder for no data
        ax1.text(0.5, 0.5, "No Left Data Available", ha='center', va='center', color='gray')
        ax2.text(0.5, 0.5, "No Right Data Available", ha='center', va='center', color='gray')
        ax1.set_xticks([])
        ax2.set_xticks([])
        ax1.set_yticks([])
        ax2.set_yticks([])

    # Grid and spines configuration
    for ax, title in [(ax1, 'Left Side ($L_n^k$)'), (ax2, 'Right Side ($R_n^k$)')]:
        ax.set_title(title, fontsize=12, pad=10, fontweight='bold', color='#333')
        ax.set_xlabel('Visual Distance $k$', fontsize=10, labelpad=8)
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#bbb')
        ax.spines['bottom'].set_color('#bbb')
        
    ax1.set_ylabel('Average Size (words)', fontsize=10, labelpad=8)
    
    # Legend
    if ax1.get_legend_handles_labels()[0]:
        ax1.legend(loc='best', frameon=True, facecolor='white', edgecolor='#eee')
    if ax2.get_legend_handles_labels()[0]:
        ax2.legend(loc='best', frameon=True, facecolor='white', edgecolor='#eee')
        
    plt.suptitle(f"{lang_name} ({lang_code}) - Outer Effect Curves", fontsize=13, fontweight='bold', y=0.98, color='#111')
    plt.tight_layout()
    
    plot_path = os.path.join(out_dir, 'outer_plots', f"{lang_code}_outer_effects.svg")
    plt.savefig(plot_path, format='svg', bbox_inches='tight')
    plt.close()

def generate(out_dir):
    csv_path = "data/sbl_laws_summary.csv"
    avg_sizes_path = "data/all_langs_average_sizes.pkl"
    
    if not os.path.exists(csv_path) or not os.path.exists(avg_sizes_path):
        print("SBL data files missing. Cannot generate outer effect curves page.")
        return
        
    df = pd.read_csv(csv_path)
    df_std = df[df['Table_Type'] == 'AnyOtherSide']
    
    with open(avg_sizes_path, 'rb') as f:
        avg_sizes = pickle.load(f)
        
    print(f"Generating Outer Effect Curve SVGs for {len(df_std)} languages...")
    for _, row in df_std.iterrows():
        lang = row['Language']
        if '_' in lang:
            name, code = lang.rsplit('_', 1)
        else:
            name, code = lang, lang
        generate_language_plots(avg_sizes, code, name, out_dir)
        
    print("Generating sbl_outer_effects.html page...")
    html = [
        get_header("Outer Effect Curves"),
        get_nav("sbl_outer_effects.html"),
        "<h1>Language-Specific Outer Effect Curves</h1>",
        "<div class='explanation'>",
        "<p>This page visualizes the <strong>Outer Effect Curves</strong> for each language. For a fixed total dependent count $n \\in \\{2, 3, 4\\}$, we plot the average constituent size of the dependent at visual distance $k \\in \\{1..n\\}$ from the verb.</p>",
        "<ul>",
        "  <li><strong>Right Side ($R_n^k$)</strong>: Visual distance $k$ increases from left to right (from $k=1$ closest to the verb, to $k=4$ furthest).</li>",
        "  <li><strong>Left Side ($L_n^k$)</strong>: Visual distance $k$ increases towards the left, meaning that $k=1$ (closest to the verb) is on the right, and $k=4$ (furthest from the verb) is on the left. The Left graph's x-axis is inverted to match this physical layout.</li>",
        "  <li><strong>Shared Scale</strong>: To allow direct visual comparison of the Left and Right effect strengths, both plots for the same language share identical X and Y axis limits.</li>",
        "</ul>",
        "</div>",
        
        # Search / filter interface
        "<div style='margin-bottom: 20px;'>",
        "  <input type='text' id='langSearch' onkeyup='filterLanguages()' placeholder='Search for a language...' style='padding: 8px 12px; width: 300px; font-size: 14px; border: 1px solid #ccc; border-radius: 4px;'>",
        "</div>",
        
        "<div class='graphs-container' style='display: flex; flex-direction: column; gap: 40px;'>"
    ]
    
    for _, row in df_std.iterrows():
        lang = row['Language']
        if '_' in lang:
            name, code = lang.rsplit('_', 1)
        else:
            name, code = lang, lang
            
        beta_r = row['R_Complex_Beta']
        beta_l = row['L_Complex_Beta']
        
        beta_r_str = f"{beta_r:.3f}" if pd.notna(beta_r) else "-"
        beta_l_str = f"{beta_l:.3f}" if pd.notna(beta_l) else "-"
        
        html.append(f"""
        <div class='lang-card' data-name='{name.lower()}' data-code='{code.lower()}' style='background: #fbfbfb; border: 1px solid #e0e0e0; border-radius: 6px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);'>
            <div style='display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px;'>
                <h2 style='margin: 0; color: #2c3e50;'>{name} <small style='color: #888; font-weight: normal;'>({code})</small></h2>
                <div style='font-size: 13px; color: #555;'>
                    <span style='margin-right: 15px;'><strong>Right SbL &beta;:</strong> {beta_r_str}</span>
                    <span><strong>Left SbL &beta;:</strong> {beta_l_str}</span>
                </div>
            </div>
            <div style='display: flex; justify-content: center;'>
                <img src='outer_plots/{code}_outer_effects.svg' alt='{name} Outer Effect Curves' style='max-width: 100%; height: auto;'>
            </div>
        </div>
        """)
        
    html.append("</div>")
    
    # JavaScript for client-side search/filtering
    search_js = """
<script>
function filterLanguages() {
    var input = document.getElementById('langSearch');
    var filter = input.value.toLowerCase();
    var cards = document.getElementsByClassName('lang-card');
    
    for (var i = 0; i < cards.length; i++) {
        var name = cards[i].getAttribute('data-name');
        var code = cards[i].getAttribute('data-code');
        if (name.indexOf(filter) > -1 || code.indexOf(filter) > -1) {
            cards[i].style.display = "";
        } else {
            cards[i].style.display = "none";
        }
    }
}
</script>
"""
    html.append(search_js)
    html.append(get_footer())
    
    with open(os.path.join(out_dir, "sbl_outer_effects.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(html))
        
    print("Outer Effect Curve generation complete!")

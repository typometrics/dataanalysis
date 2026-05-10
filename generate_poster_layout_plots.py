import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

DATA_DIR = "data"
OUTPUT_DIR = "plots"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load data
    df_total = pd.read_csv(os.path.join(DATA_DIR, "mal_vo_merged.csv"))
    df_left = pd.read_csv(os.path.join(DATA_DIR, "mal_compliance_left.csv"))
    df_right = pd.read_csv(os.path.join(DATA_DIR, "mal_compliance_right.csv"))
    
    # Merge vo_score into left and right
    vo_scores = df_total[['language_code', 'vo_score']].drop_duplicates()
    df_left = df_left.merge(vo_scores, on='language_code', how='left')
    df_right = df_right.merge(vo_scores, on='language_code', how='left')
    
    df = pd.concat([df_total, df_left, df_right], ignore_index=True)
    df = df.dropna(subset=['beta_1max'])
    
    # ---------------------------------------------------------
    # 1. MAL Effect by Language Family (poster_mal_effect_by_family.pdf)
    # ---------------------------------------------------------
    df_total_valid = df_total.dropna(subset=['beta_1max']).copy()
    
    group_medians = df_total_valid.groupby('group')['beta_1max'].median().sort_values(ascending=False)
    order = group_medians.index.tolist()
    
    fig, ax = plt.subplots(figsize=(10, 3))
    sns.boxplot(data=df_total_valid, x='beta_1max', y='group', order=order, ax=ax, palette='Set3', showfliers=False)
    sns.stripplot(data=df_total_valid, x='beta_1max', y='group', order=order, ax=ax, color='black', alpha=0.5, size=4)
    
    # Add vertical lines for compliance zones
    ax.axvline(x=-0.1, color='red', linestyle='--', alpha=0.7)
    ax.axvline(x=0.1, color='green', linestyle='--', alpha=0.7)
    ax.axvline(x=0.0, color='gray', linestyle='-', alpha=0.3)
    
    # Invert x-axis if we want -beta to be positive? Wait, "MAL effect (-beta)".
    # The poster previously used positive for shrinkage, let's keep beta_1max. Usually beta < 0 means MAL if beta is slope.
    # Actually, in this codebase `beta` is usually slope of log-log. Wait, the df has `beta_1max`. Let me check if it's negative for MAL.
    # Standard MENZERATH is negative slope (shrinkage). 
    # Let's plot raw beta_1max.
    ax.set_xlabel('MAL Effect (β from n=1→max)', fontsize=14)
    ax.set_ylabel('Language Family', fontsize=14)
    ax.tick_params(axis='both', which='major', labelsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'poster_mal_effect_by_family.pdf'), dpi=300)
    plt.close()
    
    # ---------------------------------------------------------
    # 2. IE vs Non-IE (poster_ie_vs_non_ie.pdf)
    # ---------------------------------------------------------
    df_total_valid['is_ie'] = df_total_valid['group'].apply(lambda x: 'Indo-European' if x == 'Indo-European' else 'Non-Indo-European')
    fig, ax = plt.subplots(figsize=(6, 3))
    
    sns.boxplot(data=df_total_valid, x='is_ie', y='beta_1max', ax=ax, palette=['#1f77b4', '#ff7f0e'], showfliers=False)
    sns.stripplot(data=df_total_valid, x='is_ie', y='beta_1max', ax=ax, color='black', alpha=0.5, size=5)
    
    ax.axhline(y=-0.1, color='red', linestyle='--', alpha=0.7)
    ax.axhline(y=0.1, color='green', linestyle='--', alpha=0.7)
    ax.axhline(y=0.0, color='gray', linestyle='-', alpha=0.3)
    
    ax.set_ylabel('MAL Effect (β)', fontsize=14)
    ax.set_xlabel('')
    ax.tick_params(axis='both', which='major', labelsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'poster_ie_vs_non_ie.pdf'), dpi=300)
    plt.close()

    # ---------------------------------------------------------
    # 3. Directional vs VO Score (1x3 panel)
    # ---------------------------------------------------------
    # We want MAL, RMAL, LMAL vs VO score
    fig, axes = plt.subplots(1, 3, figsize=(18, 4), sharey=True)
    
    # Ensure color coding is consistent. 
    # Let's color by whether it's IE or Non-IE, or by 'group', or just a single color.
    # "Consistent color code and order across all 3 graphs" -> I will color by group.
    group_to_color = {
        'Indo-European': '#1f77b4', 'Uralic': '#ff7f0e', 'Turkic': '#2ca02c',
        'Afro-Asiatic': '#d62728', 'Dravidian': '#9467bd', 'Sino-Tibetan': '#8c564b',
        'Austronesian': '#e377c2', 'Niger-Congo': '#7f7f7f', 'Tai-Kadai': '#bcbd22',
        'Other': '#17becf'
    }
    
    score_types = ['total', 'left', 'right']
    titles = ['Total MAL vs VO/OV', 'LMAL (Left) vs VO/OV', 'RMAL (Right) vs VO/OV']
    
    for ax, stype, title in zip(axes, score_types, titles):
        df_sub = df[(df['score_type'] == stype) & df['vo_score'].notna()].copy()
        
        # Plot scatter
        for group in df_sub['group'].unique():
            df_g = df_sub[df_sub['group'] == group]
            color = group_to_color.get(group, group_to_color['Other'])
            ax.scatter(df_g['vo_score'], df_g['beta_1max'], 
                       color=color, alpha=0.7, edgecolors='none', label=group, s=50)
            
        ax.set_title(title, fontsize=16)
        ax.set_xlabel('VO Score', fontsize=14)
        
        if stype == 'total':
            ax.set_ylabel('MAL Effect (β)', fontsize=14)
            # We will put the legend above the first plot or outside.
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            # Put legend in the lower right, very small, with multiple columns to save vertical space.
            ax.legend(by_label.values(), by_label.keys(), loc='lower right', ncol=2, fontsize=8, framealpha=0.8)
            
        # Add horizontal lines
        ax.axhline(y=-0.1, color='red', linestyle='--', alpha=0.7, label='Anti-MAL boundary')
        ax.axhline(y=0.1, color='green', linestyle='--', alpha=0.7, label='MAL boundary')
        ax.axhline(y=0.0, color='gray', linestyle='-', alpha=0.3)
        
        ax.tick_params(axis='both', which='major', labelsize=12)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'poster_directional_vs_vo.pdf'), dpi=300)
    plt.close()
    print("All poster layout plots generated successfully.")

if __name__ == "__main__":
    main()

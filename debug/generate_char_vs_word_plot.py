import os
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats # Added for regression
import data_utils
import plotting

# Ensure we use the latest styles provided by plotting
# Note: Since this is a script, 'plotting' is imported fresh.

DATA_DIR = "data"
PLOTS_DIR = "plots"
os.makedirs(PLOTS_DIR, exist_ok=True)

print("Loading metadata...")
metadata = data_utils.load_metadata(os.path.join(DATA_DIR, 'metadata.pkl'))
langNames = metadata['langNames']
langnameGroup = metadata['langnameGroup']
group_to_color = metadata['appearance_dict']

print("Loading size data...")
try:
    with open(os.path.join(DATA_DIR, 'all_langs_average_sizes_filtered.pkl'), 'rb') as f:
        all_langs_average_sizes_filtered = pickle.load(f)
        
    with open(os.path.join(DATA_DIR, 'all_langs_average_charsizes.pkl'), 'rb') as f:
        all_langs_average_charsizes = pickle.load(f)
except FileNotFoundError as e:
    print(f"Error loading files: {e}")
    print("Please ensure run_data_extraction.py has finished.")
    exit(1)

print(f"Aligning data for {len(all_langs_average_sizes_filtered)} languages...")

plot_data = []

for lang in all_langs_average_sizes_filtered:
    if lang in all_langs_average_charsizes:
        # Average across all tracked positions
        word_sizes = list(all_langs_average_sizes_filtered[lang].values())
        char_sizes = list(all_langs_average_charsizes[lang].values())
        
        if word_sizes and char_sizes:
            avg_word = sum(word_sizes) / len(word_sizes)
            avg_char = sum(char_sizes) / len(char_sizes)
            
            plot_data.append({
                'Language': langNames.get(lang, lang),
                'Group': langnameGroup.get(langNames.get(lang, lang), 'Other'),
                'Avg Word Size': avg_word,
                'Avg Letter Size': avg_char
            })

df_size = pd.DataFrame(plot_data)

if not df_size.empty:
    print(f"Plotting {len(df_size)} languages...")
    plt.figure(figsize=(12, 8))
    sns.scatterplot(
        data=df_size, 
        x='Avg Word Size', 
        y='Avg Letter Size', 
        hue='Group', 
        palette=group_to_color,
        s=100
    )
    
    # Add labels using the custom utility
    plotting.adjust_text_labels(
        df_size, 
        'Avg Word Size', 
        'Avg Letter Size', 
        'Language', 
        ax=plt.gca()
    )
    
    # Add linear regression trendline
    slope, intercept, r_value, p_value, std_err = stats.linregress(df_size['Avg Word Size'], df_size['Avg Letter Size'])
    sns.regplot(data=df_size, x='Avg Word Size', y='Avg Letter Size', scatter=False, ci=None, line_kws={'color': 'black', 'alpha': 0.5, 'label': f'Regression (R²={r_value**2:.2f})'}, ax=plt.gca())

    # Add Average Ratio Diagonal
    avg_ratio = (df_size['Avg Letter Size'] / df_size['Avg Word Size']).mean()
    max_x = df_size['Avg Word Size'].max() * 1.1
    # Ensure line starts from origin
    plt.plot([0, max_x], [0, max_x * avg_ratio], linestyle='--', color='gray', label=f'Avg Ratio ({avg_ratio:.2f})')

    plt.title('Average Constituent Size: Words vs Letters')
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    output_path = os.path.join(PLOTS_DIR, 'word_vs_letter_size.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Plot saved to {output_path}")
else:
    print("No intersecting data found.")


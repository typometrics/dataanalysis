import json

nb_path = '/bigstorage/kim/typometrics/dataanalysis/05_comparative_visualization.ipynb'

with open(nb_path, 'r') as f:
    nb = json.load(f)

# Find the cell with "Word vs Letter Size Analysis"
target_cell_index = -1
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if "Word vs Letter Size Analysis" in source:
            target_cell_index = i
            break

if target_cell_index != -1:
    print(f"Found target cell at index {target_cell_index}")
    cell = nb['cells'][target_cell_index]
    source_lines = cell['source']
    
    # We want to insert calculation and plotting code BEFORE "plt.show()" or at the end of plotting block
    # Let's rebuild the source code
    
    new_source = []
    
    # 1. Imports
    if "from scipy import stats" not in "".join(source_lines):
        new_source.append("from scipy import stats\n")
        
    for line in source_lines:
        if "plt.title('Average Constituent Size: Words vs Letters')" in line:
            # Insert lines before title
            
            # Regression
            new_source.append("\n    # Add linear regression trendline\n")
            new_source.append("    slope, intercept, r_value, p_value, std_err = stats.linregress(df_size['Avg Word Size'], df_size['Avg Letter Size'])\n")
            new_source.append("    sns.regplot(data=df_size, x='Avg Word Size', y='Avg Letter Size', scatter=False, ci=None, line_kws={'color': 'black', 'alpha': 0.5, 'label': f'Regression (R²={r_value**2:.2f})'}, ax=plt.gca())\n")
            
            # Diagonal (Average Ratio)
            new_source.append("\n    # Add Average Ratio Diagonal\n")
            new_source.append("    avg_ratio = (df_size['Avg Letter Size'] / df_size['Avg Word Size']).mean()\n")
            new_source.append("    max_x = df_size['Avg Word Size'].max() * 1.1\n")
            new_source.append("    max_y = df_size['Avg Letter Size'].max() * 1.1\n")
            # Ensure line starts from origin
            new_source.append("    plt.plot([0, max_x], [0, max_x * avg_ratio], linestyle='--', color='gray', label=f'Avg Ratio ({avg_ratio:.2f})')\n")
            new_source.append("\n")
            new_source.append(line) # Add title line back
            
        elif "plt.grid(True, alpha=0.3)" in line:
            new_source.append(line)
            # Add legend after grid
            new_source.append("    plt.legend()\n")
        else:
            new_source.append(line)
            
    cell['source'] = new_source
    
    with open(nb_path, 'w') as f:
        json.dump(nb, f, indent=1)
    print("Patched Notebook 05 with trendlines.")

else:
    print("Could not find target cell.")

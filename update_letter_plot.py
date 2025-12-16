
import nbformat
import sys

nb_path = '05_comparative_visualization.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

found = False
for cell in nb.cells:
    if cell.cell_type == 'code':
        if "Average Constituent Size: Words vs Letters" in cell.source:
            # this is the cell
            print("Found target cell.")
            
            # New code content
            new_source = """from scipy import stats
## Word vs Letter Size Analysis

# Compute averages per language
plot_data = []

for lang in all_langs_average_sizes_filtered:
    if lang in all_langs_average_charsizes:
        # Average across all tracked positions
        # We filter out positions with 0 count implicitly by using filtered dicts
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
    plt.figure(figsize=(12, 10))
    
    # 1. Scatter Plot
    sns.scatterplot(
        data=df_size, 
        x='Avg Word Size', 
        y='Avg Letter Size', 
        hue='Group', 
        palette=group_to_color,
        s=100
    )
    
    # 2. Add labels (using plotting util)
    plotting.adjust_text_labels(
        df_size, 
        'Avg Word Size', 
        'Avg Letter Size', 
        'Language', 
        ax=plt.gca()
    )
    
    # Calculate limits for diagonal lines
    max_x = df_size['Avg Word Size'].max()
    max_y = df_size['Avg Letter Size'].max()
    limit = max(max_x, max_y) * 1.1
    
    # 3. Linear Regression Trendline
    slope, intercept, r_value, p_value, std_err = stats.linregress(df_size['Avg Word Size'], df_size['Avg Letter Size'])
    sns.regplot(
        data=df_size, 
        x='Avg Word Size', 
        y='Avg Letter Size', 
        scatter=False, 
        ci=None, 
        line_kws={'color': 'black', 'alpha': 0.8, 'linestyle': '-', 'linewidth': 2, 'label': f'Regression: y={slope:.2f}x+{intercept:.2f} ($R^2$={r_value**2:.2f})'}, 
        ax=plt.gca()
    )

    # 4. Average Ratio Line (Force through origin)
    avg_ratio = (df_size['Avg Letter Size'] / df_size['Avg Word Size']).mean()
    plt.plot([0, limit], [0, limit * avg_ratio], linestyle='--', color='blue', linewidth=2, alpha=0.7, label=f'Avg Ratio (y={avg_ratio:.2f}x)')

    # 5. Diagonal y=x
    plt.plot([0, limit], [0, limit], linestyle=':', color='gray', linewidth=2, alpha=0.7, label='Diagonal (y=x)')

    # Metadata & Formatting
    plt.title('Average Constituent Size: Words vs Letters')
    plt.xlabel('Average Constituent Size (Word Count)')
    plt.ylabel('Average Constituent Size (Letter Count)')
    plt.grid(True, alpha=0.3)
    
    # Set limits to ensure diagonals look correct relative to aspect ratio if square, 
    # but here we just ensure they cover the data.
    # We might want to start from 0 to see the origin clearly
    plt.xlim(0, limit)
    plt.ylim(0, limit)
    
    plt.legend(loc='upper left', framealpha=0.9)
    plt.tight_layout()
    plt.show()
    
    # Print detailed stats
    print(f"Regression: y = {slope:.4f}x + {intercept:.4f}")
    print(f"R-squared: {r_value**2:.4f}")
    print(f"Average Letter/Word Ratio: {avg_ratio:.4f}")
    
else:
    print("No data available for plotting.")"""
            
            cell.source = new_source
            found = True
            break

if found:
    with open(nb_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)
    print("Notebook updated.")
else:
    print("Could not find the target cell.")

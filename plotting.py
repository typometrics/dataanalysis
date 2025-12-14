"""
Plotting and visualization functions for dependency analysis results.
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import seaborn as sns
import textwrap
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import Axes3D
from multiprocessing import Pool, cpu_count
from scipy import stats
from tqdm.notebook import tqdm


def _always_true(x):
    """Helper function for default filtering (always returns True)."""
    return True


def plot_mal_curves_with_groups(mal_data, langNames, langnameGroup, appearance_dict, 
                                  n_required=5, figsize=(12, 7)):
    """
    Plot MALₙ curves for languages with data from 1 to n_required dependents.
    
    Colors are based on language group, and a mean curve is also shown.
    
    Parameters
    ----------
    mal_data : dict
        Dictionary mapping language codes to {n: MAL_n} dictionaries
    langNames : dict
        Dictionary mapping language codes to full names
    langnameGroup : dict
        Dictionary mapping language names to groups
    appearance_dict : dict
        Dictionary mapping groups to colors
    n_required : int
        Required number of dependents (languages must have data for 1 to n_required)
    figsize : tuple
        Figure size (width, height)
    """
    ns = list(range(1, n_required + 1))
    
    # Filter languages with complete data
    filtered_mal_data = {
        lang: data for lang, data in mal_data.items()
        if all(n in data for n in ns)
    }
    print(f"Number of languages with data from n=1 to {n_required}:", len(filtered_mal_data))
    
    plt.figure(figsize=figsize)
    groups_plotted = set()
    
    # Plot individual language curves
    for lang, data in filtered_mal_data.items():
        lang_display_name = langNames.get(lang, lang)
        group = langnameGroup.get(lang_display_name, 'Other')
        color = appearance_dict.get(group, 'gray')
        values = [data[n] for n in ns]
        plt.plot(ns, values, alpha=0.3, color=color)
        groups_plotted.add(group)
    
    # Plot mean curve
    mean_vals = [
        np.mean([filtered_mal_data[lang][n] for lang in filtered_mal_data]) 
        for n in ns
    ]
    print("Mean values:", mean_vals)
    plt.plot(ns, mean_vals, color='black', linewidth=2.5, label='Mean')
    
    # Axes and grid
    plt.xlabel("Number of right dependents (n)")
    plt.ylabel("Average dependent length (MALₙ)")
    plt.title(f"MALₙ curves across {len(filtered_mal_data)} languages (with data from n=1 to {n_required})")
    plt.xticks(ns)
    plt.grid(True, which='major', axis='both', linestyle='--', alpha=0.6)
    
    # Legend
    legend_elements = [Line2D([0], [0], color='black', lw=2.5, label='Mean')]
    for group in sorted(groups_plotted):
        color = appearance_dict.get(group, 'gray')
        legend_elements.append(Line2D([0], [0], color=color, lw=2, label=group))
    plt.legend(handles=legend_elements, title="Language groups", 
              bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    plt.show()


def plot_mal_heatmap(mal_data, figsize=(12, 10), cmap="coolwarm"):
    """
    Plot a heatmap of MALₙ values across languages.
    
    Parameters
    ----------
    mal_data : dict
        Dictionary mapping language codes to {n: MAL_n} dictionaries
    figsize : tuple
        Figure size (width, height)
    cmap : str
        Colormap name
    """
    # Convert mal_data to a DataFrame
    df_mal = pd.DataFrame.from_dict(mal_data, orient='index')
    df_mal = df_mal.sort_index()  # sort languages alphabetically
    
    plt.figure(figsize=figsize)
    sns.heatmap(df_mal, cmap=cmap, annot=False, linewidths=0.3)
    plt.title("MALₙ across languages (n = number of right dependents)")
    plt.xlabel("n (number of right dependents)")
    plt.ylabel("Language")
    plt.tight_layout()
    plt.show()


def plot_scatter_2d(df, x_col, y_col, group_col, appearance_dict, 
                   title="", xlabel="", ylabel="", figsize=(10, 8), label_col=None, with_labels=True,
                   add_diagonal=False, add_regression=False):
    """
    Create a 2D scatter plot colored by language group.
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with data to plot
    x_col : str
        Column name for x-axis
    y_col : str
        Column name for y-axis
    group_col : str
        Column name for grouping/coloring
    appearance_dict : dict
        Dictionary mapping groups to colors
    title : str
        Plot title
    xlabel : str
        X-axis label
    ylabel : str
        Y-axis label
    figsize : tuple
        Figure size (width, height)
    add_diagonal : bool
        Whether to add a dashed diagonal line (y=x)
    add_regression : bool
        Whether to add a linear regression trend line and average ratio
    """
    plt.figure(figsize=figsize)
    
    # Use seaborn scatterplot for consistency
    sns.scatterplot(data=df, x=x_col, y=y_col, hue=group_col, palette=appearance_dict, s=60, alpha=0.7)
    
    # Add diagonal line
    if add_diagonal:
        min_val = min(df[x_col].min(), df[y_col].min())
        max_val = max(df[x_col].max(), df[y_col].max())
        plt.plot([min_val, max_val], [min_val, max_val], color='grey', linestyle='--', label='Diagonal (y=x)')

    # Add regression line
    if add_regression:
        sns.regplot(data=df, x=x_col, y=y_col, scatter=False, color='black', robust=True, ax=plt.gca(), label='Regression')
        
    
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add labels if label_col is provided and enabled
    if label_col and with_labels:
        adjust_text_labels(df, x_col, y_col, label_col, ax=plt.gca())
        
    plt.tight_layout()
    plt.show()


def plot_scatter_3d(df, x_col, y_col, z_col, group_col, appearance_dict,
                   title="", xlabel="", ylabel="", zlabel="", figsize=(12, 10)):
    """
    Create a 3D scatter plot colored by language group.
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with data to plot
    x_col : str
        Column name for x-axis
    y_col : str
        Column name for y-axis
    z_col : str
        Column name for z-axis
    group_col : str
        Column name for grouping/coloring
    appearance_dict : dict
        Dictionary mapping groups to colors
    title : str
        Plot title
    xlabel : str
        X-axis label
    ylabel : str
        Y-axis label
    zlabel : str
        Z-axis label
    figsize : tuple
        Figure size (width, height)
    """
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection='3d')
    
    for group in df[group_col].unique():
        group_data = df[df[group_col] == group]
        color = appearance_dict.get(group, 'gray')
        ax.scatter(group_data[x_col], group_data[y_col], group_data[z_col],
                  alpha=0.6, color=color, s=50, label=group)
    
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_zlabel(zlabel)
    ax.set_title(title)
    ax.legend(title="Language groups", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.show()


def plot_position_distribution(data, position_key, langNames, langnameGroup, 
                               appearance_dict, top_n=30):
    """
    Plot the distribution of a specific position type across languages.
    
    Parameters
    ----------
    data : dict
        Dictionary mapping languages to {position: value}
    position_key : str
        Position key to plot (e.g., 'right_1', 'left_2_totleft_3')
    langNames : dict
        Dictionary mapping language codes to full names
    langnameGroup : dict
        Dictionary mapping language names to groups
    appearance_dict : dict
        Dictionary mapping groups to colors
    top_n : int
        Number of top languages to display
    """
    # Extract data for this position
    lang_values = []
    for lang, positions in data.items():
        if position_key in positions:
            lang_name = langNames.get(lang, lang)
            group = langnameGroup.get(lang_name, 'Other')
            lang_values.append({
                'lang': lang,
                'lang_name': lang_name,
                'group': group,
                'value': positions[position_key]
            })
    
    # Sort and take top N
    lang_values.sort(key=lambda x: x['value'], reverse=True)
    lang_values = lang_values[:top_n]
    
    # Plot
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = [appearance_dict.get(item['group'], 'gray') for item in lang_values]
    lang_names = [item['lang_name'] for item in lang_values]
    values = [item['value'] for item in lang_values]
    
    bars = ax.barh(range(len(lang_names)), values, color=colors, alpha=0.7)
    ax.set_yticks(range(len(lang_names)))
    ax.set_yticklabels(lang_names)
    ax.set_xlabel('Average size (words)')
    ax.set_title(f'Distribution of position "{position_key}" across top {top_n} languages')
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def create_ie_palette(IElangnameGenus, appearance_dict):
    """
    Create color palette for Indo-European language genera.
    
    Parameters
    ----------
    IElangnameGenus : dict
        Dictionary mapping IE language names to genera
    appearance_dict : dict
        Dictionary with base colors
        
    Returns
    -------
    tuple
        (palette, genus_to_color) - seaborn palette and mapping dict
    """
    ie_genera = sorted(set(IElangnameGenus.values()))
    palette = sns.color_palette("husl", len(ie_genera))
    IEgenus_to_color = dict(zip(ie_genera, palette))
    
    return palette, IEgenus_to_color


def plot_dependency_sizes(pos1, pos2, prefix, all_langs_average_sizes_filtered, 
        filter_lang, langNames, langnameGroup, langname_group_or_genus=None, 
        folderprefix='', palette=None, group_to_color=None, with_labels=True, show_inline=True):
    """
    Plot the dependency sizes of two positions of dependents in a scatter plot.
    
    Parameters
    ----------
    pos1 : str
        First position key (x-axis)
    pos2 : str
        Second position key (y-axis)
    prefix : str
        Prefix for output filename (MAL, HCS, DIAG, etc.)
    all_langs_average_sizes_filtered : dict
        Dictionary of language -> position -> average size
    filter_lang : function
        Function to filter languages (returns True/False)
    langNames : dict
        Dictionary mapping language codes to full names
    langnameGroup : dict
        Dictionary mapping language names to groups
    langname_group_or_genus : dict, optional
        Mapping of language names to groups or genera
    folderprefix : str
        Prefix for output folders (e.g., 'IE-', 'noIE-')
    palette : dict, optional
        Color palette for groups/genera
    group_to_color : dict, optional
        Alternative color palette (for backward compatibility)
    with_labels : bool
        Whether to show labels on the plot (default True)
    show_inline : bool
        Whether to display plots inline (default True for interactive use, False for batch)
    """
    if langname_group_or_genus is None:
        langname_group_or_genus = langnameGroup
    if palette is None:
        palette = group_to_color if group_to_color is not None else {}
    
    # Generate filename based on naming convention
    def create_filename(pos_str):
        """Extract components from position string like 'right_1_totright_2'"""
        parts = pos_str.split('_')
        side = parts[0]  # 'right' or 'left'
        pos = parts[1]   # position number
        if len(parts) >= 3 and 'tot' in parts[2]:
            # Extract tot number from 'totright2' or 'totleft2'
            tot_part = parts[2]
            if len(parts) == 4:
                tot = parts[3]  # 'totright_2' format
            else:
                # Extract number from 'totright2' format
                tot = tot_part.replace('tot' + side, '')
            return side, pos, tot
        else:
            return side, pos, None
    
    side1, pos1_num, tot1 = create_filename(pos1)
    side2, pos2_num, tot2 = create_filename(pos2)
    
    # Create filename based on pattern type
    if prefix == 'MAL':
        # right pos1 tot 1 vs tot 2 MAL
        if tot1 and tot2:
            filename = f"{side1} pos {pos1_num} tot {tot1} vs tot {tot2} MAL"
        else:
            filename = f"{side1} {pos1} vs {pos2} MAL"
    elif prefix == 'HCS':
        # right tot2 pos1 vs pos2 HCS
        if tot1 and tot2:
            filename = f"{side1} tot {tot1} pos {pos1_num} vs pos {pos2_num} HCS"
        else:
            filename = f"{side1} {pos1} vs {pos2} HCS"
    elif prefix == 'DIAG':
        # right pos 1 tot 1 vs pos 2 tot 2 diag
        if tot1 and tot2:
            filename = f"{side1} pos {pos1_num} tot {tot1} vs pos {pos2_num} tot {tot2} DIAG"
        else:
            filename = f"{side1} {pos1} vs {pos2} DIAG"
    else:
        # Fallback to old format
        filename = f"{prefix}_{pos1}_vs_{pos2}"
    
    # Filter languages that have both positions and pass the filter
    pos1_pos2 = {}
    for lang, data in all_langs_average_sizes_filtered.items():
        # Determine if language should be included
        if callable(filter_lang):
            include_lang = filter_lang(lang)
        elif isinstance(filter_lang, (list, set, tuple)):
            include_lang = lang in filter_lang
        else:
            include_lang = True

        if include_lang and pos1 in data and pos2 in data:
            pos1_pos2[lang] = data
    
    if len(pos1_pos2) == 0:
        print(f"No languages have both {pos1} and {pos2}")
        return
    
    # Create DataFrame
    df = pd.DataFrame(pos1_pos2).T
    
    # Compute correlation and special cases
    try:
        corr = f'the Pearson correlation is: {round(df.corr()[pos1][pos2],2)}.'
        special_langs = (df[df[pos1] > df[pos2]]).index.map(lambda x: langNames.get(x, x))
        special = f'{pos1} value is bigger than the {pos2} value for {len(special_langs)} out of {len(df)} languages.'
    except:
        corr = 'No correlation could be computed.'
        special = ''
        special_langs = []
    
    # Add language names and groups
    df['language'] = df.index.map(lambda x: langNames.get(x, x))
    df['group'] = df.index.map(lambda x: langname_group_or_genus.get(langNames.get(x, x), 'Other'))
    df = df.sort_values('group')
    
    # Determine axis limits
    max_y = max(int(df[pos2].max() + 1), 10)
    max_x = max(max_y, int(df[pos1].max() + 1))
    
    # Create plot
    plt.figure(figsize=(max_x, max_y))
    plot = sns.scatterplot(data=df, x=pos1, y=pos2, hue='group', palette=palette)
    plt.xlim(0, max_x)
    plt.ylim(0, max_y)
    plt.xticks(range(max_x+1))
    plt.yticks(range(max_y+1))
    plt.legend(loc='lower right')
    
    # Add diagonal line
    plot.plot([0, max_y], [0, max_y], color='grey', linestyle='--')
    
    # Add title and subtitle using filename
    plt.title(filename, fontsize=16)
    plt.suptitle('\n'.join([corr, special]), fontsize=12, y=0)
    
    # Save no_labels plot (with diagonal line but no language labels)
    plot_path_no = f'plots/{folderprefix}scatters/{filename}_no_labels.png'
    os.makedirs(os.path.dirname(plot_path_no), exist_ok=True)
    plot.figure.savefig(plot_path_no, bbox_inches='tight')

    # Add language labels using adjustText
    if with_labels:
        adjust_text_labels(df, pos1, pos2, 'language', ax=plt.gca())
    
    # Add language list at bottom
    if len(special_langs) > 0:
        langs = ', '.join(special_langs)
        langs_lines = textwrap.wrap(langs, 150)
        for i, line in enumerate(langs_lines):
            plt.gca().text(0.5, -0.2 - i * 0.02, line, horizontalalignment='center', 
                          fontsize=7, transform=plt.gca().transAxes)
    
    # Save plot
    plot_path = f'plots/{folderprefix}scatters/{filename}.png'
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    plot.figure.savefig(plot_path, bbox_inches='tight')
    # print(f"✓ Saved plot: {plot_path} (labels={with_labels})")
    
    # Display the plot inline only if requested
    if show_inline:
        plt.show()
    else:
        plt.close()
    
    # Create new figure for regression plot with scatter points
    plt.figure(figsize=(max_x, max_y))
    plot = sns.scatterplot(data=df, x=pos1, y=pos2, hue='group', palette=palette)
    plt.xlim(0, max_x)
    plt.ylim(0, max_y)
    plt.xticks(range(max_x+1))
    plt.yticks(range(max_y+1))
    
    # Add diagonal line
    plot.plot([0, max_y], [0, max_y], color='grey', linestyle='--', label='Diagonal (y=x)')
    
    # Add regression line
    sns.regplot(data=df, x=pos1, y=pos2, scatter=False, color='black', robust=True, ax=plt.gca(), label='Regression')
    x = df[pos1]
    y = df[pos2]
    
    # Compute average factor (y/x ratio)
    avg_factor = (y / x).mean()
    
    # Compute Theil-Sen regression
    res = stats.theilslopes(y, x)
    regr = f" The trendline has slope {round(res[0],2)} and intercept {round(res[1],2)}."
    
    # Add average factor line from origin
    plot.plot([0, max_x], [0, max_x * avg_factor], color='blue', linestyle='--', 
             alpha=0.7, linewidth=2, label=f'Avg Ratio (y/x = {avg_factor:.2f})')
    
    # Update legend to include all lines
    # Get handles and labels from current axes
    handles, labels = plt.gca().get_legend_handles_labels()
    # Create proxy artist for regression if needed (regplot doesn't always label well)
    # But specifically ensure blue line is present
    
    # Organize legend: Groups first, then lines
    # Filter out duplicates if any
    by_label = dict(zip(labels, handles))
    
    # Add explicit black line for regression if missing
    if 'Regression' not in by_label:
        from matplotlib.lines import Line2D
        by_label['Regression'] = Line2D([0], [0], color='black', linewidth=2)
        
    plt.legend(by_label.values(), by_label.keys(), loc='lower right', fontsize=8)
    
    plt.title(f'{filename} regplot', fontsize=16)
    plt.suptitle('\n'.join([corr+regr, special]), fontsize=12, y=0)
    
    # Save no_labels regression plot (with all lines but no language labels)
    regplot_path_no = f'plots/{folderprefix}regscatters/{filename} regplot_no_labels.png'
    os.makedirs(os.path.dirname(regplot_path_no), exist_ok=True)
    plt.savefig(regplot_path_no, bbox_inches='tight')

    # Add language labels using adjustText
    if with_labels:
        adjust_text_labels(df, pos1, pos2, 'language', ax=plt.gca())
    
    # Add language list at bottom
    if len(special_langs) > 0:
        langs = ', '.join(special_langs)
        langs_lines = textwrap.wrap(langs, 150)
        for i, line in enumerate(langs_lines):
            plt.gca().text(0.5, -0.2 - i * 0.02, line, horizontalalignment='center', 
                          fontsize=7, transform=plt.gca().transAxes)
    
    # Save regression plot
    regplot_path = f'plots/{folderprefix}regscatters/{filename} regplot.png'
    os.makedirs(os.path.dirname(regplot_path), exist_ok=True)
    plt.savefig(regplot_path, bbox_inches='tight')
    # print(f"✓ Saved regression plot: {regplot_path}")
    
    # Display the regression plot inline only if requested
    if show_inline:
        plt.show()
    else:
        plt.close()


def plot_hcs_factor(pos1_key, pos2_key, prefix, all_langs_average_sizes_filtered, 
                     langNames, langnameGroup, group_to_color, output_folder='plots/factorhistograms',
                     filter_lang=None):
    """
    Compute and plot HCS factor for two positions.
    
    Parameters
    ----------
    pos1_key : str
        Key for position 1 (denominator)
    pos2_key : str
        Key for position 2 (numerator)
    prefix : str
        Prefix for the plot filename (MAL, HCS, DIAG)
    all_langs_average_sizes_filtered : dict
        Dictionary of language data
    langNames : dict
        Language code to name mapping
    langnameGroup : dict
        Language name to group mapping
    group_to_color : dict
        Group to color mapping
    output_folder : str
        Output folder for plots (default: 'plots/factorhistograms')
    filter_lang : function, optional
        Function to filter languages (returns True/False)
    
    Returns
    -------
    str
        Summary string with filename and average factor
    """
    import os
    os.makedirs(output_folder, exist_ok=True)
    
    # Compute HCS factor
    hcs_data = []
    for lang in all_langs_average_sizes_filtered:
        # Apply filter if provided
        if filter_lang is not None and not filter_lang(lang):
            continue
        lang_name = langNames.get(lang, lang)
        group = langnameGroup.get(lang_name, 'Unknown')
        
        if pos1_key in all_langs_average_sizes_filtered[lang] and pos2_key in all_langs_average_sizes_filtered[lang]:
            pos1_val = all_langs_average_sizes_filtered[lang][pos1_key]
            pos2_val = all_langs_average_sizes_filtered[lang][pos2_key]
            
            if pos1_val > 0:
                hcs_factor = pos2_val / pos1_val
                hcs_data.append({
                    'language_code': lang,
                    'language_name': lang_name,
                    'group': group,
                    pos1_key: pos1_val,
                    pos2_key: pos2_val,
                    'hcs_factor': hcs_factor
                })
    
    if len(hcs_data) == 0:
        print(f"No data for {prefix}: {pos1_key} vs {pos2_key}")
        return None
    
    # Create DataFrame
    hcs_df = pd.DataFrame(hcs_data)
    hcs_df = hcs_df.sort_values('hcs_factor')
    
    # Generate filename based on naming convention (same as plot_dependency_sizes)
    def create_filename(pos_str):
        """Extract components from position string like 'right_1_totright_2'"""
        parts = pos_str.split('_')
        side = parts[0]  # 'right' or 'left'
        pos = parts[1]   # position number
        if len(parts) >= 3 and 'tot' in parts[2]:
            # Extract tot number from 'totright2' or 'totleft2'
            tot_part = parts[2]
            if len(parts) == 4:
                tot = parts[3]  # 'totright_2' format
            else:
                # Extract number from 'totright2' format
                tot = tot_part.replace('tot' + side, '')
            return side, pos, tot
        else:
            return side, pos, None
    
    side1, pos1_num, tot1 = create_filename(pos1_key)
    side2, pos2_num, tot2 = create_filename(pos2_key)
    
    # Create filename based on pattern type
    if prefix == 'MAL':
        # right pos1 tot 1 vs tot 2 MAL
        if tot1 and tot2:
            filename = f"{side1} pos {pos1_num} tot {tot1} vs tot {tot2} MAL"
        else:
            filename = f"{side1} {pos1_key} vs {pos2_key} MAL"
    elif prefix == 'HCS':
        # right tot2 pos1 vs pos2 HCS
        if tot1 and tot2:
            filename = f"{side1} tot {tot1} pos {pos1_num} vs pos {pos2_num} HCS"
        else:
            filename = f"{side1} {pos1_key} vs {pos2_key} HCS"
    elif prefix == 'DIAG':
        # right pos 1 tot 1 vs pos 2 tot 2 diag
        if tot1 and tot2:
            filename = f"{side1} pos {pos1_num} tot {tot1} vs pos {pos2_num} tot {tot2} DIAG"
        else:
            filename = f"{side1} {pos1_key} vs {pos2_key} DIAG"
    else:
        filename = f"{prefix} {pos1_key} vs {pos2_key}"
    
    # Create plot
    fig, ax = plt.subplots(1, 1, figsize=(20, 10))
    
    colors = [group_to_color.get(group, '#888888') for group in hcs_df['group']]
    bars = ax.bar(range(len(hcs_df)), hcs_df['hcs_factor'], color=colors)
    
    # Compute and display average HCS factor and standard deviation
    avg_hcs_factor = hcs_df['hcs_factor'].mean()
    std_hcs_factor = hcs_df['hcs_factor'].std()
    ax.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='HCS factor = 1.0')
    ax.axhline(y=avg_hcs_factor, color='blue', linestyle='--', alpha=0.7, linewidth=2, 
               label=f'Average = {avg_hcs_factor:.3f}, StdDev = {std_hcs_factor:.3f}')
    
    ax.set_xlabel('Languages (sorted by HCS factor)', fontsize=14)
    ax.set_ylabel(f'HCS Factor ({pos2_key} / {pos1_key})', fontsize=14)
    ax.set_title(f'{filename}', fontsize=16)
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    
    # Add language names below bars
    ax.set_xticks(range(len(hcs_df)))
    ax.set_xticklabels(hcs_df['language_name'], rotation=90, fontsize=8, ha='center')
    
    plt.tight_layout()
    filepath = f'{output_folder}/{filename}.png'
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()
    
    return f"{filename}, avg={avg_hcs_factor:.4f}"


def _plot_head_init_factor_task(args):
    """Helper function for parallel plotting of head-initiality vs factor."""
    factor_col, df_valid, subset_name, group_to_color, output_folder = args
    
    # Apply subset filter
    if subset_name == 'all':
        df_plot = df_valid
    elif subset_name == 'headInit':
        df_plot = df_valid[df_valid['head_initiality'] > 50]
    elif subset_name == 'headFinal':
        df_plot = df_valid[df_valid['head_initiality'] <= 50]
    else:
        df_plot = df_valid
    
    if len(df_plot) < 3:
        return None
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Create scatter plot using seaborn for consistency
    sns.scatterplot(
        data=df_plot, 
        x='head_initiality', 
        y=factor_col, 
        hue='group', 
        palette=group_to_color,
        ax=ax,
        legend=True 
    )
    
    # Compute correlation
    from scipy.stats import pearsonr, spearmanr
    r_pearson, p_pearson = pearsonr(df_plot['head_initiality'], df_plot[factor_col])
    r_spearman, p_spearman = spearmanr(df_plot['head_initiality'], df_plot[factor_col])
    
    # Add regression line
    from sklearn.linear_model import TheilSenRegressor
    X = df_plot['head_initiality'].values.reshape(-1, 1)
    y = df_plot[factor_col].values
    regressor = TheilSenRegressor(random_state=42)
    regressor.fit(X, y)
    x_trend = np.linspace(df_plot['head_initiality'].min(), df_plot['head_initiality'].max(), 100).reshape(-1, 1)
    y_trend = regressor.predict(x_trend)
    ax.plot(x_trend, y_trend, 'r-', alpha=0.7, linewidth=2.5, 
           label=f'Trendline: y={regressor.coef_[0]:.4f}x+{regressor.intercept_:.4f}')
    
    # Labels and title
    ax.set_xlabel('Head-Initiality (%)', fontsize=14)
    ax.set_ylabel(f'{factor_col}', fontsize=14)
    
    title_prefix = {'all': 'All Languages', 'headInit': 'Head-Initial Languages', 
                   'headFinal': 'Head-Final Languages'}[subset_name]
    ax.set_title(f'{title_prefix}: Head-Initiality vs {factor_col}', fontsize=16)
    
    # Add correlation info
    ax.text(0.02, 0.98, f'Pearson r={r_pearson:.3f} (p={p_pearson:.4f})\nSpearman ρ={r_spearman:.3f} (p={p_spearman:.4f})\nN={len(df_plot)}',
           transform=ax.transAxes, fontsize=11, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax.grid(alpha=0.3)
    ax.grid(alpha=0.3)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    
    
    # Save plot
    safe_filename = factor_col.replace('/', '_').replace(' ', '_')
    output_base = f'{output_folder}/{subset_name}/{safe_filename}'
    
    # 1. Save no_labels version
    os.makedirs(os.path.dirname(output_base), exist_ok=True)
    plt.savefig(f'{output_base}_no_labels.png', dpi=300, bbox_inches='tight')
    
    # Add labels
    # Check if we have language name column
    label_col = 'language_name' if 'language_name' in df_plot.columns else 'language_code'
    if label_col in df_plot.columns:
        adjust_text_labels(df_plot, 'head_initiality', factor_col, label_col, ax=ax)
    
    plt.tight_layout()
    plt.savefig(f'{output_base}.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    return f"{subset_name}/{safe_filename}.png"


def plot_head_initiality_vs_factors(all_factors_df, group_to_color, 
                                      output_folder='plots/head_init_vs_factors',
                                      parallel=True):
    """
    Create scatter plots showing relationship between head-initiality and each factor.
    
    Creates three versions: all languages, head-initial only, head-final only.
    
    Parameters
    ----------
    all_factors_df : pandas.DataFrame
        DataFrame with head_initiality and all linguistic factors
    group_to_color : dict
        Mapping of language groups to colors
    output_folder : str
        Base output folder for plots
    parallel : bool
        Whether to use parallel processing (default True)
    """
    import os
    from multiprocessing import Pool, cpu_count
    
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(f"{output_folder}/all", exist_ok=True)
    os.makedirs(f"{output_folder}/headInit", exist_ok=True)
    os.makedirs(f"{output_folder}/headFinal", exist_ok=True)
    
    # Get all factor columns (exclude metadata columns)
    factor_columns = [col for col in all_factors_df.columns 
                      if col not in ['language_code', 'language_name', 'group', 'head_initiality']]
    
    print(f"Generating {len(factor_columns) * 3} scatter plots (3 versions per factor)...")
    
    # Build list of all plot tasks
    tasks = []
    for factor_col in factor_columns:
        # Filter out NaN values
        df_valid = all_factors_df.dropna(subset=['head_initiality', factor_col])
        
        if len(df_valid) < 3:  # Need at least 3 points for meaningful plot
            continue
        
        # Create three plots: all, head-initial, head-final
        for subset_name in ['all', 'headInit', 'headFinal']:
            tasks.append((factor_col, df_valid, subset_name, 
                         group_to_color, output_folder))
    
    print(f"Total tasks: {len(tasks)}")
    
    if parallel:
        # Use multiprocessing for parallel execution
        num_cores = cpu_count()
        print(f"Using {num_cores} CPU cores for parallel processing")
        
        results = []
        with Pool(processes=num_cores) as pool:
            for result in tqdm(pool.imap(_plot_head_init_factor_task, tasks), total=len(tasks), desc="Generating Head-Init Plots"):
                results.append(result)
        
        # Filter out None results (plots that were skipped)
        successful_results = [r for r in results if r is not None]
        print(f"\n✅ Completed {len(successful_results)} scatter plots in {output_folder}/")
    else:
        # Sequential execution
        successful_results = []
        for i, task in enumerate(tasks):
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{len(tasks)}")
            result = _plot_head_init_factor_task(task)
            if result is not None:
                successful_results.append(result)
        
        print(f"\n✅ Completed {len(successful_results)} scatter plots in {output_folder}/")
    
    return successful_results


def adjust_text_labels(df, x_col, y_col, label_col, ax=None):
    """
    Adjust text labels to avoid overlap using adjustText.
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing coordinates and labels
    x_col : str
        Column name for x coordinates
    y_col : str
        Column name for y coordinates
    label_col : str
        Column name for text labels
    ax : matplotlib.axes.Axes, optional
        Axes object to draw on
    """
    try:
        from adjustText import adjust_text
    except ImportError:
        # Fallback to local import if installed as module fails
        try:
            import adjustText
            from adjustText import adjust_text
        except ImportError:
            print("Warning: adjustText not found. Labels may overlap.")
            return

    if ax is None:
        ax = plt.gca()
        
    texts = []
    for _, row in df.iterrows():
        # Only label points that are valid
        if pd.notna(row[x_col]) and pd.notna(row[y_col]):
            texts.append(ax.text(row[x_col], row[y_col], str(row[label_col]), 
                                fontsize=9, alpha=0.8))
    
    if texts:
        # print(f"  Adjusting {len(texts)} labels with arrows...", flush=True)
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle='-', color='gray', alpha=0.5, lw=0.5))


def _plot_sv_vs_vo_task(args):
    """
    Worker function for parallel SV vs VO plot generation.
    
    Parameters
    ----------
    args : tuple
        (df, lang_filter, title, filename_prefix, group_to_color, plots_dir)
    
    Returns
    -------
    str
        Path to generated plot file
    """
    df, lang_filter, title, filename_prefix, group_to_color, plots_dir = args
    
    # Filter data
    plot_df = df.copy()
    
    if lang_filter is not None:
        plot_df = plot_df[plot_df['language_code'].isin(lang_filter)]
    
    # Remove rows with missing scores
    plot_df = plot_df.dropna(subset=['sv_score', 'vo_score'])
    
    if len(plot_df) == 0:
        return None
    
    # Create figure
    plt.figure(figsize=(12, 10))
    
    # Create scatter plot
    scatter = sns.scatterplot(
        data=plot_df,
        x='sv_score',
        y='vo_score',
        hue='group',
        palette=group_to_color,
        s=80,
        alpha=0.7
    )
    
    # Add reference lines
    plt.axhline(y=0.666, color='red', linestyle='--', alpha=0.3, label='VO threshold (66.6%)')
    plt.axhline(y=0.333, color='blue', linestyle='--', alpha=0.3, label='OV threshold (33.3%)')
    plt.axvline(x=0.666, color='red', linestyle='--', alpha=0.3, label='VS threshold (66.6%)')
    plt.axvline(x=0.333, color='blue', linestyle='--', alpha=0.3, label='SV threshold (33.3%)')
    
    # Add diagonal for reference
    plt.plot([0, 1], [0, 1], 'k--', alpha=0.2, label='Diagonal')
    
    # Labels and title
    plt.xlabel('VS Score (proportion of subjects after verb)', fontsize=12)
    plt.ylabel('VO Score (proportion of objects after verb)', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlim(-0.05, 1.05)
    plt.ylim(-0.05, 1.05)
    
    # Update legend
    handles, labels = plt.gca().get_legend_handles_labels()
    plt.legend(handles=handles, labels=labels, loc='best', fontsize=9)
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save plot without labels
    output_dir = os.path.join(plots_dir, 'sv_vs_vo')
    os.makedirs(output_dir, exist_ok=True)
    output_path_no_labels = os.path.join(output_dir, f'{filename_prefix}vs_vs_vo_scatter_no_labels.png')
    plt.savefig(output_path_no_labels, dpi=150, bbox_inches='tight')
    
    # Add language labels using adjustText (same as other plots)
    adjust_text_labels(plot_df, 'sv_score', 'vo_score', 'language_name', ax=plt.gca())
    
    # Save plot with labels
    output_path = os.path.join(output_dir, f'{filename_prefix}vs_vs_vo_scatter.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    
    plt.close()
    
    # Compute statistics
    corr = plot_df['sv_score'].corr(plot_df['vo_score'])
    
    # Count by quadrants
    vo_high = plot_df['vo_score'] > 0.666
    vo_low = plot_df['vo_score'] < 0.333
    vs_high = plot_df['sv_score'] > 0.666  # Subjects after verb
    vs_low = plot_df['sv_score'] < 0.333   # Subjects before verb (SV)
    
    stats = {
        'title': title,
        'n_langs': len(plot_df),
        'mean_vs': plot_df['sv_score'].mean(),
        'mean_vo': plot_df['vo_score'].mean(),
        'correlation': corr,
        'vo_vs': (vo_high & vs_high).sum(),
        'vo_sv': (vo_high & vs_low).sum(),
        'ov_vs': (vo_low & vs_high).sum(),
        'ov_sv': (vo_low & vs_low).sum(),
    }
    
    return output_path, stats


def plot_sv_vs_vo_scatter_batch(df, language_filters, group_to_color, plots_dir='plots', parallel=True):
    """
    Create VS vs VO scatterplots for multiple language groups in parallel.
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with sv_score, vo_score, language_code, language_name, and group columns
    language_filters : list of tuples
        List of (title, filename_prefix, lang_filter_set) tuples
    group_to_color : dict
        Mapping of language groups to colors
    plots_dir : str
        Base directory for plots
    parallel : bool
        Whether to use parallel processing (default True)
    
    Returns
    -------
    list
        List of (output_path, stats_dict) tuples for successful plots
    """
    from multiprocessing import Pool, cpu_count
    
    # Build list of tasks
    tasks = []
    for title, filename_prefix, lang_filter in language_filters:
        tasks.append((df, lang_filter, title, filename_prefix, group_to_color, plots_dir))
    
    print(f"Generating {len(tasks)} VS vs VO scatterplots...")
    
    if parallel:
        # Use multiprocessing for parallel execution
        num_cores = max(1, cpu_count() - 1)
        print(f"Using {num_cores} CPU cores for parallel processing")
        
        results = []
        with Pool(processes=num_cores) as pool:
            for result in tqdm(pool.imap(_plot_sv_vs_vo_task, tasks), total=len(tasks), desc="Generating VS vs VO plots"):
                results.append(result)
        
        # Filter out None results (plots that were skipped)
        successful_results = [r for r in results if r is not None]
        print(f"\n✅ Completed {len(successful_results)} VS vs VO plots")
    else:
        # Sequential execution
        successful_results = []
        for task in tqdm(tasks, desc="Generating VS vs VO plots"):
            result = _plot_sv_vs_vo_task(task)
            if result is not None:
                successful_results.append(result)
        print(f"\n✅ Completed {len(successful_results)} VS vs VO plots")
    
    # Print statistics for all plots
    print("\n" + "="*80)
    print("VS vs VO Analysis Statistics")
    print("="*80)
    for output_path, stats in successful_results:
        print(f"\n{stats['title']}:")
        print(f"  Total languages: {stats['n_langs']}")
        print(f"  Mean VS score: {stats['mean_vs']:.3f}")
        print(f"  Mean VO score: {stats['mean_vo']:.3f}")
        print(f"  Correlation: {stats['correlation']:.3f}")
        print(f"  VO & VS (both >66.6%): {stats['vo_vs']}")
        print(f"  VO & SV (VO>66.6%, VS<33.3%): {stats['vo_sv']}")
        print(f"  OV & VS (VO<33.3%, VS>66.6%): {stats['ov_vs']}")
        print(f"  OV & SV (both <33.3%): {stats['ov_sv']}")
    
    return successful_results


def plot_vo_vs_vo_nominal_scatter(df, lang_filter=None, title="VO vs VOnominal Scores", 
                                   filename="vo_vs_vo_nominal.png", group_to_color=None, 
                                   plots_dir='plots'):
    """
    Create a scatterplot comparing VO score (all objects) vs VOnominal score (NOUN objects only).
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with vo_score, vo_nominal_score, language_code, language_name, and group columns
    lang_filter : set, optional
        Set of language codes to include (if None, use all)
    title : str
        Plot title
    filename : str
        Output filename
    group_to_color : dict
        Mapping of language groups to colors
    plots_dir : str
        Base directory for plots
    
    Returns
    -------
    tuple
        (output_path, stats_dict) or None if no data
    """
    # Filter data
    plot_df = df.copy()
    
    if lang_filter is not None:
        plot_df = plot_df[plot_df['language_code'].isin(lang_filter)]
    
    # Remove rows with missing scores
    plot_df = plot_df.dropna(subset=['vo_score', 'vo_nominal_score'])
    
    if len(plot_df) == 0:
        print(f"No data to plot for {title}")
        return None
    
    # Create figure
    plt.figure(figsize=(12, 10))
    
    # Create scatter plot
    scatter = sns.scatterplot(
        data=plot_df,
        x='vo_score',
        y='vo_nominal_score',
        hue='group',
        palette=group_to_color,
        s=80,
        alpha=0.7
    )
    
    # Add reference lines for classification thresholds
    plt.axhline(y=0.666, color='red', linestyle='--', alpha=0.3, label='VO threshold (66.6%)')
    plt.axhline(y=0.333, color='blue', linestyle='--', alpha=0.3, label='OV threshold (33.3%)')
    plt.axvline(x=0.666, color='red', linestyle='--', alpha=0.3)
    plt.axvline(x=0.333, color='blue', linestyle='--', alpha=0.3)
    
    # Add diagonal for reference
    plt.plot([0, 1], [0, 1], 'k--', alpha=0.3, linewidth=2, label='Diagonal (y=x)')
    
    # Labels and title
    plt.xlabel('VO Score (all objects)', fontsize=12)
    plt.ylabel('VOnominal Score (NOUN objects only)', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlim(-0.05, 1.05)
    plt.ylim(-0.05, 1.05)
    
    # Update legend
    handles, labels = plt.gca().get_legend_handles_labels()
    plt.legend(handles=handles, labels=labels, loc='best', fontsize=9)
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save plot without labels
    output_dir = os.path.join(plots_dir, 'vo_vs_vo_nominal')
    os.makedirs(output_dir, exist_ok=True)
    output_path_no_labels = os.path.join(output_dir, filename.replace('.png', '_no_labels.png'))
    plt.savefig(output_path_no_labels, dpi=150, bbox_inches='tight')
    print(f"Saved (no labels): {output_path_no_labels}")
    
    # Add language labels using adjustText
    adjust_text_labels(plot_df, 'vo_score', 'vo_nominal_score', 'language_name', ax=plt.gca())
    
    # Save plot with labels
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved (with labels): {output_path}")
    
    plt.show()
    
    # Compute statistics
    corr = plot_df['vo_score'].corr(plot_df['vo_nominal_score'])
    
    # Count differences (languages where scores differ significantly)
    plot_df['diff'] = abs(plot_df['vo_score'] - plot_df['vo_nominal_score'])
    significant_diff = plot_df[plot_df['diff'] > 0.1]
    
    print(f"\nStatistics for {title}:")
    print(f"  Total languages: {len(plot_df)}")
    print(f"  Mean VO score: {plot_df['vo_score'].mean():.3f}")
    print(f"  Mean VOnominal score: {plot_df['vo_nominal_score'].mean():.3f}")
    print(f"  Correlation: {corr:.3f}")
    print(f"  Languages with >10% difference: {len(significant_diff)}")
    
    if len(significant_diff) > 0:
        print(f"\n  Top differences (VO - VOnominal):")
        top_diffs = plot_df.nlargest(5, 'diff')[['language_name', 'vo_score', 'vo_nominal_score', 'diff']]
        for _, row in top_diffs.iterrows():
            print(f"    {row['language_name']}: VO={row['vo_score']:.3f}, VOnominal={row['vo_nominal_score']:.3f}, diff={row['diff']:.3f}")
    
    stats = {
        'title': title,
        'n_langs': len(plot_df),
        'mean_vo': plot_df['vo_score'].mean(),
        'mean_vo_nominal': plot_df['vo_nominal_score'].mean(),
        'correlation': corr,
        'n_significant_diff': len(significant_diff)
    }
    
    return output_path, stats


def _plot_task(args):
    """Helper function for parallel plotting."""
    (pos1_str, pos2_str, prefix, all_langs_average_sizes_filtered, 
     filter_lang, langNames, langnameGroup, langname_group_or_genus, 
     folderprefix, palette) = args
    
    # Check if data exists for these positions
    has_data = False
    for lang in all_langs_average_sizes_filtered:
        # Determine if language should be included
        if callable(filter_lang):
            include_lang = filter_lang(lang)
        elif isinstance(filter_lang, (list, set, tuple)):
            include_lang = lang in filter_lang
        else:
            include_lang = True # Default to True if None or unknown type (though should handle None at call site)

        if include_lang:
            if pos1_str in all_langs_average_sizes_filtered[lang] and pos2_str in all_langs_average_sizes_filtered[lang]:
                has_data = True
                break
    
    if not has_data:
        return f"Skipped (no data): {prefix} {pos1_str} vs {pos2_str}"

    plot_dependency_sizes(
        pos1_str, 
        pos2_str, 
        prefix,
        all_langs_average_sizes_filtered,  
        filter_lang=filter_lang,
        langNames=langNames,
        langnameGroup=langnameGroup,
        langname_group_or_genus=langname_group_or_genus,               
        folderprefix=folderprefix, 
        palette=palette,
        group_to_color=palette,
        with_labels=True,
        show_inline=False  # Don't show inline for batch processing
    )
    return f"{prefix}: {pos1_str} vs {pos2_str}"



def plot_all(all_langs_average_sizes_filtered, langNames, langnameGroup, 
             filter_lang=None, langname_group_or_genus=None, folderprefix='', palette=None, parallel=True):
    """
    Plot all dependency size comparisons.
    
    Parameters
    ----------
    all_langs_average_sizes_filtered : dict
        Data dictionary
    langNames : dict
        Language names mapping
    langnameGroup : dict
        Language group mapping
    filter_lang : function or iterable, optional
        Function to filter languages OR a set/list of allowed language codes. 
        If None, includes all languages.
    langname_group_or_genus : dict
        Mapping of language names to groups or genera
    folderprefix : str
        Prefix for output folders
    palette : dict
        Color palette
    parallel : bool
        Whether to use parallel processing (default True)
    """
    if filter_lang is None:
        filter_lang = _always_true

    if langname_group_or_genus is None:
        langname_group_or_genus = langnameGroup
    
    print(f'_________________________ plotting all ___________________________ {folderprefix}')
    
    measures = [
        ('MAL', 'right_{k}_totright_{m}', 'right_{k}_totright_{n}', [1,5], [1,5]), # MAL comparison
        ('MAL', 'left_{k}_totleft_{m}', 'left_{k}_totleft_{n}', [1,5], [1,5]), # MAL left side
        ('HCS', 'right_{j}_totright_{n}', 'right_{k}_totright_{n}', [2,6], [2,6]), # HCS comparison
        ('HCS', 'left_{j}_totleft_{n}', 'left_{k}_totleft_{n}', [2,6], [2,6]), # HCS left side - j < k, so j on x-axis
        ('DIAG', 'right_{k}_totright_{n}', 'right_{l}_totright_{m}', [1,5], [1,5]), # Diagonal comparison
        ('DIAG', 'left_{k}_totleft_{n}', 'left_{l}_totleft_{m}', [1,5], [1,5]), # Diagonal left side
    ]
    
    # Build list of all plot tasks
    tasks = []
    for (prefix, pos1, pos2, n_range, k_range) in measures:
        for n in range(*n_range):
            for k in range(*k_range):
                if k <= n:
                    m = n + 1
                    j = k - 1
                    l = k + 1
                    pos1_str = pos1.format(n=n, k=k, m=m, j=j, l=l)
                    pos2_str = pos2.format(n=n, k=k, m=m, j=j, l=l)
                    
                    tasks.append((
                        pos1_str, pos2_str, prefix, all_langs_average_sizes_filtered,
                        filter_lang, langNames, langnameGroup, langname_group_or_genus,
                        folderprefix, palette
                    ))
    
    print(f"Total plots to generate: {len(tasks)}")
    
    if parallel:
        # Use multiprocessing for parallel execution
        # Use fewer cores than max to avoid overloading if running on shared machine, or just use cpu_count
        num_cores = max(1, cpu_count() - 1) 
        print(f"Using {num_cores} CPU cores for parallel processing")
        
        results = []
        with Pool(processes=num_cores) as pool:
            # Use imap to get results as they complete for tqdm
            for result in tqdm(pool.imap(_plot_task, tasks), total=len(tasks), desc="Generating plots"):
                results.append(result)
        
        print(f"\\n✅ Completed {len(results)} plots")
    else:
        # Sequential execution
        results = []
        for task in tqdm(tasks, desc="Generating plots"):
            results.append(_plot_task(task))

def plot_bastard_vs_vo_score(df, group_to_color, plots_dir='plots', title='Bastard Percentage vs. VO Score', filename='bastard_vs_vo_score.png'):
    """
    Create a scatterplot comparing Bastard Percentage vs VO Score with standard styling.
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame with 'vo_score', 'Bastards_per_Verb_Pct', 'Language', 'group' columns
    group_to_color : dict
        Mapping of language groups to colors
    plots_dir : str
        Base directory for plots
    title : str
        Plot title
    filename : str
        Output filename
    
    Returns
    -------
    str
        Path to generated plot file
    """
    import os
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # Filter data
    plot_df = df.copy()
    plot_df = plot_df.dropna(subset=['vo_score', 'Bastards_per_Verb_Pct'])
    
    if len(plot_df) == 0:
        print(f"No data to plot for {title}")
        return None
        
    # Create figure
    plt.figure(figsize=(12, 10))
    
    # Create scatter plot
    sns.scatterplot(
        data=plot_df,
        x='vo_score',
        y='Bastards_per_Verb_Pct',
        hue='group',
        palette=group_to_color,
        s=80,
        alpha=0.8,
        edgecolor='w', 
        linewidth=0.5
    )
    
    # Add reference lines for VO/OV
    plt.axvline(x=0.666, color='red', linestyle='--', alpha=0.3, label='VO threshold (66.6%)')
    plt.axvline(x=0.333, color='blue', linestyle='--', alpha=0.3, label='OV threshold (33.3%)')
    plt.axvline(x=0.5, color='gray', linestyle=':', alpha=0.5)
    
    # Labels and title
    plt.xlabel('VO Score (Higher = more Verb-Object order)', fontsize=12)
    plt.ylabel('Bastard Dependencies (%)', fontsize=12)
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlim(-0.05, 1.05)
    # Y-axis auto-scaled but start at 0
    plt.ylim(bottom=0)
    
    # Legend
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='Language Family')
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save plot without labels
    output_dir = os.path.join(plots_dir, 'bastard_analysis')
    os.makedirs(output_dir, exist_ok=True)
    output_path_no_labels = os.path.join(output_dir, f'{os.path.splitext(filename)[0]}_no_labels.png')
    plt.savefig(output_path_no_labels, dpi=300, bbox_inches='tight')
    
    # Add language labels using adjustText
    # Use 'Language' column for labels if present, else 'Code' or 'language'
    label_col = 'Language' if 'Language' in plot_df.columns else 'language'
    if label_col not in plot_df.columns and 'Code' in plot_df.columns:
        label_col = 'Code'
        
    if label_col in plot_df.columns:
        adjust_text_labels(plot_df, 'vo_score', 'Bastards_per_Verb_Pct', label_col, ax=plt.gca())
    
    # Save plot with labels
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    # Show plot
    plt.show()
    plt.close()
    
    print(f"Saved plot to {output_path}")
    return output_path

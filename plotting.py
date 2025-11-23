"""
Plotting and visualization functions for dependency analysis results.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import textwrap
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import Axes3D
from scipy import stats


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
                   title="", xlabel="", ylabel="", figsize=(10, 8)):
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
    """
    plt.figure(figsize=figsize)
    
    groups_plotted = set()
    for group in df[group_col].unique():
        group_data = df[df[group_col] == group]
        color = appearance_dict.get(group, 'gray')
        plt.scatter(group_data[x_col], group_data[y_col], 
                   alpha=0.6, color=color, s=50, label=group)
        groups_plotted.add(group)
    
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend(title="Language groups", bbox_to_anchor=(1.05, 1), loc='upper left')
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
        folderprefix='', palette=None, group_to_color=None, show_inline=True):
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
            filename = f"{side1} pos {pos1_num} tot {tot1} vs pos {pos2_num} tot {tot2} diag"
        else:
            filename = f"{side1} {pos1} vs {pos2} diag"
    else:
        # Fallback to old format
        filename = f"{prefix}_{pos1}_vs_{pos2}"
    
    # Filter languages that have both positions and pass the filter
    pos1_pos2 = {
        lang: all_langs_average_sizes_filtered[lang] 
        for lang in all_langs_average_sizes_filtered 
        if pos1 in all_langs_average_sizes_filtered[lang] 
        and pos2 in all_langs_average_sizes_filtered[lang]
        and filter_lang(lang)
    }
    
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
    
    # Add language labels
    for line in df.itertuples():
        color = palette.get(line.group, 'gray')
        plot.text(getattr(line, pos1), getattr(line, pos2), line.language, 
                 horizontalalignment='left', size='large', color=color, alpha=1)
    
    # Add diagonal line
    plot.plot([0, max_y], [0, max_y], color='grey', linestyle='--')
    
    # Add title and subtitle
    plt.title(f'{prefix} - {pos1} vs {pos2} dependency sizes', fontsize=16)
    plt.suptitle('\n'.join([corr, special]), fontsize=12, y=0)
    
    # Add language list at bottom
    if len(special_langs) > 0:
        langs = ', '.join(special_langs)
        langs_lines = textwrap.wrap(langs, 150)
        for i, line in enumerate(langs_lines):
            plt.gca().text(0.5, -0.2 - i * 0.02, line, horizontalalignment='center', 
                          fontsize=7, transform=plt.gca().transAxes)
    
    # Save plot
    plot_path = f'{folderprefix}plots/{filename}.png'
    plot.figure.savefig(plot_path, bbox_inches='tight')
    print(f"✓ Saved plot: {plot_path}")
    
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
    plt.legend(loc='lower right')
    
    # Add language labels
    for line in df.itertuples():
        color = palette.get(line.group, 'gray')
        plot.text(getattr(line, pos1), getattr(line, pos2), line.language, 
                 horizontalalignment='left', size='large', color=color, alpha=1)
    
    # Add diagonal line
    plot.plot([0, max_y], [0, max_y], color='grey', linestyle='--')
    
    # Add regression line
    sns.regplot(data=df, x=pos1, y=pos2, scatter=False, color='black', robust=True, ax=plt.gca())
    x = df[pos1]
    y = df[pos2]
    
    # Compute Theil-Sen regression
    res = stats.theilslopes(y, x)
    regr = f" The trendline has slope {round(res[0],2)} and intercept {round(res[1],2)}."
    
    plt.title(f'with trendline: {prefix} - {pos1} vs {pos2} dependency sizes', fontsize=16)
    plt.suptitle('\n'.join([corr+regr, special]), fontsize=12, y=0)
    
    # Add language list at bottom
    if len(special_langs) > 0:
        langs = ', '.join(special_langs)
        langs_lines = textwrap.wrap(langs, 150)
        for i, line in enumerate(langs_lines):
            plt.gca().text(0.5, -0.2 - i * 0.02, line, horizontalalignment='center', 
                          fontsize=7, transform=plt.gca().transAxes)
    
    # Save regression plot
    regplot_path = f'{folderprefix}regplots/{filename} regplot.png'
    plt.savefig(regplot_path, bbox_inches='tight')
    print(f"✓ Saved regression plot: {regplot_path}")
    
    # Display the regression plot inline only if requested
    if show_inline:
        plt.show()
    else:
        plt.close()

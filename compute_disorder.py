"""
Module for computing disorder percentages in dependency size sequences.

For each configuration (e.g., R tot=4 with positions 1,2,3,4), we check whether
the sizes are strictly monotonically increasing. If not, the sequence is "disordered".
"""

import pandas as pd
import numpy as np


def compute_disorder_per_language(all_langs_average_sizes):
    """
    For each language and each configuration, compute whether the sequence is ordered.
    
    Parameters
    ----------
    all_langs_average_sizes : dict
        Dictionary: lang -> position_key -> average_size
        
    Returns
    -------
    disorder_data : dict
        Dictionary: (lang, side, tot) -> is_disordered (bool)
    """
    disorder_data = {}
    
    for lang, positions in all_langs_average_sizes.items():
        # Check right side configurations
        for tot in [1, 2, 3, 4]:
            sizes = []
            for pos in range(1, tot + 1):
                key = f'right_{pos}_totright_{tot}'
                if key in positions:
                    sizes.append(positions[key])
                else:
                    sizes.append(None)
            
            # Check if strictly increasing (ordered)
            if len(sizes) > 1 and all(s is not None for s in sizes):
                is_ordered = all(sizes[i] < sizes[i+1] for i in range(len(sizes)-1))
                disorder_data[(lang, 'right', tot)] = not is_ordered
        
        # Check left side configurations
        for tot in [1, 2, 3, 4]:
            sizes = []
            # For left side, position 1 is closest to verb, higher positions are farther
            # In display order (farthest to closest): we want sizes decreasing toward verb
            for pos in range(tot, 0, -1):
                key = f'left_{pos}_totleft_{tot}'
                if key in positions:
                    sizes.append(positions[key])
                else:
                    sizes.append(None)
            
            # Check if strictly decreasing (ordered for left side display)
            if len(sizes) > 1 and all(s is not None for s in sizes):
                is_ordered = all(sizes[i] > sizes[i+1] for i in range(len(sizes)-1))
                disorder_data[(lang, 'left', tot)] = not is_ordered
    
    return disorder_data


def compute_disorder_percentages(disorder_data):
    """
    Compute percentage of disordered languages for each configuration.
    
    Parameters
    ----------
    disorder_data : dict
        Dictionary: (lang, side, tot) -> is_disordered (bool)
        
    Returns
    -------
    disorder_percentages : dict
        Dictionary: (side, tot) -> percentage of disordered languages
    """
    disorder_percentages = {}
    
    # Group by (side, tot)
    config_groups = {}
    for (lang, side, tot), is_disordered in disorder_data.items():
        key = (side, tot)
        if key not in config_groups:
            config_groups[key] = []
        config_groups[key].append(is_disordered)
    
    # Compute percentage for each configuration
    for (side, tot), disordered_list in config_groups.items():
        if len(disordered_list) > 0:
            pct = 100.0 * sum(disordered_list) / len(disordered_list)
            disorder_percentages[(side, tot)] = pct
        else:
            disorder_percentages[(side, tot)] = None
    
    return disorder_percentages


def create_disorder_dataframe(disorder_data, langNames, langnameGroup):
    """
    Create a DataFrame with disorder information for each language and configuration.
    
    Parameters
    ----------
    disorder_data : dict
        Dictionary: (lang, side, tot) -> is_disordered (bool)
    langNames : dict
        Language code to name mapping
    langnameGroup : dict
        Language name to group mapping
        
    Returns
    -------
    df : pd.DataFrame
        DataFrame with columns: language_code, language_name, group, 
        right_tot_1_disordered, right_tot_2_disordered, ..., left_tot_4_disordered
    """
    # Organize data by language
    lang_data = {}
    for (lang, side, tot), is_disordered in disorder_data.items():
        if lang not in lang_data:
            lang_data[lang] = {
                'language_code': lang,
                'language_name': langNames.get(lang, lang),
                'group': langnameGroup.get(langNames.get(lang, lang), 'Unknown')
            }
        col_name = f'{side}_tot_{tot}_disordered'
        lang_data[lang][col_name] = is_disordered
    
    # Convert to DataFrame
    df = pd.DataFrame(list(lang_data.values()))
    
    # Add total disorder count
    disorder_cols = [col for col in df.columns if col.endswith('_disordered')]
    df['total_disordered'] = df[disorder_cols].sum(axis=1)
    
    return df


def compute_disorder_statistics(all_langs_average_sizes, langNames, langnameGroup):
    """
    Complete disorder analysis pipeline.
    
    Parameters
    ----------
    all_langs_average_sizes : dict
        Dictionary: lang -> position_key -> average_size
    langNames : dict
        Language code to name mapping
    langnameGroup : dict
        Language name to group mapping
        
    Returns
    -------
    disorder_df : pd.DataFrame
        Per-language disorder information
    disorder_percentages : dict
        Per-configuration disorder percentages
    """
    disorder_data = compute_disorder_per_language(all_langs_average_sizes)
    disorder_percentages = compute_disorder_percentages(disorder_data)
    disorder_df = create_disorder_dataframe(disorder_data, langNames, langnameGroup)
    
    return disorder_df, disorder_percentages

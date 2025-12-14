"""
Module for computing disorder percentages in dependency size sequences.

For each configuration (e.g., R tot=4 with positions 1,2,3,4), we check whether
the sizes are strictly monotonically increasing. If not, the sequence is "disordered".
"""

import pandas as pd
import numpy as np


def compute_disorder_per_language(all_langs_average_sizes, ordering_stats=None):
    """
    For each language and each configuration, compute whether the sequence is ordered.
    
    Parameters
    ----------
    all_langs_average_sizes : dict
        Dictionary: lang -> position_key -> average_size
    ordering_stats : dict, optional
        Dictionary: lang -> (side, tot, idx) -> {'lt': count, 'eq': count, 'gt': count}
        
    Returns
    -------
    disorder_data : dict
        Dictionary: (lang, side, tot) -> disorder_score (float 0.0-1.0) or is_disordered (bool)
        If ordering_stats is provided, returns a float score (0.0=ordered, 1.0=fully disordered).
        If not, returns boolean (True=disordered, False=ordered).
    """
    disorder_data = {}
    
    # Method 1: Use granular ordering stats if available
    if ordering_stats:
        for lang, stats in ordering_stats.items():
            # Organize by configuration
            config_counts = {} # (side, tot) -> {'disordered': 0, 'total': 0}
            
            for key, counts in stats.items():
                # Skip raw total counts (integers)
                if isinstance(counts, int):
                    continue

                # key is (side, tot, pair_idx)
                if len(key) != 3: continue
                side, tot, idx = key
                
                if (side, tot) not in config_counts:
                    config_counts[(side, tot)] = {'disordered': 0, 'total': 0}
                
                total = counts['lt'] + counts['eq'] + counts['gt']
                if total == 0: continue
                
                # Right side: Ordered if lt. Disordered if eq or gt.
                if side == 'right':
                    disordered = counts['eq'] + counts['gt']
                # Left side: Ordered if gt (decreasing towards verb). Disordered if eq or lt.
                else:
                    disordered = counts['lt'] + counts['eq']
                
                config_counts[(side, tot)]['disordered'] += disordered
                config_counts[(side, tot)]['total'] += total
            
            # Calculate final score per configuration
            for (side, tot), sums in config_counts.items():
                if sums['total'] > 0:
                    disorder_data[(lang, side, tot)] = sums['disordered'] / sums['total']
                else:
                    disorder_data[(lang, side, tot)] = None
                    
        # Return here if we used this method
        # Note: We might want to fill in gaps from averages if missing? 
        # But generally if we have stats we use them.
        if disorder_data:
            return disorder_data

    # Method 2: Fallback to average sizes (Binary check)
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
    config_vals = {}
    for (lang, side, tot), val in disorder_data.items():
        if val is None: continue
        
        key = (side, tot)
        if key not in config_vals:
            config_vals[key] = []
        config_vals[key].append(val)
    
    # Compute percentage for each configuration
    for (side, tot), vals in config_vals.items():
        if len(vals) > 0:
            # If vals are booleans (from Method 2), sum gives count of True.
            # If vals are floats (from Method 1), sum gives total disorder mass.
            # In both cases, mean * 100 gives the percentage.
            pct = 100.0 * np.mean(vals)
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
    
    # Add total disorder count/score
    # If using floats: sum of scores. If bools: sum of True.
    disorder_cols = [col for col in df.columns if col.endswith('_disordered')]
    
    # We want a normalized total score (0-1) or at least comparable?
    # Original logic just summed them up (0-8 max).
    # If we have probabilities 0.0-1.0, the sum will be 0.0-8.0.
    # This preserves the magnitude relation.
    df['total_disordered'] = df[disorder_cols].sum(axis=1)
    
    return df


def compute_disorder_statistics(all_langs_average_sizes, langNames, langnameGroup, ordering_stats=None):
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
    ordering_stats : dict, optional
        Granular ordering statistics.
        
    Returns
    -------
    disorder_df : pd.DataFrame
        Per-language disorder information
    disorder_percentages : dict
        Per-configuration disorder percentages
    """
    disorder_data = compute_disorder_per_language(all_langs_average_sizes, ordering_stats)
    disorder_percentages = compute_disorder_percentages(disorder_data)
    disorder_df = create_disorder_dataframe(disorder_data, langNames, langnameGroup)
    
    return disorder_df, disorder_percentages

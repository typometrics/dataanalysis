"""
Analysis functions for computing statistics and derived metrics.
"""

import re
import pickle
import os
import numpy as np


def filter_by_min_count(all_langs_position2num, all_langs_position2sizes, min_count=10):
    """
    Filter position statistics to keep only positions with sufficient occurrences.
    
    Parameters
    ----------
    all_langs_position2num : dict
        Dictionary mapping languages to position occurrence counts
    all_langs_position2sizes : dict
        Dictionary mapping languages to position total sizes
    min_count : int
        Minimum number of occurrences required to keep a position
        
    Returns
    -------
    tuple
        (filtered_position2num, filtered_position2sizes)
    """
    filtered_position2num = {}
    filtered_position2sizes = {}
    
    for lang in all_langs_position2num:
        filtered_position2num[lang] = {}
        filtered_position2sizes[lang] = {}
        
        for ty in all_langs_position2num[lang]:
            if all_langs_position2num[lang][ty] >= min_count:
                filtered_position2num[lang][ty] = all_langs_position2num[lang][ty]
                filtered_position2sizes[lang][ty] = all_langs_position2sizes[lang][ty]
    
    print(f"Filtered to positions with at least {min_count} occurrences")
    return filtered_position2num, filtered_position2sizes


def compute_MAL_per_language(all_langs_position2sizes, all_langs_position2num):
    """
    Compute Mean Aggregate Length (MAL) for right dependents per language.
    
    For each language and each value of n (number of right dependents),
    computes the average total size of all n right dependents combined.
    
    Parameters
    ----------
    all_langs_position2sizes : dict
        Dictionary mapping languages to position total sizes
    all_langs_position2num : dict
        Dictionary mapping languages to position occurrence counts
        
    Returns
    -------
    dict
        Dictionary mapping language codes to {n: MAL_n} dictionaries
        
    Notes
    -----
    MAL_n is computed as:
        sum of all sizes for right_1 through right_n (with totright_n context)
        divided by
        sum of all counts for right_1 through right_n (with totright_n context)
    """
    lang2MAL = {}
    
    for lang in all_langs_position2sizes:
        MAL_n = {}
        
        # Collect all right dependent keys with totright context
        right_keys = [
            k for k in all_langs_position2sizes[lang] 
            if k.startswith('right_') and '_totright_' in k
        ]
        
        # Extract unique values of n (total number of right dependents)
        n_values = set(
            int(re.search(r'_totright_(\d+)', k).group(1)) 
            for k in right_keys
        )
        
        for n in n_values:
            total_size = 0
            total_count = 0
            
            # Sum across all positions for this n
            for i in range(1, n + 1):
                key = f'right_{i}_totright_{n}'
                total_size += all_langs_position2sizes[lang].get(key, 0)
                total_count += all_langs_position2num[lang].get(key, 0)
            
            if total_count > 0:
                MAL_n[n] = np.exp(total_size / total_count)
        
        lang2MAL[lang] = MAL_n
    
    return lang2MAL


def compute_average_sizes(all_langs_position2sizes, all_langs_position2num):
    """
    Compute average sizes from total sizes and counts.
    
    Parameters
    ----------
    all_langs_position2sizes : dict
        Dictionary mapping languages to position total sizes
    all_langs_position2num : dict
        Dictionary mapping languages to position occurrence counts
        
    Returns
    -------
    dict
        Dictionary mapping languages to {position: average_size}
    """
    all_langs_average_sizes = {}
    
    for lang in all_langs_position2sizes:
        all_langs_average_sizes[lang] = {
            ty: np.exp(all_langs_position2sizes[lang][ty] / all_langs_position2num[lang][ty])
            for ty in all_langs_position2sizes[lang]
        }
    
    return all_langs_average_sizes


def save_analysis_results(all_langs_position2num, all_langs_position2sizes, 
                          all_langs_average_sizes, filtered_position2num, 
                          filtered_position2sizes, lang2MAL, output_dir='data'):
    """
    Save all analysis results to pickle files.
    
    Parameters
    ----------
    all_langs_position2num : dict
        Unfiltered position occurrence counts
    all_langs_position2sizes : dict
        Unfiltered position total sizes
    all_langs_average_sizes : dict
        Unfiltered average sizes
    filtered_position2num : dict
        Filtered position occurrence counts
    filtered_position2sizes : dict
        Filtered position total sizes
    lang2MAL : dict
        Mean Aggregate Length per language
    output_dir : str
        Output directory
    """
    os.makedirs(output_dir, exist_ok=True)
    
    files = {
        'all_langs_position2num.pkl': all_langs_position2num,
        'all_langs_position2sizes.pkl': all_langs_position2sizes,
        'all_langs_average_sizes.pkl': all_langs_average_sizes,
        'filtered_position2num.pkl': filtered_position2num,
        'filtered_position2sizes.pkl': filtered_position2sizes,
        'lang2MAL.pkl': lang2MAL
    }
    
    for filename, data in files.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        print(f"Saved {filename}")
    
    print(f"All analysis results saved to {output_dir}/")


def load_analysis_results(output_dir='data'):
    """
    Load all analysis results from pickle files.
    
    Parameters
    ----------
    output_dir : str
        Input directory
        
    Returns
    -------
    dict
        Dictionary containing all loaded data
    """
    files = [
        'all_langs_position2num.pkl',
        'all_langs_position2sizes.pkl',
        'all_langs_average_sizes.pkl',
        'filtered_position2num.pkl',
        'filtered_position2sizes.pkl',
        'lang2MAL.pkl'
    ]
    
    results = {}
    for filename in files:
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'rb') as f:
            key = filename.replace('.pkl', '')
            results[key] = pickle.load(f)
        print(f"Loaded {filename}")
    
    print(f"All analysis results loaded from {output_dir}/")
    return results

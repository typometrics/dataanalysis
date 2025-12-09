
import pandas as pd

def compute_hcs_factors(all_langs_average_sizes_filtered, langNames, langnameGroup):
    """
    Compute HCS factor: right_2_totright_2 / right_1_totright_2
    Returns a DataFrame with the computed factors.
    """
    hcs_data = []

    for lang in all_langs_average_sizes_filtered:
        lang_name = langNames.get(lang, lang)
        group = langnameGroup.get(lang_name, 'Unknown')
        
        # Get the two positions
        pos1_key = 'right_1_totright_2'  # position 1, total 2
        pos2_key = 'right_2_totright_2'  # position 2, total 2
        
        if pos1_key in all_langs_average_sizes_filtered[lang] and pos2_key in all_langs_average_sizes_filtered[lang]:
            pos1_val = all_langs_average_sizes_filtered[lang][pos1_key]
            pos2_val = all_langs_average_sizes_filtered[lang][pos2_key]
            
            # Compute factor (avoid division by zero)
            if pos1_val > 0:
                hcs_factor = pos2_val / pos1_val
                hcs_data.append({
                    'language_code': lang,
                    'language_name': lang_name,
                    'group': group,
                    'right_1_totright_2': pos1_val,
                    'right_2_totright_2': pos2_val,
                    'hcs_factor': hcs_factor
                })

    # Create DataFrame
    hcs_df = pd.DataFrame(hcs_data)
    if not hcs_df.empty:
        hcs_df = hcs_df.sort_values('hcs_factor')
    
    return hcs_df

def compute_dep_length_ratios(all_langs_average_sizes_filtered, langNames, langnameGroup):
    """
    Compute ratios of dependency lengths (e.g., pos 2 / pos 1) for various totals.
    This logic was implicitly part of the scatter plot analysis.
    """
    # This might be needed if we want to generalize the HCS factor computation
    # for now, HCS is the main one explicitly computed in the notebook.
    pass

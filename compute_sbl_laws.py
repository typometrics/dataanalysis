import os
import glob
import re
import numpy as np
import pandas as pd
from scipy.stats import linregress, binomtest

def parse_helix_tsv(filepath):
    data = {'R': {}, 'L': {}}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip('\n').split('\t')
                if not parts: continue
                
                row_name = parts[0].strip()
                if row_name.startswith('R tot=') or row_name.startswith('L tot='):
                    side = 'R' if row_name.startswith('R') else 'L'
                    n = int(row_name.split('=')[1])
                    data[side][n] = {'sizes': {}, 'stats': {}}
                    
                    n_match = re.search(r'N=(\d+)', parts[-1])
                    data[side][n]['N'] = int(n_match.group(1)) if n_match else 0
                    
                    for k in range(1, n+1):
                        idx = 10 + 2 * (k - 1) if side == 'R' else 8 - 2 * (k - 1)
                        if 0 <= idx < len(parts) and parts[idx].strip():
                            try:
                                data[side][n]['sizes'][k] = float(parts[idx].strip())
                            except ValueError:
                                pass
                        
                        stat_idx = idx + 1 if side == 'R' else idx - 1
                        if 0 <= stat_idx < len(parts) and parts[stat_idx].strip():
                            stat_match = re.search(r'<\s*([\d.]+)\s*=\s*([\d.]+)\s*>\s*([\d.]+)', parts[stat_idx])
                            if stat_match:
                                lt = float(stat_match.group(1))
                                eq = float(stat_match.group(2))
                                gt = float(stat_match.group(3))
                                data[side][n]['stats'][k] = (lt, eq, gt)
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None
    return data

def geometric_mean(ratios):
    ratios = [r for r in ratios if r > 0]
    if not ratios: return np.nan
    return np.exp(np.mean(np.log(ratios)))


from scipy.stats import ttest_ind_from_stats

def get_mean_std(n, sum_x, sum_sq_x):
    if n <= 1: return np.nan, np.nan
    mean = sum_x / n
    var = (sum_sq_x - (sum_x**2) / n) / (n - 1)
    if var < 0: var = 0
    return mean, np.sqrt(var)

def get_ttest_pval(k1, k2, p2n, p2ls, p2lsq):
    if not p2n or not p2ls or not p2lsq: return np.nan
    n1 = p2n.get(k1, 0)
    n2 = p2n.get(k2, 0)
    if n1 <= 1 or n2 <= 1: return np.nan
    
    m1, s1 = get_mean_std(n1, p2ls.get(k1, 0), p2lsq.get(k1, 0))
    m2, s2 = get_mean_std(n2, p2ls.get(k2, 0), p2lsq.get(k2, 0))
    
    if np.isnan(s1) or np.isnan(s2) or (s1 == 0 and s2 == 0): return np.nan
    
    res = ttest_ind_from_stats(m1, s1, n1, m2, s2, n2, equal_var=False)
    return res.pvalue

def linregress_simple(x, y):
    # We use scipy.stats.linregress instead of this custom function
    # but we can leave this here for backward compatibility if needed
    return linregress(x, y).slope

def compute_metrics(data, side='R', table_type='Standard', p2n=None, p2ls=None, p2lsq=None):
    d = data[side]
    
    # 1. Horizontal
    horiz_pairs = []
    horiz_ratios = []
    horiz_cmp = {'<': 0, '=': 0, '>': 0}
    horiz_pvals = []
    
    for n in range(2, 5):
        for k in range(1, n):
            if n in d and k in d[n]['sizes'] and (k+1) in d[n]['sizes']:
                v1, v2 = d[n]['sizes'][k], d[n]['sizes'][k+1]
                horiz_ratios.append(v2 / v1)
                if v1 < v2: horiz_cmp['<'] += 1
                elif abs(v1 - v2) < 1e-6: horiz_cmp['='] += 1
                else: horiz_cmp['>'] += 1
                
                # Compute Binomial test p-value using the TSV stats
                if k in d[n]['stats'] and d[n]['N'] > 0:
                    lt_pct, eq_pct, gt_pct = d[n]['stats'][k]
                    total_N = d[n]['N']
                    # We are testing Short-Before-Long (lt) vs Long-Before-Short (gt)
                    # For Left side, k is counted from the verb, so k=1 is closest to verb, k=2 is further.
                    # R_n^k < R_n^{k+1} means inner is shorter than outer. This corresponds to 'lt'.
                    trials = int(round(total_N * (lt_pct + gt_pct) / 100.0))
                    successes = int(round(total_N * lt_pct / 100.0))
                    if trials > 0:
                        res = binomtest(successes, trials, p=0.5, alternative='two-sided')
                        horiz_pvals.append(res.pvalue)
                    else:
                        horiz_pvals.append(np.nan)
                else:
                    horiz_pvals.append(np.nan)
                
    horiz_score = horiz_cmp['<']
    horiz_valid = len(horiz_ratios)
    
    # Outer ratio mean
    outer_ratios = []
    for n in range(2, 5):
        if n in d and n in d[n]['sizes'] and (n-1) in d[n]['sizes']:
            outer_ratios.append(d[n]['sizes'][n] / d[n]['sizes'][n-1])
            
    # 2. Vertical (R_{n+1}^k < R_n^k)
    vert_ratios = []
    vert_pvals = []
    vert_score = 0
    side_full = 'right' if side == 'R' else 'left'
    for k in range(1, 4):
        for n in range(k, 4):
            if (n+1) in d and k in d[n+1]['sizes'] and n in d and k in d[n]['sizes']:
                v_lower = d[n+1]['sizes'][k] # R_{n+1}^k
                v_upper = d[n]['sizes'][k]   # R_n^k
                vert_ratios.append(v_upper / v_lower)
                if v_lower < v_upper: vert_score += 1
                
                # P-value for Vertical Law
                if table_type == 'Standard':
                    k1 = f'{side_full}_{k}_tot{side_full}_{n+1}'
                    k2 = f'{side_full}_{k}_tot{side_full}_{n}'
                else:
                    k1 = f'{side_full}_{k}_anyother_tot{side_full}_{n+1}'
                    k2 = f'{side_full}_{k}_anyother_tot{side_full}_{n}'
                
                # R_{n+1}^k vs R_n^k
                pval = get_ttest_pval(k1, k2, p2n, p2ls, p2lsq)
                vert_pvals.append(pval)
    vert_valid = len(vert_ratios)

    # 3. Diagonal (R_n^k < R_{n+1}^{k+1})
    diag_ratios = []
    diag_pvals = []
    diag_score = 0
    for n in range(1, 4):
        for k in range(1, n+1):
            if n in d and k in d[n]['sizes'] and (n+1) in d and (k+1) in d[n+1]['sizes']:
                v1, v2 = d[n]['sizes'][k], d[n+1]['sizes'][k+1]
                diag_ratios.append(v2 / v1)
                if v1 < v2: diag_score += 1
                
                # P-value for Diagonal Law
                if table_type == 'Standard':
                    k1 = f'{side_full}_{k}_tot{side_full}_{n}'
                    k2 = f'{side_full}_{k+1}_tot{side_full}_{n+1}'
                else:
                    k1 = f'{side_full}_{k}_anyother_tot{side_full}_{n}'
                    k2 = f'{side_full}_{k+1}_anyother_tot{side_full}_{n+1}'
                    
                pval = get_ttest_pval(k1, k2, p2n, p2ls, p2lsq)
                diag_pvals.append(pval)
    diag_valid = len(diag_ratios)

    # Complex Beta
    pts_x, pts_y = [], []
    for n in range(1, 5):
        for k in range(1, n+1):
            if n in d and k in d[n]['sizes']:
                if side == 'R':
                    pts_x.append(-np.log(n + 1 - k))
                else:
                    pts_x.append(np.log(n + 1 - k))
                pts_y.append(np.log(d[n]['sizes'][k]))
                
    if len(pts_x) >= 2:
        res = linregress(pts_x, pts_y)
        slope = res.slope
        p_value = res.pvalue
    else:
        slope = np.nan
        p_value = np.nan
        
    return {
        f'{side}_Horiz_Score': horiz_score if horiz_valid == 6 else np.nan,
        f'{side}_Horiz_Valid': horiz_valid,
        f'{side}_Horiz_GM': geometric_mean(horiz_ratios),
        f'{side}_Horiz_Min': min(horiz_ratios) if horiz_ratios else np.nan,
        f'{side}_Horiz_Max': max(horiz_ratios) if horiz_ratios else np.nan,
        f'{side}_Horiz_Pct_Lt': horiz_cmp['<'] / horiz_valid * 100 if horiz_valid > 0 else np.nan,
        f'{side}_Horiz_Outer_GM': geometric_mean(outer_ratios),
        f'{side}_Horiz_Pvals': '|'.join(f"{p:.4e}" if pd.notna(p) else "" for p in horiz_pvals),
        
        f'{side}_Vert_Score': vert_score if vert_valid == 6 else np.nan,
        f'{side}_Vert_Valid': vert_valid,
        f'{side}_Vert_GM': geometric_mean(vert_ratios),
        f'{side}_Vert_Min': min(vert_ratios) if vert_ratios else np.nan,
        f'{side}_Vert_Max': max(vert_ratios) if vert_ratios else np.nan,
        f'{side}_Vert_Pvals': '|'.join(f"{p:.4e}" if pd.notna(p) else "" for p in vert_pvals),
        
        f'{side}_Diag_Score': diag_score if diag_valid == 6 else np.nan,
        f'{side}_Diag_Valid': diag_valid,
        f'{side}_Diag_GM': geometric_mean(diag_ratios),
        f'{side}_Diag_Min': min(diag_ratios) if diag_ratios else np.nan,
        f'{side}_Diag_Max': max(diag_ratios) if diag_ratios else np.nan,
        f'{side}_Diag_Pvals': '|'.join(f"{p:.4e}" if pd.notna(p) else "" for p in diag_pvals),
        
        f'{side}_Complex_Beta': slope,
        f'{side}_Complex_Pval': p_value
    }

import pickle
def process_all_languages(input_dir, output_csv):
    results = []
    
    # Load raw sums for Welch's t-test
    base = os.path.dirname(input_dir)
    try:
        with open(os.path.join(base, 'all_langs_position2num.pkl'), 'rb') as f:
            all_langs_position2num = pickle.load(f)
        with open(os.path.join(base, 'all_langs_position2logsizes.pkl'), 'rb') as f:
            all_langs_position2logsizes = pickle.load(f)
        with open(os.path.join(base, 'all_langs_position2logsqsizes.pkl'), 'rb') as f:
            all_langs_position2logsqsizes = pickle.load(f)
    except Exception as e:
        print(f"Error loading pkl files: {e}")
        all_langs_position2num = {}
        all_langs_position2logsizes = {}
        all_langs_position2logsqsizes = {}
    
    # We expect subdirectories like input_dir/Language_code/
    for lang_dir in sorted(glob.glob(os.path.join(input_dir, '*_*'))):
        if not os.path.isdir(lang_dir): continue
        
        lang_name_code = os.path.basename(lang_dir)
        # Process Standard table
        std_tsv = os.path.join(lang_dir, f'Helix_{lang_name_code}.tsv')
        if os.path.exists(std_tsv):
            data = parse_helix_tsv(std_tsv)
            if data:
                metrics = {'Language': lang_name_code, 'Table_Type': 'Standard'}
                lang = lang_name_code.split('_')[-1]
                
                # Check if this is a GLOBAL or FAMILY table
                if lang_name_code == 'GLOBAL_average':
                    p2n = {k: sum(d.get(k, 0) for d in all_langs_position2num.values()) for k in set().union(*(d.keys() for d in all_langs_position2num.values()))}
                    p2ls = {k: sum(d.get(k, 0) for d in all_langs_position2logsizes.values()) for k in set().union(*(d.keys() for d in all_langs_position2logsizes.values()))}
                    p2lsq = {k: sum(d.get(k, 0) for d in all_langs_position2logsqsizes.values()) for k in set().union(*(d.keys() for d in all_langs_position2logsqsizes.values()))}
                elif lang_name_code.startswith('FAMILY_'):
                    # To do this accurately for families, we would need metadata mapping, but for now we'll skip or use empty dicts
                    # Actually, we can get family languages from the DataFrame later if needed. For now, empty.
                    p2n, p2ls, p2lsq = {}, {}, {}
                else:
                    # Individual language treebank
                    # Match exact keys that start with lang_code or end with it?
                    # The keys in the pkl are treebank codes (e.g. 'af_afribooms')
                    # Actually we don't know the exact treebank code from lang_name_code if it's 'Afrikaans_af' and treebank was 'af_afribooms'
                    # But if we search all_langs_position2num keys for anything starting with 'af_'?
                    # Usually 'lang' here is just the lang code like 'af', wait no, verb_centered uses treebank code!
                    # Actually, if we pass the whole dicts and look up, we need the right key.
                    # Let's find the matching key(s)
                    matching_keys = [k for k in all_langs_position2num.keys() if k == lang or k.split('_')[0] == lang]
                    p2n = {k: sum(all_langs_position2num[mk].get(k, 0) for mk in matching_keys) for k in set().union(*(all_langs_position2num[mk].keys() for mk in matching_keys))}
                    p2ls = {k: sum(all_langs_position2logsizes[mk].get(k, 0) for mk in matching_keys) for k in set().union(*(all_langs_position2logsizes[mk].keys() for mk in matching_keys))}
                    p2lsq = {k: sum(all_langs_position2logsqsizes[mk].get(k, 0) for mk in matching_keys) for k in set().union(*(all_langs_position2logsqsizes[mk].keys() for mk in matching_keys))}

                metrics.update(compute_metrics(data, 'R', 'Standard', p2n, p2ls, p2lsq))
                metrics.update(compute_metrics(data, 'L', 'Standard', p2n, p2ls, p2lsq))
                results.append(metrics)
                
        # Process AnyOtherSide table
        any_tsv = os.path.join(lang_dir, f'Helix_{lang_name_code}_AnyOtherSide.tsv')
        if os.path.exists(any_tsv):
            data = parse_helix_tsv(any_tsv)
            if data:
                metrics = {'Language': lang_name_code, 'Table_Type': 'AnyOtherSide'}
                lang = lang_name_code.split('_')[-1]
                
                # Check if this is a GLOBAL or FAMILY table
                if lang_name_code == 'GLOBAL_average':
                    p2n = {k: sum(d.get(k, 0) for d in all_langs_position2num.values()) for k in set().union(*(d.keys() for d in all_langs_position2num.values()))}
                    p2ls = {k: sum(d.get(k, 0) for d in all_langs_position2logsizes.values()) for k in set().union(*(d.keys() for d in all_langs_position2logsizes.values()))}
                    p2lsq = {k: sum(d.get(k, 0) for d in all_langs_position2logsqsizes.values()) for k in set().union(*(d.keys() for d in all_langs_position2logsqsizes.values()))}
                elif lang_name_code.startswith('FAMILY_'):
                    p2n, p2ls, p2lsq = {}, {}, {}
                else:
                    matching_keys = [k for k in all_langs_position2num.keys() if k == lang or k.split('_')[0] == lang]
                    p2n = {k: sum(all_langs_position2num[mk].get(k, 0) for mk in matching_keys) for k in set().union(*(all_langs_position2num[mk].keys() for mk in matching_keys))}
                    p2ls = {k: sum(all_langs_position2logsizes[mk].get(k, 0) for mk in matching_keys) for k in set().union(*(all_langs_position2logsizes[mk].keys() for mk in matching_keys))}
                    p2lsq = {k: sum(all_langs_position2logsqsizes[mk].get(k, 0) for mk in matching_keys) for k in set().union(*(all_langs_position2logsqsizes[mk].keys() for mk in matching_keys))}

                metrics.update(compute_metrics(data, 'R', 'AnyOtherSide', p2n, p2ls, p2lsq))
                metrics.update(compute_metrics(data, 'L', 'AnyOtherSide', p2n, p2ls, p2lsq))
                results.append(metrics)
                
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    print(f"Processed {len(results)} tables. Output saved to {output_csv}")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data', 'helix_tables')
    output_file = os.path.join(base_dir, 'data', 'sbl_laws_summary.csv')
    process_all_languages(data_dir, output_file)

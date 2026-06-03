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

def linregress_simple(x, y):
    # We use scipy.stats.linregress instead of this custom function
    # but we can leave this here for backward compatibility if needed
    return linregress(x, y).slope

def compute_metrics(data, side='R'):
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
    vert_score = 0
    for k in range(1, 4):
        for n in range(k, 4):
            if (n+1) in d and k in d[n+1]['sizes'] and n in d and k in d[n]['sizes']:
                v_lower = d[n+1]['sizes'][k] # R_{n+1}^k
                v_upper = d[n]['sizes'][k]   # R_n^k
                vert_ratios.append(v_upper / v_lower)
                if v_lower < v_upper: vert_score += 1
    vert_valid = len(vert_ratios)

    # 3. Diagonal (R_n^k < R_{n+1}^{k+1})
    diag_ratios = []
    diag_score = 0
    for n in range(1, 4):
        for k in range(1, n+1):
            if n in d and k in d[n]['sizes'] and (n+1) in d and (k+1) in d[n+1]['sizes']:
                v1, v2 = d[n]['sizes'][k], d[n+1]['sizes'][k+1]
                diag_ratios.append(v2 / v1)
                if v1 < v2: diag_score += 1
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
        
        f'{side}_Diag_Score': diag_score if diag_valid == 6 else np.nan,
        f'{side}_Diag_Valid': diag_valid,
        f'{side}_Diag_GM': geometric_mean(diag_ratios),
        f'{side}_Diag_Min': min(diag_ratios) if diag_ratios else np.nan,
        f'{side}_Diag_Max': max(diag_ratios) if diag_ratios else np.nan,
        
        f'{side}_Complex_Beta': slope,
        f'{side}_Complex_Pval': p_value
    }

def process_all_languages(input_dir, output_csv):
    results = []
    
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
                metrics.update(compute_metrics(data, 'R'))
                metrics.update(compute_metrics(data, 'L'))
                results.append(metrics)
                
        # Process AnyOtherSide table
        any_tsv = os.path.join(lang_dir, f'Helix_{lang_name_code}_AnyOtherSide.tsv')
        if os.path.exists(any_tsv):
            data = parse_helix_tsv(any_tsv)
            if data:
                metrics = {'Language': lang_name_code, 'Table_Type': 'AnyOtherSide'}
                metrics.update(compute_metrics(data, 'R'))
                metrics.update(compute_metrics(data, 'L'))
                results.append(metrics)
                
    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    print(f"Processed {len(results)} tables. Output saved to {output_csv}")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data', 'helix_tables')
    output_file = os.path.join(base_dir, 'data', 'sbl_laws_summary.csv')
    process_all_languages(data_dir, output_file)

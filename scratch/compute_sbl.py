import os
import glob
import numpy as np
import pandas as pd

def parse_helix_tsv(filepath):
    data = {'R': {}, 'L': {}}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip('\n').split('\t')
            if not parts: continue
            
            row_name = parts[0].strip()
            if row_name.startswith('R tot='):
                n = int(row_name.split('=')[1])
                data['R'][n] = {}
                for k in range(1, n+1):
                    idx = 10 + 2 * (k - 1)
                    if idx < len(parts) and parts[idx].strip():
                        try:
                            data['R'][n][k] = float(parts[idx].strip())
                        except ValueError:
                            pass
            elif row_name.startswith('L tot='):
                n = int(row_name.split('=')[1])
                data['L'][n] = {}
                for k in range(1, n+1):
                    idx = 8 - 2 * (k - 1)
                    if idx >= 0 and idx < len(parts) and parts[idx].strip():
                        try:
                            data['L'][n][k] = float(parts[idx].strip())
                        except ValueError:
                            pass
    return data

def geometric_mean(ratios):
    ratios = [r for r in ratios if r > 0]
    if not ratios: return np.nan
    return np.exp(np.mean(np.log(ratios)))

def linregress_simple(x, y):
    x = np.array(x)
    y = np.array(y)
    n = len(x)
    if n < 2: return np.nan
    sum_x = np.sum(x)
    sum_y = np.sum(y)
    sum_xy = np.sum(x * y)
    sum_xx = np.sum(x * x)
    
    denominator = n * sum_xx - sum_x ** 2
    if denominator == 0:
        return np.nan
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    return slope

def compute_metrics(data, side='R'):
    d = data[side]
    
    # 1. Horizontal
    horiz_pairs = []
    horiz_ratios = []
    horiz_cmp = {'<': 0, '=': 0, '>': 0}
    
    for n in range(2, 5):
        for k in range(1, n):
            if n in d and k in d[n] and (k+1) in d[n]:
                v1, v2 = d[n][k], d[n][k+1]
                horiz_ratios.append(v2 / v1)
                if v1 < v2: horiz_cmp['<'] += 1
                elif abs(v1 - v2) < 1e-6: horiz_cmp['='] += 1
                else: horiz_cmp['>'] += 1
                
    horiz_score = horiz_cmp['<']
    horiz_valid = len(horiz_ratios)
    
    # Outer ratio mean
    outer_ratios = []
    for n in range(2, 5):
        if n in d and n in d[n] and (n-1) in d[n]:
            outer_ratios.append(d[n][n] / d[n][n-1])
            
    # 2. Vertical (R_{n+1}^k < R_n^k)
    vert_ratios = []
    vert_score = 0
    for k in range(1, 4):
        for n in range(k, 4):
            # compare n+1 vs n
            if (n+1) in d and k in d[n+1] and n in d and k in d[n]:
                v_lower = d[n+1][k] # R_{n+1}^k
                v_upper = d[n][k]   # R_n^k
                vert_ratios.append(v_upper / v_lower)
                if v_lower < v_upper: vert_score += 1
    vert_valid = len(vert_ratios)

    # 3. Diagonal (R_n^k < R_{n+1}^{k+1})
    diag_ratios = []
    diag_score = 0
    for n in range(1, 4):
        for k in range(1, n+1):
            if n in d and k in d[n] and (n+1) in d and (k+1) in d[n+1]:
                v1, v2 = d[n][k], d[n+1][k+1]
                diag_ratios.append(v2 / v1)
                if v1 < v2: diag_score += 1
    diag_valid = len(diag_ratios)

    # Complex Beta
    pts_x, pts_y = [], []
    for n in range(1, 5):
        for k in range(1, n+1):
            if n in d and k in d[n]:
                if side == 'R':
                    pts_x.append(-np.log(n + 1 - k))
                else:
                    pts_x.append(np.log(n + 1 - k))
                pts_y.append(np.log(d[n][k]))
                
    slope = linregress_simple(pts_x, pts_y)
        
    return {
        f'{side}_Horiz_Score': horiz_score if horiz_valid == 6 else np.nan,
        f'{side}_Horiz_Valid': horiz_valid,
        f'{side}_Horiz_GM': geometric_mean(horiz_ratios),
        f'{side}_Horiz_Min': min(horiz_ratios) if horiz_ratios else np.nan,
        f'{side}_Horiz_Max': max(horiz_ratios) if horiz_ratios else np.nan,
        f'{side}_Horiz_Pct_Lt': horiz_cmp['<'] / horiz_valid * 100 if horiz_valid else np.nan,
        f'{side}_Horiz_Outer_GM': geometric_mean(outer_ratios),
        
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
        
        f'{side}_Complex_Beta': slope
    }

d = parse_helix_tsv('data/helix_tables/French_fr/Helix_French_fr.tsv')
res = compute_metrics(d, 'R')
import pprint
pprint.pprint(res)

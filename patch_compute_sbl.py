import re

with open('compute_sbl_laws.py', 'r') as f:
    content = f.read()

# Replace compute_metrics signature
content = content.replace("def compute_metrics(data, side='R'):", "def compute_metrics(data, side='R', table_type='Standard', p2n=None, p2ls=None, p2lsq=None):")

# Add get_ttest_pval helper
helper = """
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
"""
content = content.replace("def linregress_simple", helper + "\ndef linregress_simple")

# Add Vertical P-values
vert_code_search = """    vert_ratios = []
    vert_score = 0
    for k in range(1, 4):
        for n in range(k, 4):
            if (n+1) in d and k in d[n+1]['sizes'] and n in d and k in d[n]['sizes']:
                v_lower = d[n+1]['sizes'][k] # R_{n+1}^k
                v_upper = d[n]['sizes'][k]   # R_n^k
                vert_ratios.append(v_upper / v_lower)
                if v_lower < v_upper: vert_score += 1
    vert_valid = len(vert_ratios)"""

vert_code_replace = """    vert_ratios = []
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
    vert_valid = len(vert_ratios)"""
content = content.replace(vert_code_search, vert_code_replace)

# Add Diagonal P-values
diag_code_search = """    diag_ratios = []
    diag_score = 0
    for n in range(1, 4):
        for k in range(1, n+1):
            if n in d and k in d[n]['sizes'] and (n+1) in d and (k+1) in d[n+1]['sizes']:
                v1, v2 = d[n]['sizes'][k], d[n+1]['sizes'][k+1]
                diag_ratios.append(v2 / v1)
                if v1 < v2: diag_score += 1
    diag_valid = len(diag_ratios)"""

diag_code_replace = """    diag_ratios = []
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
    diag_valid = len(diag_ratios)"""
content = content.replace(diag_code_search, diag_code_replace)

# Output dict updates
out_search = """        f'{side}_Vert_Max': max(vert_ratios) if vert_ratios else np.nan,"""
out_replace = """        f'{side}_Vert_Max': max(vert_ratios) if vert_ratios else np.nan,
        f'{side}_Vert_Pvals': '|'.join(f"{p:.4e}" if pd.notna(p) else "" for p in vert_pvals),"""
content = content.replace(out_search, out_replace)

out_search2 = """        f'{side}_Diag_Max': max(diag_ratios) if diag_ratios else np.nan,"""
out_replace2 = """        f'{side}_Diag_Max': max(diag_ratios) if diag_ratios else np.nan,
        f'{side}_Diag_Pvals': '|'.join(f"{p:.4e}" if pd.notna(p) else "" for p in diag_pvals),"""
content = content.replace(out_search2, out_replace2)


# Update process_all_languages
proc_search = """def process_all_languages(input_dir, output_csv):
    results = []"""
proc_replace = """import pickle
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
        all_langs_position2logsqsizes = {}"""
content = content.replace(proc_search, proc_replace)


loop_search = """                metrics = {'Language': lang_name_code, 'Table_Type': 'Standard'}
                metrics.update(compute_metrics(data, 'R'))
                metrics.update(compute_metrics(data, 'L'))"""

loop_replace = """                metrics = {'Language': lang_name_code, 'Table_Type': 'Standard'}
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
                metrics.update(compute_metrics(data, 'L', 'Standard', p2n, p2ls, p2lsq))"""
content = content.replace(loop_search, loop_replace)


loop_search2 = """                metrics = {'Language': lang_name_code, 'Table_Type': 'AnyOtherSide'}
                metrics.update(compute_metrics(data, 'R'))
                metrics.update(compute_metrics(data, 'L'))"""

loop_replace2 = """                metrics = {'Language': lang_name_code, 'Table_Type': 'AnyOtherSide'}
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
                metrics.update(compute_metrics(data, 'L', 'AnyOtherSide', p2n, p2ls, p2lsq))"""
content = content.replace(loop_search2, loop_replace2)

with open('compute_sbl_laws.py', 'w') as f:
    f.write(content)

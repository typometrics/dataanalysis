import pickle
import numpy as np

def geometric_mean(vals):
    vals = [v for v in vals if v is not None and v > 0]
    if not vals: return np.nan
    return np.exp(np.mean(np.log(vals)))

def geometric_std(vals):
    vals = [v for v in vals if v is not None and v > 0]
    if not vals or len(vals) < 2: return np.nan
    log_vals = np.log(vals)
    return np.exp(np.std(log_vals, ddof=1))

with open('data/all_langs_position2num.pkl', 'rb') as f:
    pos2num = pickle.load(f)
with open('data/all_langs_position2logsizes.pkl', 'rb') as f:
    pos2logsizes = pickle.load(f)

# French example
lang = "fr"

print(f"Data for {lang}:")
diag_keys = ['right_2_totright_2', 'right_3_totright_3', 'right_4_totright_4']
rest_keys = ['right_1_totright_2', 'right_1_totright_3', 'right_2_totright_3']

diag_sizes = []
for k in diag_keys:
    if k in pos2logsizes[lang] and k in pos2num[lang] and pos2num[lang][k] > 0:
        diag_sizes.append(np.exp(pos2logsizes[lang][k] / pos2num[lang][k]))

rest_sizes = []
for k in rest_keys:
    if k in pos2logsizes[lang] and k in pos2num[lang] and pos2num[lang][k] > 0:
        rest_sizes.append(np.exp(pos2logsizes[lang][k] / pos2num[lang][k]))

print(f"Diag sizes: {diag_sizes}")
print(f"Rest sizes: {rest_sizes}")

if diag_sizes and rest_sizes:
    diag_gm = geometric_mean(diag_sizes)
    diag_gsd = geometric_std(diag_sizes)
    rest_gm = geometric_mean(rest_sizes)
    rest_gsd = geometric_std(rest_sizes)
    print(f"Diag GM: {diag_gm:.3f} (GSD: {diag_gsd:.3f})")
    print(f"Rest GM: {rest_gm:.3f} (GSD: {rest_gsd:.3f})")
    print(f"Ratio: {diag_gm / rest_gm:.3f}")

print("\nLeft side:")
diag_keys_l = ['left_2_totleft_2', 'left_3_totleft_3', 'left_4_totleft_4']
rest_keys_l = ['left_1_totleft_2', 'left_1_totleft_3', 'left_2_totleft_3']

diag_sizes_l = []
for k in diag_keys_l:
    if k in pos2logsizes[lang] and k in pos2num[lang] and pos2num[lang][k] > 0:
        diag_sizes_l.append(np.exp(pos2logsizes[lang][k] / pos2num[lang][k]))

rest_sizes_l = []
for k in rest_keys_l:
    if k in pos2logsizes[lang] and k in pos2num[lang] and pos2num[lang][k] > 0:
        rest_sizes_l.append(np.exp(pos2logsizes[lang][k] / pos2num[lang][k]))

print(f"Diag sizes: {diag_sizes_l}")
print(f"Rest sizes: {rest_sizes_l}")
if diag_sizes_l and rest_sizes_l:
    diag_gm_l = geometric_mean(diag_sizes_l)
    diag_gsd_l = geometric_std(diag_sizes_l)
    rest_gm_l = geometric_mean(rest_sizes_l)
    rest_gsd_l = geometric_std(rest_sizes_l)
    print(f"Diag GM: {diag_gm_l:.3f} (GSD: {diag_gsd_l:.3f})")
    print(f"Rest GM: {rest_gm_l:.3f} (GSD: {rest_gsd_l:.3f})")
    print(f"Ratio: {diag_gm_l / rest_gm_l:.3f}")

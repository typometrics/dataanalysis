import pickle
import sys
import os

sys.path.append('/bigstorage/kim/typometrics/dataanalysis')
DATA_DIR = 'data'

avg_path = os.path.join(DATA_DIR, 'all_langs_average_sizes_filtered.pkl')
if not os.path.exists(avg_path):
    print("Pickle not found")
    sys.exit(1)

with open(avg_path, 'rb') as f:
    data = pickle.load(f)

# Inspect first language
lang = next(iter(data))
print(f"Keys for language {lang}:")
keys = sorted(list(data[lang].keys()))
for k in keys:
    if 'anyother' not in k and 'tot' not in k: # filter distinct keys
        print(k)
    # Check specifically for 'left_all' or similar
    if 'all' in k or 'average' in k:
        print(f"FOUND INTERESTING KEY: {k}")

# Check specifically for global left/right keys
desired_keys = ['left_all', 'right_all', 'average_left', 'average_right', 'left_mean', 'right_mean']
found = [k for k in keys if k in desired_keys]
print("\nDirect matches:", found)

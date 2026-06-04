import pickle
import pandas as pd
import os

lang_code = 'yue'

# 1. Check what is in all_langs_average_sizes.pkl
with open('data/all_langs_average_sizes.pkl', 'rb') as f:
    avg_sizes = pickle.load(f)

yue_data = avg_sizes.get(lang_code, {})
print("From all_langs_average_sizes.pkl (used in graphs):")
for k in range(1, 5):
    key = f"right_{k}_totright_4"
    print(f"  {key}: {yue_data.get(key)}")

# 2. Check the raw TSV table values for Cantonese (yue)
print("\nFrom Standard_strict.tsv:")
tsv_path = f"data/helix_tables/Cantonese_{lang_code}/Standard_strict.tsv"
if os.path.exists(tsv_path):
    df = pd.read_csv(tsv_path, sep='\t')
    # Filter for R tot=4
    # The columns might be 'k', 'n', 'side' or 'row_name'
    print(df.to_string())
else:
    print(f"TSV not found at {tsv_path}")

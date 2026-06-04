import pickle
import pandas as pd

lang_code = 'yue'

with open('data/all_langs_average_sizes.pkl', 'rb') as f:
    avg_sizes = pickle.load(f)

yue_data = avg_sizes.get(lang_code, {})

print("Strict keys (currently plotted):")
for k in range(1, 5):
    print(f"  k={k}: {yue_data.get(f'right_{k}_totright_4')}")

print("\nAnyOtherSide keys:")
for k in range(1, 5):
    print(f"  k={k}: {yue_data.get(f'right_{k}_anyother_totright_4')}")


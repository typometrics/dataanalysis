import pandas as pd
import pickle

lang_code = 'yue'
lang_name = 'Cantonese'

tsv_path = f"data/helix_tables/{lang_name}_{lang_code}/Helix_{lang_name}_{lang_code}.tsv"
df = pd.read_csv(tsv_path, sep='\t')
row = df[df.iloc[:, 0].str.contains('R tot=4', na=False)]
print("Values in TSV for R tot=4:")
for col in df.columns:
    if not 'Unnamed' in col:
        print(f"  {col}: {row[col].values[0] if len(row) > 0 else 'N/A'}")

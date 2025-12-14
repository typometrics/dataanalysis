
import pickle
import os
import sys

# Path to data
data_path = '/bigstorage/kim/typometrics/dataanalysis/data/all_langs_average_sizes.pkl'

if os.path.exists(data_path):
    with open(data_path, 'rb') as f:
        data = pickle.load(f)
    
    # Pick French (fr)
    lang_data = data.get('fr', {})
    
    # Print keys to see what we have
    print(f"Keys for 'fr' ({len(lang_data)} keys):")
    sorted_keys = sorted(list(lang_data.keys()))
    
    # Print a sample of keys
    for k in sorted_keys[:20]:
        print(f"  {k}: {lang_data[k]}")
        
    # Check for 'count' or 'n' or 'num'
    count_keys = [k for k in sorted_keys if 'count' in k.lower() or 'num' in k.lower() or 'total' in k.lower()]
    print("\nPotential Count Keys:")
    for k in count_keys:
        print(f"  {k}: {lang_data[k]}")
        
else:
    print("Data file not found.")

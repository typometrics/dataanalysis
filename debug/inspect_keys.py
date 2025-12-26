import pickle
import sys

try:
    with open('data/all_langs_position2num.pkl', 'rb') as f:
        data = pickle.load(f)
        
    print("Keys for 'en':")
    if 'en' in data:
        keys = list(data['en'].keys())
        # Print a sample of keys, especially looking for 'average' or 'tot'
        for k in sorted(keys):
            print(k)
    else:
        print("Language 'en' not found in data.")
        
except Exception as e:
    print(e)

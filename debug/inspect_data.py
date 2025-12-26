import pickle
import sys

try:
    with open('data/metadata.pkl', 'rb') as f:
        meta = pickle.load(f)
    print("Keys:", meta.keys())
    if 'langNames' in meta:
        print("LangNames sample:", list(meta['langNames'].items())[:3])
    # check for other stats
    for k in meta:
        if k != 'langNames':
             print(f"{k}: {type(meta[k])}")
             if isinstance(meta[k], dict): 
                 print(f"Sample {k}: {list(meta[k].items())[:2]}")
except Exception as e:
    print(e)

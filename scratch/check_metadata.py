import pickle
import os

with open('data/metadata.pkl', 'rb') as f:
    metadata = pickle.load(f)

lang = 'abq'
print(f"Files for {lang}: {metadata['langConllFiles'].get(lang)}")
print(f"Name for {lang}: {metadata['langNames'].get(lang)}")

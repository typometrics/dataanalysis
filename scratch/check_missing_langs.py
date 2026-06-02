import pickle
import os

with open('data/metadata.pkl', 'rb') as f:
    metadata = pickle.load(f)

generated = [d for d in os.listdir('html_analyses/examples') if os.path.isdir(os.path.join('html_analyses/examples', d))]
all_langs = sorted(metadata['langConllFiles'].keys())

missing = [l for l in all_langs if l not in generated]
print(f"Total langs with conll files: {len(all_langs)}")
print(f"Total generated: {len(generated)}")
print(f"Missing languages in examples: {missing}")

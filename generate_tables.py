import pickle
import os
import sys
sys.path.append('public_scripts/src')
import verb_centered_analysis

with open('data/all_langs_average_sizes.pkl', 'rb') as f:
    sizes = pickle.load(f)
with open('data/all_langs_position2num.pkl', 'rb') as f:
    counts = pickle.load(f)
with open('data/ordering_stats.pkl', 'rb') as f:
    ordering_stats = pickle.load(f)
with open('data/metadata.pkl', 'rb') as f:
    metadata = pickle.load(f)

# Note: verb_centered_analysis.generate_mass_tables probably takes sizes, counts, etc.

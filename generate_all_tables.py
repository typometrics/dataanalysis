import os
import pickle
import sys

sys.path.append('public_scripts/src')
import verb_centered_analysis
import analysis
import data_utils

DATA_DIR = 'data'

# Load required data
with open(os.path.join(DATA_DIR, 'metadata.pkl'), 'rb') as f:
    metadata = pickle.load(f)

with open(os.path.join(DATA_DIR, 'all_langs_position2num.pkl'), 'rb') as f:
    all_langs_position2num = pickle.load(f)
    
with open(os.path.join(DATA_DIR, 'all_langs_position2sizes.pkl'), 'rb') as f:
    all_langs_position2sizes = pickle.load(f)

with open(os.path.join(DATA_DIR, 'sentence_disorder_percentages.pkl'), 'rb') as f:
    ordering_stats = pickle.load(f)

# Filter by min count = 10
all_langs_position2num_filtered, all_langs_position2sizes_filtered = analysis.filter_by_min_count(
    all_langs_position2num, all_langs_position2sizes, min_count=10
)

# Compute average sizes
all_langs_average_sizes_filtered = analysis.compute_average_sizes(
    all_langs_position2sizes_filtered, all_langs_position2num_filtered
)

# Generate tables
print("Generating mass tables...")
disorder_df = verb_centered_analysis.generate_mass_tables(
    all_langs_average_sizes_filtered,
    ordering_stats,
    metadata,
    vo_data=None,
    output_dir=os.path.join(DATA_DIR, 'helix_tables'),
    arrow_direction='outward'
)
print("Finished generating mass tables!")

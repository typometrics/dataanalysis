
import pickle
import os
import verb_centered_analysis
import sys

# Configuration
DATA_DIR = 'data'
TARGET_LANG = 'en'

print(f"Generating Verb-Centered Table for '{TARGET_LANG}'...")

# 1. Load Average Sizes
avg_file = os.path.join(DATA_DIR, 'all_langs_average_sizes_filtered.pkl')
if not os.path.exists(avg_file):
    print(f"ERROR: {avg_file} not found. Please run Notebook 04 (up to Cell 4) first.")
    sys.exit(1)

with open(avg_file, 'rb') as f:
    all_langs_average_sizes_filtered = pickle.load(f)

en_averages = {
    k: v for k, v in all_langs_average_sizes_filtered.get(TARGET_LANG, {}).items()
}

if not en_averages:
    print(f"ERROR: No average size data found for '{TARGET_LANG}'.")
    sys.exit(1)

# 2. Load Ordering Stats (Disorder Percentages)
disorder_file = os.path.join(DATA_DIR, 'sentence_disorder_percentages.pkl')
en_ordering_stats = None

if os.path.exists(disorder_file):
    with open(disorder_file, 'rb') as f:
        sentence_disorder_pct = pickle.load(f)
        en_ordering_stats = sentence_disorder_pct.get(TARGET_LANG, None)
        if en_ordering_stats:
             print(f"Loaded ordering stats for '{TARGET_LANG}'.")
        else:
             print(f"WARNING: '{TARGET_LANG}' not found in sentence_disorder_percentages.pkl.")
else:
    print(f"WARNING: {disorder_file} not found. Ordering triples will not be shown.")

# 3. Generate Table
table_str = verb_centered_analysis.format_verb_centered_table(
    en_averages,
    show_horizontal_factors=True,
    show_diagonal_factors=True,
    show_ordering_triples=True,
    show_row_averages=True,
    ordering_stats=en_ordering_stats,
    arrow_direction='rightwards'
)

print("\n" + table_str)

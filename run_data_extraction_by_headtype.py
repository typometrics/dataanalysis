#!/usr/bin/env python
"""
Run data extraction for different head types: verb, noun, and all (joint).

This script generates separate pickle files for each head type to enable
comparison of MAL (Menzerath-Altmann Law) effects across different syntactic contexts.

Output files created:
- data/all_langs_average_sizes_verb.pkl
- data/all_langs_average_sizes_noun.pkl  
- data/all_langs_average_sizes_all.pkl
- (and similar for position2sizes, position2num, etc.)
"""

import os
import pickle
import data_utils
import conll_processing
import psutil

DATA_DIR = "data"

# Load metadata
print("Loading metadata...")
metadata = data_utils.load_metadata(os.path.join(DATA_DIR, 'metadata.pkl'))
langShortConllFiles = metadata['langShortConllFiles']
langNames = metadata['langNames']

# Flatten file list
allshortconll = []
for lang, files in langShortConllFiles.items():
    allshortconll.extend(files)

print(f"Total files to process: {len(allshortconll)}")
print(f"Using {psutil.cpu_count()} cores")

# Head types to process
HEAD_TYPES = ['verb', 'noun', 'all']

for head_type in HEAD_TYPES:
    print(f"\n{'='*60}")
    print(f"Processing head_type='{head_type}'...")
    print(f"{'='*60}")
    
    results = conll_processing.get_all_stats_parallel(
        allshortconll,
        include_bastards=True,
        compute_sentence_disorder=True,
        collect_config_examples=False,  # Skip examples to save time
        max_examples_per_config=0,
        head_type=head_type
    )
    
    # Unpack results
    (all_langs_position2num, all_langs_position2sizes, all_langs_average_sizes, all_langs_average_charsizes,
     lang_bastard_stats, global_bastard_relations, 
     lang_vo_hi_scores, 
     sentence_disorder_pct) = results
    
    # Save with head_type suffix
    suffix = f"_{head_type}"
    
    output_files = {
        f'all_langs_average_sizes{suffix}.pkl': all_langs_average_sizes,
        f'all_langs_average_charsizes{suffix}.pkl': all_langs_average_charsizes,
        f'all_langs_position2sizes{suffix}.pkl': all_langs_position2sizes,
        f'all_langs_position2num{suffix}.pkl': all_langs_position2num,
    }
    
    for filename, data in output_files.items():
        output_path = os.path.join(DATA_DIR, filename)
        with open(output_path, 'wb') as f:
            pickle.dump(data, f)
        print(f"  Saved: {filename}")
    
    print(f"Completed head_type='{head_type}'")

print(f"\n{'='*60}")
print("All head types processed successfully!")
print(f"{'='*60}")

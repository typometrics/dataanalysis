import os
import pickle
import data_utils
import conll_processing
from tqdm import tqdm
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

print(f"Processing {len(allshortconll)} files on {psutil.cpu_count()} cores...")

compute_sentence_disorder = True

results = conll_processing.get_all_stats_parallel(
    allshortconll,
    include_bastards=True,
    compute_sentence_disorder=compute_sentence_disorder
)

print("Processing complete. Unpacking results...")

(all_langs_position2num, all_langs_position2sizes, all_langs_average_sizes, all_langs_average_charsizes,
 lang_bastard_stats, global_bastard_relations, 
 lang_vo_hi_scores, 
 sentence_disorder_pct) = results

# Save results
print("Saving results...")
output_path = os.path.join(DATA_DIR, 'all_langs_average_charsizes.pkl')
with open(output_path, 'wb') as f:
    pickle.dump(all_langs_average_charsizes, f)

# Also save position2sizes if needed (Notebook 02 does this)
with open(os.path.join(DATA_DIR, 'all_langs_position2sizes.pkl'), 'wb') as f:
    pickle.dump(all_langs_position2sizes, f)

with open(os.path.join(DATA_DIR, 'all_langs_position2num.pkl'), 'wb') as f:
    pickle.dump(all_langs_position2num, f)

print(f"Saved average char sizes to {output_path}")
print("Done!")

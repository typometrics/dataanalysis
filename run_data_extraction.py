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
collect_config_examples = True  # Enable example collection

results = conll_processing.get_all_stats_parallel(
    allshortconll,
    include_bastards=True,
    compute_sentence_disorder=compute_sentence_disorder,
    collect_config_examples=collect_config_examples,
    max_examples_per_config=25
)

print("Processing complete. Unpacking results...")

if collect_config_examples:
    (all_langs_position2num, all_langs_position2sizes, all_langs_average_sizes, all_langs_average_charsizes,
     all_langs_position2logsizes, all_langs_position2logsqsizes,
     lang_bastard_stats, global_bastard_relations, 
     lang_vo_hi_scores, 
     all_langs_ordering_stats,
     all_config_examples) = results
else:
    (all_langs_position2num, all_langs_position2sizes, all_langs_average_sizes, all_langs_average_charsizes,
     all_langs_position2logsizes, all_langs_position2logsqsizes,
     lang_bastard_stats, global_bastard_relations, 
     lang_vo_hi_scores, 
     all_langs_ordering_stats) = results
    all_config_examples = None

# Save results
print("Saving results...")
output_path = os.path.join(DATA_DIR, 'all_langs_average_charsizes.pkl')
with open(output_path, 'wb') as f:
    pickle.dump(all_langs_average_charsizes, f)

# Also save position2sizes if needed (Notebook 02 does this)
with open(os.path.join(DATA_DIR, 'all_langs_position2sizes.pkl'), 'wb') as f:
    pickle.dump(all_langs_position2sizes, f)

with open(os.path.join(DATA_DIR, 'all_langs_average_sizes.pkl'), 'wb') as f:
    pickle.dump(all_langs_average_sizes, f)
    print(f"Saved average sizes to {os.path.join(DATA_DIR, 'all_langs_average_sizes.pkl')}")

with open(os.path.join(DATA_DIR, 'all_langs_position2num.pkl'), 'wb') as f:
    pickle.dump(all_langs_position2num, f)

with open(os.path.join(DATA_DIR, 'all_langs_position2logsizes.pkl'), 'wb') as f:
    pickle.dump(all_langs_position2logsizes, f)

with open(os.path.join(DATA_DIR, 'all_langs_position2logsqsizes.pkl'), 'wb') as f:
    pickle.dump(all_langs_position2logsqsizes, f)

with open(os.path.join(DATA_DIR, 'sentence_disorder_percentages.pkl'), 'wb') as f:
    pickle.dump(all_langs_ordering_stats, f)

# Save config examples if collected
if all_config_examples is not None:
    config_examples_path = os.path.join(DATA_DIR, 'all_config_examples.pkl')
    with open(config_examples_path, 'wb') as f:
        pickle.dump(all_config_examples, f)
    print(f"Saved configuration examples to {config_examples_path}")

print(f"Saved average char sizes to {output_path}")
print("Done!")

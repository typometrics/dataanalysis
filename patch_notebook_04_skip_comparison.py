
import json

notebook_path = '/bigstorage/kim/typometrics/dataanalysis/04_data_processing.ipynb'

with open(notebook_path, 'r') as f:
    nb = json.load(f)

# Content to identify the cell (from traceback)
# "Comparison: Sentence-Level vs Average-Level Disorder"
target_text = "COMPARISON: Sentence-Level vs Average-Level Disorder"

found = False
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source_str = "".join(cell['source'])
        if target_text in source_str:
            # Replace the source with a comment
            cell['source'] = [
                "# Comparison section disabled.\n",
                "# The disorder calculation has been updated to use granular sentence-level statistics by default,\n",
                "# so 'disorder_df' now already contains the continuous percentages.\n",
                "# The distinction between 'Average-Level' and 'Sentence-Level' is no longer relevant for this comparison.\n",
                "print('Comparison skipped: Disorder scores are now continuous by default.')\n"
            ]
            found = True
            break

if found:
    with open(notebook_path, 'w') as f:
        json.dump(nb, f, indent=4)
    print("Successfully disabled comparison cell.")
else:
    print("Comparison cell not found.")

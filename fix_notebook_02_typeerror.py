
import json

nb_path = "/bigstorage/kim/typometrics/dataanalysis/02_dependency_analysis.ipynb"

with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

found = False
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = cell["source"]
        # Look for the specific loop
        # "        for (side, tot, idx), counts in sentence_disorder_pct[lang_code].items():\n",
        
        idx_start = -1
        for i, line in enumerate(source):
            if "for (side, tot, idx), counts in sentence_disorder_pct[lang_code].items():" in line:
                idx_start = i
                break
        
        if idx_start != -1:
            # Check if next line is already patched
            if "isinstance(counts, int)" in source[idx_start + 1]:
                print("Notebook already patched.")
                found = True
                break
                
            print(f"Found target cell. Patching lines starting at {idx_start}...")
            
            # Original lines to replace:
            # Loop line
            # "            total = counts['lt'] + counts['eq'] + counts['gt']\n",
            
            # Insert new lines
            new_lines = [
                "            if isinstance(counts, int):\n",
                "                # Handle integer total counts\n",
                "                row[f'{side}_tot_{tot}_{idx}'] = counts\n",
                "                continue\n",
                "            \n"
            ]
            
            # Insert after the loop definition line (idx_start)
            # The structure of source is a list of strings (lines).
            # We insert at idx_start + 1.
            
            for l in reversed(new_lines):
                source.insert(idx_start + 1, l)
            
            cell["source"] = source
            found = True
            break

if found:
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1) # Notebooks usually use indent=1 or different spacing... default is None? 
        # Actually standard ipynb formatter might be different. 
        # Let's hope basic json dump doesn't create huge diff noise. 
        # Usually it is better to read text, replace text, and write text to preserve formatting.
    print("Notebook updated successfully.")
else:
    print("Target code block not found.")

# Alternative safe write that preserves most formatting defaults?
# But json.dump is standard.

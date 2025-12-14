
import json

nb_path = "/bigstorage/kim/typometrics/dataanalysis/02_dependency_analysis.ipynb"

with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

found = False
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = cell["source"]
        
        # Look for where df_ranking is printed or displayed
        # "print(\"Top Languages by Bastard Frequency (per Verb):\")\n",
        idx_match = -1
        for i, line in enumerate(source):
            if "Top Languages by Bastard Frequency" in line:
                idx_match = i
                break
        
        if idx_match != -1:
            print("Found target cell.")
            
            # Append code to save the dataframe
            # Check if already present
            if any("to_csv" in l for l in source):
                print("Save usage already found in cell.")
                found = True
                break
            
            # We add it at the end of the cell
            source.append("\n")
            source.append("# Save bastard stats to CSV for further analysis (e.g. Notebook 05)\n")
            source.append("bastard_csv_path = os.path.join(DATA_DIR, 'bastard_stats.csv')\n")
            source.append("df_ranking.to_csv(bastard_csv_path, index=False)\n")
            source.append("print(f\"Saved bastard statistics to {bastard_csv_path}\")\n")
            
            cell["source"] = source
            found = True
            break

if found:
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    print("Notebook 02 updated successfully.")
else:
    print("Target cell in 02 not found.")

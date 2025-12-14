
import json

nb_path = "/bigstorage/kim/typometrics/dataanalysis/04_data_processing.ipynb"

with open(nb_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

found = False
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        source = cell["source"]
        
        # Look for the print block
        # "    print(\"DISORDER PERCENTAGE BY CONFIGURATION\")\n",
        idx_start = -1
        for i, line in enumerate(source):
            if "DISORDER PERCENTAGE BY CONFIGURATION" in line:
                idx_start = i
                break
        
        if idx_start != -1:
            print("Found target cell.")
            
            # We will replace the entire logic in that cell to include explanation and saving.
            # The cell effectively starts at the top (it's the 'Additional analysis' cell).
            # Let's verify context: `if merged_df is not None:`
            
            new_source = [
                "# Additional analysis: Show disorder percentage by configuration\n",
                "if merged_df is not None:\n",
                "    output_lines = []\n",
                "    output_lines.append(\"=\"*60)\n",
                "    output_lines.append(\"DISORDER PERCENTAGE BY CONFIGURATION\")\n",
                "    output_lines.append(\"=\"*60)\n",
                "    output_lines.append(\"Explanation:\")\n",
                "    output_lines.append(\"Counts indicate the number of languages where ALL sentences (100%)\")\n",
                "    output_lines.append(\"in that configuration are considered 'disordered'.\")\n",
                "    output_lines.append(\"Disordered means the sizes do not follow the expected order\")\n",
                "    output_lines.append(\"(Short-before-Long on Right, Decreasing-Size-to-Verb on Left).\")\n",
                "    output_lines.append(\"-\"*60)\n",
                "    \n",
                "    all_configs = [\n",
                "        ('right_tot_2_disordered', 'R tot=2 (V X X)'),\n",
                "        ('right_tot_3_disordered', 'R tot=3 (V X X X)'),\n",
                "        ('right_tot_4_disordered', 'R tot=4 (V X X X X)'),\n",
                "        ('left_tot_2_disordered', 'L tot=2 (X X V)'),\n",
                "        ('left_tot_3_disordered', 'L tot=3 (X X X V)'),\n",
                "        ('left_tot_4_disordered', 'L tot=4 (X X X X V)'),\n",
                "    ]\n",
                "    \n",
                "    for config_col, config_label in all_configs:\n",
                "        if config_col in merged_df.columns:\n",
                "            config_data = merged_df[config_col].dropna()\n",
                "            n_total = len(config_data)\n",
                "            # Integers: 1 if score=1.0 (fully disordered), 0 otherwise\n",
                "            n_disordered = config_data.astype(int).sum()\n",
                "            pct = (n_disordered / n_total * 100) if n_total > 0 else 0\n",
                "            \n",
                "            line = f\"{config_label:<25} {n_disordered}/{n_total} languages ({pct:>5.1f}%) fully disordered\"\n",
                "            output_lines.append(line)\n",
                "    \n",
                "    output_lines.append(\"=\"*60)\n",
                "    \n",
                "    # Print\n",
                "    print(\"\\n\".join(output_lines))\n",
                "    \n",
                "    # Save to file\n",
                "    import os\n",
                "    output_table_dir = 'data/tables'\n",
                "    if not os.path.exists(output_table_dir):\n",
                "        os.makedirs(output_table_dir)\n",
                "    \n",
                "    with open(os.path.join(output_table_dir, 'disorder_summary.txt'), 'w', encoding='utf-8') as f:\n",
                "        f.write(\"\\n\".join(output_lines))\n",
                "    print(f\"\\nSaved summary to {output_table_dir}/disorder_summary.txt\")\n"
            ]
            
            cell["source"] = new_source
            found = True
            break
            
if found:
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    print("Notebook updated successfully.")
else:
    print("Target cell not found.")

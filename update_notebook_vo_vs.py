
import nbformat

nb_path = '05_comparative_visualization.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

cells_to_remove = []
for cell in nb.cells:
    if cell.cell_type == 'markdown':
        if "VO vs VOnominal Analysis" in cell.source:
            cells_to_remove.append(cell)
            # Also find the next code cell which likely does the plotting
            idx = nb.cells.index(cell)
            if idx + 1 < len(nb.cells) and nb.cells[idx+1].cell_type == 'code':
                cells_to_remove.append(nb.cells[idx+1])
    
    if cell.cell_type == 'markdown' and "VS vs VO Analysis" in cell.source:
        cell.source = """## VSnom vs VOnom Analysis

Analyze the relationship between Nominal Subject-Verb order (VSnom score) and Nominal Verb-Object order (VOnom score) across different language groups.

**Note:**
- **VOnom**: Counts only **nominal (NOUN)** objects.
- **VSnom**: Counts only **nominal (NOUN)** subjects.
- The `sv_score` measures the proportion of nominal subjects that appear **after** the verb (VS order)."""

# Remove identified cells
for cell in cells_to_remove:
    if cell in nb.cells:
        nb.cells.remove(cell)
        print("Removed cell: " + cell.source[:50] + "...")

with open(nb_path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("Notebook updated successfully.")

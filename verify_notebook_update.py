
import nbformat

nb_path = '05_comparative_visualization.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

found = False
for cell in nb.cells:
    if cell.cell_type == 'code':
        if "Average Constituent Size: Words vs Letters" in cell.source and "Diagonal (y=x)" in cell.source:
            print("SUCCESS: Found updated cell.")
            print("-" * 20)
            print(cell.source[:200] + "...")
            print("..." + cell.source[-200:])
            print("-" * 20)
            found = True
            break

if not found:
    print("FAILURE: Could not find updated cell.")

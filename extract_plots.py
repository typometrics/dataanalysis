import json
import base64
import os

notebook_path = '/bigstorage/kim/typometrics/dataanalysis/09_verbal_vs_nominal_mal.ipynb'
output_dir = '/bigstorage/kim/typometrics/dataanalysis/plots'

with open(notebook_path, 'r') as f:
    nb = json.load(f)

# Find cell 23 (or the one with the plots)
target_cell = None
for cell in nb['cells']:
    if cell.get('execution_count') == 23:
        target_cell = cell
        break

if target_cell:
    print("Found cell 23")
    image_count = 0
    for output in target_cell.get('outputs', []):
        data = output.get('data', {})
        if 'image/png' in data:
            image_count += 1
            img_data = data['image/png']
            # Decode
            img_bytes = base64.b64decode(img_data)
            
            # Name them sequentially for now, user can rename or we check content later
            # Assuming the order: Verb vs Noun, Verb vs All, Noun vs All?
            # Or maybe they are named in the notebook output metadata? No usually.
            filename = f"mal_scatter_comparison_{image_count}.png"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'wb') as f_img:
                f_img.write(img_bytes)
            print(f"Saved {filepath}")
else:
    print("Cell 23 not found")

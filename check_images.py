import re
import os

md_file = '/bigstorage/kim/typometrics/dataanalysis/draft_section_MAL.md'
base_dir = '/bigstorage/kim/typometrics/dataanalysis'

print(f"Checking images in {md_file}...")

with open(md_file, 'r') as f:
    content = f.read()

# Regex for markdown images: ![alt](path)
# Also handle potential title attributes ![alt](path "title")
image_refs = re.findall(r'!\[.*?\]\((.*?)(?:\s+".*?")?\)', content)

missing_count = 0
for ref in image_refs:
    # Cleanup ref if needed (sometimes verify ignores query params etc, but here plain files)
    ref = ref.strip()
    full_path = os.path.join(base_dir, ref)
    if not os.path.exists(full_path):
        print(f"[MISSING] {ref}")
        print(f"  Expected at: {full_path}")
        missing_count += 1
    else:
        print(f"[OK] {ref}")

if missing_count == 0:
    print(f"\nAll {len(image_refs)} image references verified.")
else:
    print(f"\nFound {missing_count} missing images.")

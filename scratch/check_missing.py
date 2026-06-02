import json
import os

# Extract ROWS from mal_explorer.html
html_path = 'html_analyses/mal_explorer.html'
with open(html_path, 'r') as f:
    content = f.read()

start_marker = 'const ROWS = '
end_marker = '];'
start = content.find(start_marker) + len(start_marker)
end = content.find(end_marker, start) + 1
rows_json = content[start:end]
rows = json.loads(rows_json)

missing = []
for r in rows:
    code = r['code']
    idx_path = f'html_analyses/examples/{code}/index.html'
    if not os.path.exists(idx_path):
        missing.append(code)

print(f"Total languages in explorer: {len(rows)}")
print(f"Missing example index for: {missing}")

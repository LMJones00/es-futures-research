import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('analysis.ipynb', 'r', encoding='utf-8', errors='replace') as f:
    nb = json.load(f)

cells = nb['cells']

# Just get markdown sections (which describe what each section does)
md_sections = []
for i, cell in enumerate(cells):
    if cell['cell_type'] == 'markdown':
        text = ''.join(cell.get('source', [])).strip()
        if text:
            md_sections.append((i, text))

for idx, text in md_sections:
    print(f"[{idx}] {text}\n")


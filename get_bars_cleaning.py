import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('barsToCleaning.ipynb', 'r', encoding='utf-8', errors='replace') as f:
    nb = json.load(f)

cells = nb['cells']

# Cells 2-30 contain the main logic
for i in range(2, min(30, len(cells))):
    cell = cells[i]
    if cell['cell_type'] == 'markdown':
        text = ''.join(cell.get('source', [])).strip()
        if text:
            print(f"\n[MD] {text}\n")
    elif cell['cell_type'] == 'code':
        code = ''.join(cell.get('source', []))
        if code.strip():
            # Print just the key parts
            lines = code.split('\n')
            for j, line in enumerate(lines):
                if line.strip() and not line.strip().startswith(('import ', 'from ', '%')):
                    print(line)


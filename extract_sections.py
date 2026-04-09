import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def extract_code_sections(nb_path, start_cell=None, end_cell=None):
    with open(nb_path, 'r', encoding='utf-8', errors='replace') as f:
        nb = json.load(f)
    
    cells = nb['cells']
    if start_cell:
        cells = [c for i, c in enumerate(cells) if i >= start_cell]
    if end_cell:
        cells = [c for i, c in enumerate(cells) if i <= end_cell]
    
    for i, cell in enumerate(cells):
        if cell['cell_type'] == 'markdown':
            text = ''.join(cell.get('source', [])).strip()
            if text:
                print(f"\n[MD] {text}\n")
        elif cell['cell_type'] == 'code':
            code = ''.join(cell.get('source', []))
            if code.strip():
                print(f"[CODE]\n{code}\n")
                print("---" * 20)

print("=" * 80)
print("PREPARING.IPYNB - SECTIONS 5-13 (Feature Engineering)")
print("=" * 80)
extract_code_sections('preparing.ipynb', start_cell=10, end_cell=30)


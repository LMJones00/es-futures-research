import json
import sys
from pathlib import Path

# Force UTF-8 output
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

nb_path = sys.argv[1] if len(sys.argv) > 1 else 'barsToCleaning.ipynb'

try:
    with open(nb_path, 'r', encoding='utf-8', errors='replace') as f:
        nb = json.load(f)
    
    print(f"\n{'=' * 80}")
    print(f"Notebook: {nb_path}")
    print(f"{'=' * 80}\n")
    
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'markdown':
            text = ''.join(cell.get('source', [])).strip()
            if text and text.startswith('#'):
                print(f"[Cell {i}] {text[:200]}")
        elif cell['cell_type'] == 'code':
            code = ''.join(cell.get('source', []))
            # Show first meaningful line or comment
            for line in code.split('\n')[:3]:
                if line.strip() and not line.strip().startswith('import'):
                    print(f"[Cell {i}] {line[:100]}")
                    break

except Exception as e:
    print(f"Error: {e}")


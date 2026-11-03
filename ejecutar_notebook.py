"""Ejecuta el notebook y preserva sus salidas incluso si ocurre un error."""
from pathlib import Path
import json
import os
import sys
import nbformat
from nbclient import NotebookClient

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

root = Path(__file__).resolve().parent
jupyter_path = root / '.jupyter'
kernel = jupyter_path / 'kernels' / 'caltech-local'
kernel.mkdir(parents=True, exist_ok=True)
(kernel / 'kernel.json').write_text(json.dumps({
    'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
    'display_name': 'Caltech local', 'language': 'python',
}), encoding='utf-8')
os.environ['JUPYTER_PATH'] = str(jupyter_path)
os.environ['JUPYTER_RUNTIME_DIR'] = str(jupyter_path / 'runtime')
os.environ['IPYTHONDIR'] = str(root / '.ipython')
os.environ['PYTHONIOENCODING'] = 'utf-8'
path = root / 'Caltech101_10_clases_ejecutado.ipynb'
nb = nbformat.read(path, as_version=4)


def on_cell_start(cell, cell_index, **kwargs):
    if cell.cell_type == 'code':
        print(f'Iniciando celda {cell_index + 1}: {cell.source.splitlines()[0][:90]}', flush=True)


def on_cell_executed(cell, cell_index, **kwargs):
    nbformat.write(nb, path)
    print(f'Celda {cell_index + 1} completada.', flush=True)
    for output in cell.get('outputs', []):
        if output.output_type == 'stream':
            lines = output.text.strip().splitlines()
            print('\n'.join(lines[-4:]), flush=True)


client = NotebookClient(nb, timeout=7200, kernel_name='caltech-local',
    resources={'metadata': {'path': str(root)}},
    on_cell_start=on_cell_start, on_cell_executed=on_cell_executed)
try:
    client.execute()
finally:
    nbformat.write(nb, path)
print('Ejecución completa y notebook guardado.', flush=True)

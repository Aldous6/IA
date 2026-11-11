"""Empaqueta código, datos, resultados e informe; comprueba archivos y notebook."""
from pathlib import Path
import hashlib
import json
import zipfile

import nbformat

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'entrega'
nombre = 'Tarea_6_TSP_Busqueda_Tabu'

nb = nbformat.read(OUT / f'{nombre}.ipynb', as_version=4)
nbformat.validate(nb)
celdas = [c for c in nb.cells if c.cell_type == 'code']
assert all(c.execution_count is not None for c in celdas)
assert not [o for c in celdas for o in c.outputs if o.output_type == 'error']

primera = json.loads((ROOT / 'resultados/experimento.json').read_text(encoding='utf-8'))
segunda = json.loads((OUT / 'tarea6_resultados/resultados/experimento.json').read_text(encoding='utf-8'))
claves = lambda r: (r['n'], r['semilla'], r['algoritmo'])
costos = lambda experimento: {claves(r): r['mejor_costo'] for r in experimento['corridas']}
assert len(primera['corridas']) == len(segunda['corridas']) == 160
assert costos(primera) == costos(segunda)
assert all(r['evaluaciones'] == 91700 for e in [primera, segunda] for r in e['corridas'])

with zipfile.ZipFile(OUT / f'{nombre}.docx') as documento:
    assert documento.testzip() is None

archivos = [p for p in ROOT.glob('*.py')]
archivos += [ROOT / n for n in ['LEEME.md', 'requirements.txt', 'requirements_entrega.txt']]
archivos += sorted((ROOT / 'datos').glob('*'))
archivos += sorted((ROOT / 'material').glob('*.txt'))
archivos += [p for p in sorted((ROOT / 'resultados').glob('*'))
             if p.is_file() and p.name != 'verificacion_entrega.json'
             and not p.name.startswith(('revision_p', 'colab_figura_revision'))]
archivos += [OUT / f'{nombre}.{ext}' for ext in ['docx', 'pdf', 'ipynb']]
archivos += [OUT / 'Resultados_Tarea_6.zip']
assert all(p.is_file() for p in archivos)

manifiesto = {
    'tarea': 6,
    'corridas_primera_ejecucion': 160,
    'corridas_notebook_ejecutado': 160,
    'celdas_codigo_ejecutadas': len(celdas),
    'errores_notebook': 0,
    'costos_reproducidos': 160,
    'evaluaciones_por_corrida': 91700,
    'sha256': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(set(archivos))},
}
verificacion = ROOT / 'resultados/verificacion_entrega.json'
verificacion.write_text(json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding='utf-8')
archivos = [p for p in archivos if p != verificacion] + [verificacion]
destino = OUT / 'Tarea_6_Completa.zip'
with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as paquete:
    for archivo in sorted(set(archivos)):
        paquete.write(archivo, Path('Tarea_6') / archivo.relative_to(ROOT))
with zipfile.ZipFile(destino) as paquete:
    assert paquete.testzip() is None
    assert len(paquete.namelist()) == len(set(paquete.namelist()))
print(f'Paquete completo y verificado: {destino.name}, {destino.stat().st_size:,} bytes.')
print('Dos ejecuciones completas; 160 mejores costos reproducidos; notebook sin errores.')

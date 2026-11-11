"""Empaqueta los documentos, el Colab ejecutado y los resultados reproducibles."""
from pathlib import Path
import hashlib
import json
import math
import platform
import sys
import zipfile
import nbformat
import numpy as np
import pandas as pd
import matplotlib

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'entrega'
datos = json.loads((ROOT / 'resultados/experimento.json').read_text(encoding='utf-8'))
optimo = json.loads((ROOT / 'resultados/optimo_exacto.json').read_text(encoding='utf-8'))
principal = datos['principal']
assert len(datos['ciudades']) == 15
assert len(datos['corridas']) == 20
assert all(math.isclose(r['mejor_costo'], optimo['costo_optimo'], abs_tol=1e-8, rel_tol=0)
           for r in datos['corridas'])
assert principal['propuestas'] == 91700 and principal['niveles'] == 917

nb_path = OUT / 'Tarea_5_TSP_Templado_Simulado.ipynb'
nb = nbformat.read(nb_path, as_version=4)
nbformat.validate(nb)
code = [c for c in nb.cells if c.cell_type == 'code']
assert [c.execution_count for c in code] == list(range(1, 11))
assert not [o for c in code for o in c.outputs if o.output_type == 'error']
assert sum('image/png' in o.get('data', {}) for c in code for o in c.outputs) == 2

config = {
    'python': platform.python_version(), 'numpy': np.__version__,
    'pandas': pd.__version__, 'matplotlib': matplotlib.__version__,
    'numero_ciudades': 15, 'semilla_datos': 42, 'semilla_principal': 0,
    'semillas_experimento': list(range(20)),
    'parametros': datos['parametros'],
    'distancia': 'euclidiana sin redondear; ciclo cerrado; unidades del plano',
    'vecino': 'intercambio de dos posiciones distintas de la permutación',
    'aceptacion': 'Delta<0: siempre; Delta>=0: 1/(1+exp(Delta/T)); Delta=nuevo-actual',
    'tolerancia_comparacion_optimo': 1e-8,
    'datos_sha256': hashlib.sha256((ROOT / 'datos/ciudades.csv').read_bytes()).hexdigest(),
}
(ROOT / 'resultados/configuracion.json').write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')

readme = '''La Tarea 5 está desarrollada en Word y PDF y tiene un notebook de Colab ya ejecutado. Para abrir el .ipynb en Colab, usa Archivo → Abrir notebook → Subir. La instancia de 15 ciudades viene incluida.

Se utilizan ciudades sintéticas C01–C15 en un plano, con coordenadas de ejemplo generadas con semilla 42. Las distancias son euclidianas, se calculan sin redondear y se incluye el regreso al origen. Las unidades son las del plano.

El vecino se obtiene intercambiando dos posiciones distintas. Se respeta la logística de las láminas 27–29 de la presentación 8 y el pseudocódigo de la 30: las mejoras estrictas se aceptan siempre; en otro caso p = 1/(1+exp((costo_nuevo-costo_actual)/T)). Los empates tienen p = 0.5.

La temperatura comienza en 100 y baja un 1 % después de cada 100 propuestas, hasta ser menor que 0.01. El recorrido principal usa semilla 0. Se conserva el mejor recorrido visitado por separado del actual.

La corrida principal pasó de 631.089690 a 288.609288 unidades, una reducción de 54.268103 %. Las 20 semillas probadas coincidieron con el óptimo de referencia para esta instancia. La referencia Held–Karp se calcula de forma independiente y no dirige la búsqueda de Templado Simulado. Este resultado no implica una garantía general para toda instancia o corrida.

Para ejecutar el programa local, instala requirements.txt y ejecuta python tsp_templado.py. Para repetir la referencia exacta, ejecuta python referencia_exacta.py. Cada script lee datos/ciudades.csv y escribe en resultados/. El notebook es autocontenido y también genera sus propios archivos de salida.

La carpeta resultados contiene la matriz de distancias, el historial de la corrida principal, los costos de las 20 corridas, la referencia exacta, la configuración y las dos figuras. Los documentos incluyen la explicación de la fórmula, los parámetros, las rutas y las fuentes de consulta.
'''
(OUT / 'LEEME.txt').write_text(readme, encoding='utf-8')
(OUT / 'requirements.txt').write_text('numpy>=1.26\npandas>=2\nmatplotlib>=3.8\n', encoding='utf-8')

files = {
    OUT / 'Tarea_5_TSP_Templado_Simulado.docx': 'Tarea_5_TSP_Templado_Simulado.docx',
    OUT / 'Tarea_5_TSP_Templado_Simulado.pdf': 'Tarea_5_TSP_Templado_Simulado.pdf',
    nb_path: nb_path.name,
    OUT / 'LEEME.txt': 'LEEME.txt',
    OUT / 'requirements.txt': 'requirements.txt',
    ROOT / 'tsp_templado.py': 'tsp_templado.py',
    ROOT / 'referencia_exacta.py': 'referencia_exacta.py',
    ROOT / 'datos/ciudades.csv': 'datos/ciudades.csv',
}
for filename in ['experimento.json', 'optimo_exacto.json', 'historial_semilla0.csv',
                 'corridas.csv', 'distancias.csv', 'configuracion.json', 'rutas.png', 'convergencia.png']:
    files[ROOT / 'resultados' / filename] = 'resultados/' + filename
for path in files:
    assert path.is_file() and path.stat().st_size > 0, path
target = OUT / 'Entrega_Tarea_5_TSP.zip'
with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for path, name in files.items():
        archive.write(path, name)
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    assert len(archive.namelist()) == len(files)
print('Paquete verificado:', target.name, '| Archivos:', len(files), '| bytes:', target.stat().st_size)

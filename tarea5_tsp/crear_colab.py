"""Crea y ejecuta el notebook autocontenido de la Tarea 5."""
from pathlib import Path
import ast
import csv
import json
import os
import sys
import textwrap
import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'entrega'
OUT.mkdir(exist_ok=True)
TARGET = OUT / 'Tarea_5_TSP_Templado_Simulado.ipynb'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def extraer_funciones(path, names):
    text = Path(path).read_text(encoding='utf-8')
    tree = ast.parse(text)
    by_name = {node.name: ast.get_source_segment(text, node)
               for node in tree.body if isinstance(node, ast.FunctionDef)}
    return '\n\n\n'.join(by_name[name] for name in names)


def md(text):
    return nbf.v4.new_markdown_cell(textwrap.dedent(text).strip())


def code(text, **metadata):
    return nbf.v4.new_code_cell(textwrap.dedent(text).strip(), metadata=metadata)


with (ROOT / 'datos' / 'ciudades.csv').open(encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
points = [[int(r['x']), int(r['y'])] for r in rows]
core = ROOT / 'tsp_templado.py'
exact = ROOT / 'referencia_exacta.py'

cells = [
    md('''
        **Tarea 5: TSP de 15 ciudades mediante Templado Simulado**

        Se sigue la tarea de la lámina 32 de la presentación 8. Cada ruta es una
        permutación de 15 ciudades y cada vecina se obtiene intercambiando dos
        posiciones distintas elegidas al azar. Se busca minimizar la distancia
        total y regresar a la ciudad inicial.

        El notebook conserva una ejecución completa. En Colab se puede repetir
        con **Entorno de ejecución → Ejecutar todas**. Las coordenadas están
        incluidas; las ciudades son un ejemplo sintético reproducible, con
        distancias en unidades del plano.
    '''),
    code('''
        import math
        import random
        import time
        import json
        from pathlib import Path
        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        from IPython.display import display, Markdown

        SALIDA = Path('resultados_tsp')
        SALIDA.mkdir(exist_ok=True)
    '''),
    md('''
        La presentación no establece ciudades ni distancias concretas. Se
        eligieron 15 puntos distintos generados con semilla 42 y se conservan
        explícitamente para repetir la misma instancia. No representan kilómetros
        entre municipios reales. La semilla del recorrido principal será 0.
    '''),
    code('coordenadas = np.array(' + json.dumps(points) + ', dtype=float)\n'
         "ciudades = [f'C{i+1:02d}' for i in range(len(coordenadas))]\n"
         "tabla_ciudades = pd.DataFrame(coordenadas.astype(int), columns=['x', 'y'])\n"
         "tabla_ciudades.insert(0, 'ciudad', ciudades)\n"
         'display(tabla_ciudades)\n'
         "tabla_ciudades.to_csv(SALIDA / 'ciudades.csv', index=False)"),
    md(r'''
        La distancia entre dos ciudades es euclidiana:
        $d(i,j)=\sqrt{(x_i-x_j)^2+(y_i-y_j)^2}$.
        Para una ruta $v$, se suman sus 15 aristas, incluida la última hacia
        la primera. La función `vecino_intercambio` copia `vc` y cambia sólo dos
        posiciones para producir `vn`. Hay $\binom{15}{2}=105$ intercambios posibles.
        Los índices internos van de 0 a 14; las etiquetas visibles son C01 a C15.
    '''),
    code(extraer_funciones(core, ['matriz_distancias', 'longitud', 'vecino_intercambio']) +
         '\n\nD = matriz_distancias(coordenadas)\n'
         'assert D.shape == (15, 15) and np.allclose(D, D.T)\n'
         "pd.DataFrame(D, index=ciudades, columns=ciudades).to_csv(SALIDA / 'distancias.csv')"),
    md(r'''
        La diferencia para **minimizar** es $\Delta=L(v_n)-L(v_c)$.
        Se combinan la logística de las láminas 27–29 y el pseudocódigo de la 30:
        si $\Delta<0$, la mejora se acepta siempre. En otro caso se acepta cuando
        $u<p$, con $u$ uniforme entre 0 y 1, y
        $$p=\frac{1}{1+e^{\Delta/T}}.$$

        Con $\Delta=0$, $p=0.5$. Para una ruta peor, $\Delta>0$ y $p<0.5$;
        al bajar la temperatura disminuye esa aceptación. Por ejemplo, cambiar
        107 por 120 con $T=10$ da $p\approx0.214165$.
        La implementación usa la expresión equivalente
        $a=e^{-\Delta/T}$, $p=a/(1+a)$ para evitar desbordamientos numéricos.
    '''),
    code(extraer_funciones(core, ['probabilidad_aceptar']) +
         '\n\nassert probabilidad_aceptar(-13, 10) == 1.0\n'
         'assert probabilidad_aceptar(0, 10) == 0.5\n'
         "print('p para empeorar de 107 a 120, T=10:', probabilidad_aceptar(13, 10))"),
    md('''
        Se comienza con T = 100, se proponen 100 intercambios por temperatura y
        luego se enfría un 1 %: T nueva = 0.99 × T. El proceso termina cuando
        T < 0.01. Se guarda la mejor ruta por separado de la ruta actual:
        aceptar temporalmente un empeoramiento permite explorar sin perder
        la mejor solución ya encontrada. No se utiliza el óptimo de referencia
        para decidir vecinos, aceptar propuestas o detener la búsqueda.
    '''),
    code(extraer_funciones(core, ['templado_simulado'])),
    md('''
        Ejecutamos 20 corridas con semillas 0 a 19 y el mismo calendario. La
        corrida principal es la semilla 0, fijada antes de observar resultados.
        Los contadores comprueban que se aceptaron rutas peores durante la búsqueda.
    '''),
    code('''
        corridas = []
        for semilla in range(20):
            corrida = templado_simulado(D, semilla=semilla)
            corridas.append(corrida)
            print(f'Semilla {semilla:02d}: {corrida["mejor_costo"]:.6f}')

        principal = corridas[0]
        mejora = 100 * (principal['costo_inicial'] - principal['mejor_costo']) / principal['costo_inicial']
        display(pd.DataFrame([{
            'Semilla': 0,
            'Distancia inicial': principal['costo_inicial'],
            'Mejor distancia': principal['mejor_costo'],
            'Reducción (%)': mejora,
            'Vecinos propuestos': principal['propuestas'],
            'Empeoramientos aceptados': principal['empeoramientos_aceptados'],
        }]).round(6))
    '''),
    md('''
        Primero se comparan la ruta inicial y la mejor ruta de la corrida
        principal. Los segmentos cierran el ciclo. Después se muestra la
        evolución de la distancia actual, de la mejor encontrada y de la
        temperatura; el historial se registra cada 100 propuestas.
    '''),
    code('''
        fig, ejes = plt.subplots(1, 2, figsize=(12, 5))
        for eje, ruta, titulo in zip(ejes,
                [principal['ruta_inicial'], principal['mejor_ruta']],
                ['Ruta inicial', 'Mejor ruta por Templado Simulado']):
            ciclo = ruta + ruta[:1]
            eje.plot(coordenadas[ciclo, 0], coordenadas[ciclo, 1], '-o', color='#17677b')
            for nombre, (x, y) in zip(ciudades, coordenadas):
                eje.annotate(nombre, (x, y), xytext=(4, 4), textcoords='offset points', fontsize=8)
            eje.set_title(f'{titulo}: {longitud(ruta, D.tolist()):.6f} u')
            eje.set(xlabel='x', ylabel='y')
            eje.set_aspect('equal'); eje.margins(0.13); eje.grid(alpha=0.2)
        fig.tight_layout()
        fig.savefig(SALIDA / 'rutas.png', dpi=150)
        plt.show()

        historial = pd.DataFrame(principal['historial'])
        fig, ejes = plt.subplots(1, 2, figsize=(12, 4))
        ejes[0].plot(historial.iteracion, historial.costo_actual, color='#9ca3af', label='Actual')
        ejes[0].plot(historial.iteracion, historial.mejor_costo, color='#17677b', label='Mejor')
        ejes[0].set(xlabel='Propuestas', ylabel='Distancia (u)'); ejes[0].legend()
        ejes[1].semilogy(historial.iteracion, historial.temperatura, color='#b44c20')
        ejes[1].set(xlabel='Propuestas', ylabel='Temperatura (escala logarítmica)')
        for eje in ejes:
            eje.grid(alpha=0.2)
        fig.tight_layout()
        fig.savefig(SALIDA / 'convergencia.png', dpi=150)
        plt.show()
        historial.to_csv(SALIDA / 'historial_semilla0.csv', index=False)
    '''),
    md('''
        Como comprobación adicional, calculamos el óptimo de esta instancia con
        programación dinámica Held–Karp. Este cálculo se realiza después del
        templado y no forma parte de su búsqueda. La celda plegada contiene el
        método exacto; se contrasta con las 120 permutaciones de una subinstancia
        de seis ciudades antes de usarlo con las quince.
    '''),
    code('# @title Comprobación exacta adicional: Held–Karp\n'
         'from array import array\nfrom itertools import permutations\n\n' +
         extraer_funciones(exact, ['costo_ciclo', 'canonicalizar', 'held_karp', 'verificar_con_fuerza_bruta']),
         cellView='form', jupyter={'source_hidden': True}),
    code('''
        comprobacion_6 = verificar_con_fuerza_bruta(D.tolist())
        assert comprobacion_6['coinciden']
        exacto = held_karp(D.tolist())
        optimo = exacto['costo_optimo']
        coinciden = [math.isclose(c['mejor_costo'], optimo, rel_tol=0, abs_tol=1e-8) for c in corridas]
        resumen = pd.DataFrame([{
            'semilla': c['semilla'], 'costo_inicial': c['costo_inicial'],
            'mejor_costo': c['mejor_costo'],
            'brecha_porcentaje': max(0, c['mejor_costo'] - optimo) / optimo * 100,
        } for c in corridas])
        display(resumen.round(6))
        ruta = canonicalizar(principal['mejor_ruta'])
        print('Óptimo exacto:', f'{optimo:.12f}', 'unidades')
        print('Coincidencias con el óptimo:', sum(coinciden), '/', len(corridas))
        print('Mejor ciclo:', ' → '.join(ciudades[i] for i in ruta))
        resumen.to_csv(SALIDA / 'corridas.csv', index=False)
        (SALIDA / 'optimo_exacto.json').write_text(json.dumps(exacto, indent=2), encoding='utf-8')
    '''),
    md('''
        La siguiente conclusión se obtiene de los resultados de esta ejecución.
        Alcanzar el óptimo en esta instancia y estas semillas no garantiza que
        el templado lo encuentre siempre con cualquier dato o configuración.
    '''),
    code('''
        conclusion = (
            f'La corrida principal redujo la distancia de {principal["costo_inicial"]:.6f} '
            f'a {principal["mejor_costo"]:.6f} unidades ({mejora:.2f} %). '
            f'Se propusieron {principal["propuestas"]:,} intercambios y se aceptaron '
            f'{principal["empeoramientos_aceptados"]:,} empeoramientos durante la exploración. '
            f'{sum(coinciden)} de las {len(corridas)} corridas coincidieron con el óptimo '
            f'de referencia, con tolerancia absoluta de 1e-8 unidades.'
        )
        display(Markdown(conclusion))
        (SALIDA / 'conclusion.txt').write_text(conclusion, encoding='utf-8')
    '''),
    md('''
        Los archivos de `resultados_tsp` se pueden descargar desde **Archivos**
        en Colab. La ruta conserva las 15 ciudades y cierra en su origen.

        Fuentes: presentación 8 de la clase, láminas 27–32;
        [regla de aceptación de MathWorks](https://www.mathworks.com/help/gads/how-simulated-annealing-works.html);
        [Held y Karp: programación dinámica para secuenciación y TSP](https://research.ibm.com/publications/a-dynamic-programming-approach-to-sequencing-problems).
    '''),
]
for cell in cells:
    if cell.cell_type == 'markdown':
        cell.source = cell.source.replace(chr(92) * 2, chr(92))
nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python'},
    'colab': {'name': TARGET.name, 'provenance': []},
})
nbf.write(nb, TARGET)
print('Notebook creado; comenzando ejecución real.', flush=True)

jupyter_path = ROOT / '.jupyter'
kernel = jupyter_path / 'kernels' / 'tsp-local'
kernel.mkdir(parents=True, exist_ok=True)
(kernel / 'kernel.json').write_text(json.dumps({
    'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
    'display_name': 'TSP local', 'language': 'python',
}), encoding='utf-8')
os.environ['JUPYTER_PATH'] = str(jupyter_path)
os.environ['JUPYTER_RUNTIME_DIR'] = str(jupyter_path / 'runtime')
os.environ['IPYTHONDIR'] = str(ROOT / '.ipython')
os.environ['PYTHONIOENCODING'] = 'utf-8'


def finished(cell, cell_index, **kwargs):
    nbf.write(nb, TARGET)
    if cell.cell_type == 'code':
        print(f'Celda {cell_index + 1} completada.', flush=True)


try:
    NotebookClient(nb, timeout=300, kernel_name='tsp-local',
        resources={'metadata': {'path': str(OUT)}}, on_cell_executed=finished).execute()
finally:
    nbf.write(nb, TARGET)
nbf.validate(nb)
assert not [o for c in nb.cells for o in c.get('outputs', []) if o.output_type == 'error']
print('Colab ejecutado completo y guardado.', flush=True)

"""Construye y ejecuta un Colab autocontenido: datos, métodos y 160 corridas reales."""
from pathlib import Path
import ast
import json
import os
import sys
import textwrap

import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'entrega'
OUT.mkdir(exist_ok=True)
TARGET = OUT / 'Tarea_6_TSP_Busqueda_Tabu.ipynb'


def funciones(archivo, nombres):
    texto = (ROOT / archivo).read_text(encoding='utf-8')
    nodos = {n.name: ast.get_source_segment(texto, n) for n in ast.parse(texto).body
             if isinstance(n, ast.FunctionDef)}
    return '\n\n\n'.join(nodos[nombre] for nombre in nombres)


def md(texto):
    return nbf.v4.new_markdown_cell(textwrap.dedent(texto).strip())


def code(texto, **metadata):
    return nbf.v4.new_code_cell(textwrap.dedent(texto).strip(), metadata=metadata)


datos = {p.name: p.read_text(encoding='utf-8') for p in sorted((ROOT / 'datos').glob('*'))
         if p.suffix in {'.csv', '.json'}}
original = json.loads((ROOT / 'resultados/experimento.json').read_text(encoding='utf-8'))
costos_referencia = {f"{r['n']}_{r['semilla']}_{r['algoritmo']}": r['mejor_costo']
                     for r in original['corridas']}

cells = [
    md(r'''
        # Tarea 6: búsqueda tabú para el TSP

        Se implementa la variante **basada en lo reciente**, de la presentación
        9, y se compara con el templado simulado de la Tarea 5. Se usan 10, 15,
        30 y 50 ciudades, con 20 rutas iniciales por tamaño.

        Este archivo conserva una ejecución completa. Se puede abrir en Google
        Colab y usar **Entorno de ejecución → Ejecutar todas**, con CPU. No
        necesita Drive, credenciales ni archivos externos: incluye coordenadas,
        algoritmos, referencia exacta y comparación. Se ejecutan de nuevo las
        160 corridas; el tiempo depende del equipo. El informe Word/PDF usa los
        tiempos de la primera ejecución local, guardada en el paquete; los
        tiempos mostrados aquí corresponden a esta ejecución del notebook.
    '''),
    code('''
        from pathlib import Path
        from itertools import combinations, permutations
        from array import array
        import contextlib
        import math
        import random
        import time
        import json
        import platform
        import sys
        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        from IPython.display import display, Markdown

        CARPETA = Path('tarea6_resultados')
        (CARPETA / 'datos').mkdir(parents=True, exist_ok=True)
        (CARPETA / 'resultados').mkdir(exist_ok=True)
        plt.rcParams.update({'figure.dpi': 110, 'font.size': 10,
                             'axes.spines.top': False, 'axes.spines.right': False})
        print('Python:', platform.python_version(), '| NumPy:', np.__version__, '| pandas:', pd.__version__)
    '''),
    md(r'''
        ## Datos y formulación

        Las ciudades son puntos sintéticos, en unidades del plano, no municipios
        ni kilómetros. Se generaron 50 pares enteros con
        `np.random.default_rng(42).integers(0,101,(50,2))`. Cada instancia es un
        prefijo de ese conjunto; las primeras 15 ciudades son exactamente las
        usadas en la Tarea 5. Las coordenadas se conservan explícitamente abajo
        para no depender de cambios de un generador entre versiones.

        Una solución es una permutación $v$ de las $n$ ciudades. Su costo es
        $L(v)=\sum_{k=0}^{n-1}d(v_k,v_{(k+1)\bmod n})$, incluida la vuelta al
        origen. Se minimiza usando distancias euclidianas sin redondear.
        Un vecino intercambia dos posiciones; hay $n(n-1)/2$ posibles.
    '''),
    code('archivos_datos = ' + repr(datos) + '\n'
         'for nombre, contenido in archivos_datos.items():\n'
         "    (CARPETA / 'datos' / nombre).write_text(contenido, encoding='utf-8')\n"
         "coordenadas = pd.read_csv(CARPETA / 'datos/ciudades_50.csv')[['x', 'y']].to_numpy()\n"
         'assert np.array_equal(coordenadas, np.random.default_rng(42).integers(0, 101, (50, 2)))\n'
         "display(pd.read_csv(CARPETA / 'datos/ciudades_15.csv'))"),
    code(funciones('templado_base.py', ['matriz_distancias', 'longitud', 'vecino_intercambio']) + '''

D15 = matriz_distancias(coordenadas[:15])
assert np.allclose(D15, D15.T) and np.allclose(np.diag(D15), 0)
display(pd.DataFrame({'ciudades': [10, 15, 30, 50],
                      'vecinos_por_barrido': [n*(n-1)//2 for n in [10, 15, 30, 50]]}))
'''),
    md(r'''
        ## Memoria tabú basada en lo reciente

        La memoria registra el par **no ordenado de identidades de ciudades**
        intercambiadas, no los índices que ocupaban. Si el movimiento se acepta
        en la iteración $k$, queda prohibido en $k+1,\ldots,k+5$, y vuelve a ser
        admisible en $k+6$. El horizonte es cinco en todos los tamaños.

        En cada barrido se elige el vecino admisible de menor costo, aunque sea
        peor que el estado actual; el mejor global se conserva aparte. Se añade
        una regla de aspiración: un movimiento tabú se admite si mejora el mejor
        global existente **antes de iniciar el barrido**, con tolerancia $10^{-12}$.
        El desempate se resuelve por orden del par de ciudades.

        Al quedar menos evaluaciones que vecinos, se evalúa un subconjunto
        uniforme sin reemplazo, con generador independiente y semilla fija.
        Así cada corrida consume exactamente 91 700 evaluaciones, incluidas las
        de candidatos tabú que se necesitan para verificar la aspiración.
    '''),
    code('EPS = 1e-12\n\n' + funciones('tabu_tsp.py',
         ['atributo_intercambio', 'admision', 'busqueda_tabu'])),
    md('''
        Estas comprobaciones detectan un posible desfase del horizonte, verifican
        la aspiración y la identidad del movimiento inverso, y usan un cuadrado
        de cuatro ciudades cuyo ciclo mínimo mide cuatro unidades. También
        comprueban un presupuesto que termina con un barrido parcial.
    '''),
    code(funciones('tabu_tsp.py', ['verificar_tabu']).replace(
         '    from templado_base import matriz_distancias\n', '') +
         "\n\nverificar_tabu()\nprint('Comprobaciones de memoria, aspiración, ciclo y presupuesto: correctas.')"),
    md(r'''
        ## Templado simulado de referencia

        Se conserva el algoritmo de la Tarea 5 y sus parámetros, incluida su
        aceptación logística. Para $\Delta=L(v_n)-L(v_c)$ se acepta siempre una
        mejora estricta; en otro caso se acepta con
        $p=1/(1+\exp(\Delta/T))$. Los empates tienen probabilidad $1/2$.

        $T_0=100$, $T_{\min}=0.01$, $\alpha=0.99$ y 100 propuestas por
        temperatura producen 917 niveles y 91 700 evaluaciones. Ambos métodos
        usan la misma función que suma las $n$ aristas del ciclo completo. En
        tabú una iteración examina muchos vecinos; en templado se propone uno.
        Igualar iteraciones no igualaría el trabajo de evaluación.
    '''),
    code(funciones('templado_base.py', ['probabilidad_aceptar', 'templado_simulado'])),
    md(r'''
        ## Referencia exacta y diseño del experimento

        Held–Karp calcula el óptimo de 10 y 15 ciudades mediante programación
        dinámica. Se contrasta con fuerza bruta sobre seis ciudades antes de
        usarlo. Su costo exponencial es la razón para limitar esta comprobación
        a los tamaños pequeños; **no se conoce el óptimo de 30 y 50 en esta entrega**.

        Se usan semillas 0 a 19. Cada pareja comienza con la misma permutación
        y el mismo costo, y se alterna el orden de los métodos para repartir
        efectos temporales del equipo. La medición cubre el ciclo de búsqueda,
        después de preparar la matriz y el estado inicial. Los tiempos incluyen
        la instrumentación de cada método, y no representan una garantía de
        velocidad para otras implementaciones.
    '''),
    code('# @title Referencia exacta independiente\n' +
         funciones('referencia_exacta.py', ['costo_ciclo', 'canonicalizar', 'held_karp',
                                           'verificar_con_fuerza_bruta']) +
         "\n\nassert verificar_con_fuerza_bruta(D15.tolist())['coinciden']",
         cellView='form', jupyter={'source_hidden': True}),
    code('TAMANOS = [10, 15, 30, 50]\nSEMILLAS = list(range(20))\nPRESUPUESTO = 91700\n\n' +
         funciones('experimento.py', ['resumir', 'ejecutar'])),
    code('''
        print('Ejecutando 160 corridas secuenciales: 4 tamaños × 20 semillas × 2 métodos...')
        with (CARPETA / 'resultados/ejecucion.log').open('w', encoding='utf-8') as log:
            with contextlib.redirect_stdout(log):
                resultado = ejecutar(CARPETA)
        assert len(resultado['corridas']) == 160
        print('Ejecución completa: 160 corridas y 80 parejas. Todas con 91 700 evaluaciones.')
        print('Las 20 corridas de templado para 15 ciudades reprodujeron los costos de Tarea 5.')
    '''),
    code('costos_primera_ejecucion = ' + repr(costos_referencia) + '\n'
         'for corrida in resultado["corridas"]:\n'
         '    clave = f"{corrida[\'n\']}_{corrida[\'semilla\']}_{corrida[\'algoritmo\']}"\n'
         '    assert math.isclose(corrida["mejor_costo"], costos_primera_ejecucion[clave], rel_tol=0, abs_tol=1e-8)\n'
         "print('Reproducción verificada: los 160 mejores costos coinciden con la primera ejecución local.')"),
    md('''
        ## Resultados agregados

        Cada valor de costo corresponde al **mejor ciclo conservado** por la
        corrida, no necesariamente al último estado visitado. Se informa la
        media y desviación estándar muestral de esos 20 costos, así como mínimo
        y máximo. Para tiempo se usa mediana y cuartiles. Las columnas de óptimo
        quedan vacías en los tamaños donde no se calculó una referencia exacta.
    '''),
    code('''
        corridas = pd.DataFrame(resultado['corridas'])
        resumen = pd.DataFrame(resultado['resumen'])
        comparaciones = pd.DataFrame(resultado['comparaciones_emparejadas'])
        display(resumen[['n', 'algoritmo', 'costo_medio', 'desviacion_costos',
                         'mejor_costo', 'peor_costo', 'aciertos_optimo']].round(6))
        display(resumen[['n', 'algoritmo', 'tiempo_mediano_s', 'tiempo_q1_s',
                         'tiempo_q3_s', 'movimientos_medios']].round(4))
        display(comparaciones.round(4))
        print('Diferencia porcentual pareada: 100*(costo_tabú - costo_templado)/costo_templado.')
        print('Un valor positivo indica mayor longitud con tabú en esa comparación.')
    '''),
    md('''
        La gráfica de evolución compara **evaluaciones de vecinos**, no
        iteraciones. Cada punto de tabú se registra al terminar un barrido y
        seleccionar el movimiento. Se muestran las corridas con semilla cero;
        la distribución de las 20 semillas se presenta después.
    '''),
    code('''
        colores = {'Templado': '#16485B', 'Tabu': '#B95722'}
        fig, axes = plt.subplots(2, 2, figsize=(11, 7))
        for ax, n in zip(axes.flat, TAMANOS):
            for algoritmo in ['Templado', 'Tabu']:
                h = pd.DataFrame(resultado['historiales_semilla0'][f'{n}_{algoritmo}'])
                ax.step(h.evaluaciones, h.mejor_costo, where='post',
                        color=colores[algoritmo], label=algoritmo, linewidth=1.3)
            if str(n) in resultado['optimos']:
                ax.axhline(resultado['optimos'][str(n)]['costo_optimo'], color='#777777',
                           linestyle=':', linewidth=1, label='Óptimo exacto')
            ax.set(title=f'{n} ciudades · semilla 0', xlabel='Evaluaciones', ylabel='Mejor longitud')
            ax.grid(alpha=.2)
            ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(CARPETA / 'resultados/convergencia.png', dpi=140)
        plt.show()
    '''),
    code('''
        fig, axes = plt.subplots(1, 4, figsize=(12, 3.8))
        for ax, n in zip(axes, TAMANOS):
            grupos = [corridas[(corridas.n == n) & (corridas.algoritmo == a)].mejor_costo.to_numpy()
                      for a in ['Templado', 'Tabu']]
            # El argumento labels conserva compatibilidad con Matplotlib de Colab.
            ax.boxplot(grupos, positions=[1, 2], widths=.45)
            ax.set_xticks([1, 2], ['Templado', 'Tabú'])
            for x, grupo in zip([1, 2], grupos):
                desplazamiento = np.linspace(-.13, .13, len(grupo))
                ax.scatter(x + desplazamiento, grupo, s=13,
                           color=colores['Templado' if x == 1 else 'Tabu'], alpha=.7)
            ax.set(title=f'{n} ciudades', ylabel='Mejor longitud de cada corrida')
            ax.grid(axis='y', alpha=.2)
        fig.tight_layout()
        fig.savefig(CARPETA / 'resultados/distribucion.png', dpi=140)
        plt.show()
    '''),
    md('''
        ## Comparación directa con Tarea 5: 15 ciudades

        La siguiente traza muestra los primeros movimientos de tabú de la
        semilla cero. Los índices internos se convierten aquí a etiquetas C01,
        C02, etc. Una marca aceptada en k vence al terminar k+5.
    '''),
    code('''
        r15 = corridas[(corridas.n == 15) & (corridas.semilla == 0)].set_index('algoritmo')
        fig, axes = plt.subplots(1, 3, figsize=(12, 4.3), sharex=True, sharey=True)
        puntos = coordenadas[:15]
        rutas = [r15.loc['Templado', 'ruta_inicial'], r15.loc['Templado', 'mejor_ruta'],
                 r15.loc['Tabu', 'mejor_ruta']]
        costos = [r15.loc['Templado', 'costo_inicial'], r15.loc['Templado', 'mejor_costo'],
                  r15.loc['Tabu', 'mejor_costo']]
        for ax, ruta, costo, titulo in zip(axes, rutas, costos, ['Inicial', 'Templado', 'Tabú']):
            cerrada = ruta + ruta[:1]
            ax.plot(puntos[cerrada, 0], puntos[cerrada, 1], linewidth=1, color='#16485B')
            ax.scatter(puntos[:, 0], puntos[:, 1], s=17, color='#B95722', zorder=3)
            for i, (x, y) in enumerate(puntos):
                ax.annotate(f'{i+1}', (x, y), xytext=(3, 3), textcoords='offset points', fontsize=7)
            ax.set(title=f'{titulo}: {costo:.6f}', xlabel='x', ylabel='y', aspect='equal')
            ax.grid(alpha=.15)
        fig.tight_layout()
        fig.savefig(CARPETA / 'resultados/rutas_15.png', dpi=140)
        plt.show()
        traza = pd.DataFrame(resultado['trazas_tabu']['15'])
        traza['ciudades'] = traza.ciudades_intercambiadas_base0.map(
            lambda par: ' ↔ '.join(f'C{i+1:02d}' for i in par))
        display(traza[['iteracion', 'ciudades', 'tabu_hasta_inclusive', 'aspiracion',
                       'costo_actual', 'mejor_costo']].round(6))
        display(corridas[corridas.n == 15][['semilla', 'algoritmo', 'mejor_costo', 'segundos']]
                .pivot(index='semilla', columns='algoritmo').round(6))
    '''),
    code('''
        s15 = resumen[resumen.n == 15].set_index('algoritmo')
        c30 = comparaciones.set_index('n').loc[30]
        c50 = comparaciones.set_index('n').loc[50]
        conclusion = (
            f"En 15 ciudades, templado alcanzó el óptimo en {int(s15.loc['Templado', 'aciertos_optimo'])}/20 "
            f"corridas y tabú en {int(s15.loc['Tabu', 'aciertos_optimo'])}/20. "
            f"Para 30 ciudades, templado produjo menor costo en {int(c30.templado_mejor)} de 20 parejas; "
            f"para 50, en {int(c50.templado_mejor)} de 20. "
            'Con horizonte cinco y este presupuesto, el templado fue más consistente en calidad al crecer '
            'la instancia. Tabú tuvo menor tiempo mediano en esta implementación. '
            'Al evaluar el vecindario completo, tabú sólo pudo elegir 2038, 874, 211 y 75 movimientos '
            'para 10, 15, 30 y 50 ciudades; el templado propuso 91 700 vecinos en cada tamaño.'
        )
        display(Markdown(conclusion))
        (CARPETA / 'resultados/conclusion.txt').write_text(conclusion, encoding='utf-8')
    '''),
    md('''
        ## Alcance y archivos

        Se estudia **una instancia por tamaño**, con 20 rutas iniciales. Son
        instancias anidadas, no 20 mapas independientes. Estos resultados
        describen sensibilidad al arranque y a esta configuración; no prueban
        superioridad general ni que el número de ciudades sea la única causa.
        El horizonte fijo cinco tiene distinto peso relativo en cada tamaño.
        La memoria por pares reduce repeticiones recientes de movimientos,
        pero no garantiza evitar todos los ciclos de rutas completas.

        La búsqueda tabú conserva el mejor ciclo visto aunque el estado final
        empeore. El valor mínimo observado para 30 o 50 ciudades se denomina
        **mejor encontrado**, no óptimo. Los tiempos variarán al ejecutar en Colab.

        Los CSV, JSON, trazas y figuras quedan en `tarea6_resultados/resultados`.
        El ZIP generado abajo se puede descargar desde el panel **Archivos**.

        Fuentes: presentación 9 de la clase, *Heurísticas modernas*, y Tarea 5
        previamente ejecutada;
        [Glover (1989), Tabu Search—Part I](https://leeds-faculty.colorado.edu/glover/TS%20-%20Part%20I-ORSA-aw.pdf),
        DOI 10.1287/ijoc.1.3.190;
        [MathWorks: regla de aceptación del templado](https://www.mathworks.com/help/gads/how-simulated-annealing-works.html);
        [Held y Karp: referencia de programación dinámica](https://research.ibm.com/publications/a-dynamic-programming-approach-to-sequencing-problems).
    '''),
    code('''
        import zipfile
        archivo_zip = Path('Resultados_Tarea_6.zip')
        with zipfile.ZipFile(archivo_zip, 'w', zipfile.ZIP_DEFLATED) as paquete:
            for archivo in sorted(CARPETA.rglob('*')):
                if archivo.is_file():
                    paquete.write(archivo, archivo.relative_to(CARPETA.parent))
        print('Resultados guardados en:', archivo_zip)
    '''),
]

nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python'},
    'colab': {'name': TARGET.name, 'provenance': []},
})
nbf.write(nb, TARGET)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print('Colab creado; iniciando ejecución real de todas las celdas.', flush=True)
    jupyter_path = ROOT / '.jupyter'
    kernel = jupyter_path / 'kernels/tsp-tabu-local'
    kernel.mkdir(parents=True, exist_ok=True)
    (kernel / 'kernel.json').write_text(json.dumps({
        'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
        'display_name': 'TSP Tabú local', 'language': 'python',
    }), encoding='utf-8')
    os.environ['JUPYTER_PATH'] = str(jupyter_path)
    os.environ['JUPYTER_RUNTIME_DIR'] = str(jupyter_path / 'runtime')
    os.environ['IPYTHONDIR'] = str(ROOT / '.ipython')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

    def terminada(cell, cell_index, **kwargs):
        nbf.write(nb, TARGET)
        if cell.cell_type == 'code':
            print(f'Celda {cell_index + 1} completada.', flush=True)

    try:
        NotebookClient(nb, timeout=600, kernel_name='tsp-tabu-local',
                       resources={'metadata': {'path': str(OUT)}},
                       on_cell_executed=terminada).execute()
    finally:
        nbf.write(nb, TARGET)
    nbf.validate(nb)
    assert all(c.execution_count is not None for c in nb.cells if c.cell_type == 'code')
    assert not [o for c in nb.cells for o in c.get('outputs', []) if o.output_type == 'error']
    print('Colab ejecutado y verificado sin errores.', flush=True)

"""Genera el informe Word/PDF de la Tarea 6 a partir de las corridas guardadas."""
from pathlib import Path
from xml.sax.saxutils import escape
import json
import math
import sys

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.platypus import Spacer, PageBreak, Image as PDFImage, Preformatted, KeepTogether

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'entrega'
RESULTS = ROOT / 'resultados'
OUT.mkdir(exist_ok=True)
R = json.loads((RESULTS / 'experimento.json').read_text(encoding='utf-8'))
DF = pd.DataFrame(R['corridas'])
SUMMARY = {(x['n'], x['algoritmo']): x for x in R['resumen']}
NAVY, ORANGE = '#16485B', '#B95722'
COLORS = {'Templado': NAVY, 'Tabu': ORANGE}
LABELS = {'Templado': 'Templado simulado', 'Tabu': 'Búsqueda tabú'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
                     'axes.spines.top': False, 'axes.spines.right': False})

assert len(DF) == 160 and DF.evaluaciones.eq(91700).all()
assert DF.groupby(['n', 'algoritmo']).size().eq(20).all()
for n in [10, 15, 30, 50]:
    points = pd.read_csv(ROOT / 'datos' / f'ciudades_{n}.csv')[['x', 'y']].to_numpy()
    d = np.linalg.norm(points[:, None] - points[None, :], axis=2)
    for row in R['corridas']:
        if row['n'] != n:
            continue
        route = row['mejor_ruta']
        assert sorted(route) == list(range(n))
        cost = sum(d[a, b] for a, b in zip(route, route[1:] + route[:1]))
        assert math.isclose(cost, row['mejor_costo'], rel_tol=0, abs_tol=1e-8)

# Distribuciones: se conservan los veinte puntos, incluso cuando coinciden.
fig, axes = plt.subplots(1, 4, figsize=(9, 3.2))
for ax, n in zip(axes, [10, 15, 30, 50]):
    for pos, alg in enumerate(['Templado', 'Tabu']):
        values = DF[(DF.n == n) & (DF.algoritmo == alg)].mejor_costo.to_numpy()
        jitter = np.linspace(-.12, .12, len(values))
        ax.scatter(pos + jitter, values, s=13, alpha=.65, color=COLORS[alg], zorder=2)
        ax.plot([pos-.23, pos+.23], [values.mean()]*2, color=COLORS[alg], lw=2.2)
    if str(n) in R['optimos']:
        ax.axhline(R['optimos'][str(n)]['costo_optimo'], ls='--', color='#6F7D83', lw=.8)
    ax.set_xticks([0, 1], ['Templado', 'Tabú'], fontsize=8)
    ax.set_title(f'{n} ciudades')
    ax.grid(axis='y', alpha=.18)
axes[0].set_ylabel('Mejor longitud de cada corrida')
fig.suptitle('Veinte semillas por algoritmo y tamaño; línea horizontal = media', fontsize=10)
fig.tight_layout(rect=(0, 0, 1, .94))
fig.savefig(RESULTS / 'costos_por_tamano.png', dpi=180, facecolor='white')
plt.close(fig)

coords = pd.read_csv(ROOT / 'datos/ciudades_15.csv')[['x', 'y']].to_numpy()
fig, axes = plt.subplots(1, 2, figsize=(9, 3.35), sharex=True, sharey=True)
for ax, alg in zip(axes, ['Templado', 'Tabu']):
    row = next(x for x in R['corridas'] if x['n'] == 15 and x['semilla'] == 0 and x['algoritmo'] == alg)
    route = row['mejor_ruta'] + row['mejor_ruta'][:1]
    ax.plot(coords[route, 0], coords[route, 1], color=COLORS[alg], lw=1.15)
    ax.scatter(coords[:, 0], coords[:, 1], s=19, color=COLORS[alg], zorder=3)
    for i, (x, y) in enumerate(coords):
        ax.annotate(str(i+1), (x, y), xytext=(3, 4), textcoords='offset points', fontsize=7)
    ax.set(xlabel='x', ylabel='y', xlim=(-2, 104), ylim=(-2, 108), aspect='equal')
    ax.set_title(f'{LABELS[alg]} · semilla 0\nL = {row["mejor_costo"]:.6f}', fontsize=10)
    ax.grid(alpha=.15)
fig.tight_layout(pad=.6)
fig.savefig(RESULTS / 'rutas_15.png', dpi=180, facecolor='white')
plt.close(fig)

fig, ax = plt.subplots(figsize=(9, 2.25))
for alg in ['Templado', 'Tabu']:
    h = R['historiales_semilla0'][f'15_{alg}']
    ax.step([x['evaluaciones'] for x in h], [x['mejor_costo'] for x in h],
            where='post', label=LABELS[alg], color=COLORS[alg], lw=1.3)
ax.axhline(R['optimos']['15']['costo_optimo'], color='#6F7D83', lw=.8, ls='--', label='Óptimo exacto')
ax.set(xlabel='Evaluaciones de vecinos', ylabel='Mejor longitud acumulada', xlim=(0, 91700))
ax.legend(fontsize=8, frameon=False, loc='upper right')
ax.grid(alpha=.15)
fig.tight_layout(pad=.6)
fig.savefig(RESULTS / 'convergencia_15.png', dpi=180, facecolor='white')
plt.close(fig)

blocks = []
def p(text, role='body'):
    blocks.append(('paragraph', text, role))
def heading(text):
    p(text, 'heading')
def page():
    blocks.append(('page',))
def table(headers, rows, widths):
    blocks.append(('table', headers, rows, widths))
def figure(name, width=7.05):
    blocks.append(('image', RESULTS / name, width))
def link(label, url):
    blocks.append(('reference_link', label, url))

p('Tarea 6 · Búsqueda tabú para el TSP', 'title')
p('Comparación con el templado simulado de la Tarea 5\n3 de noviembre de 2026', 'subtitle')
heading('1. Objetivo y formulación')
p('Se implementa la búsqueda tabú basada en lo reciente, según el enunciado de la presentación 9, y se analiza su comportamiento con 10, 15, 30 y 50 ciudades. La comparación principal conserva las mismas 15 ciudades y el mismo templado simulado de la Tarea 5.')
p('Cada solución es una permutación v de las n ciudades. El recorrido visita cada ciudad una vez y regresa al punto de partida. Las distancias son euclidianas en unidades de un plano sintético; no representan kilómetros entre ciudades reales. Se minimiza la longitud total, calculada sin redondear las distancias:')
p('d(i, j) = √((xᵢ − xⱼ)² + (yᵢ − yⱼ)²)\nL(v) = d(v₀, v₁) + … + d(vₙ₋₂, vₙ₋₁) + d(vₙ₋₁, v₀)', 'formula')
p('El vecindario se obtiene intercambiando dos posiciones distintas de la permutación. Tiene n(n−1)/2 movimientos: 45, 105, 435 y 1 225, respectivamente. Las rutas iniciales se generan barajando la misma lista de ciudades con una semilla explícita.')
heading('2. Memoria de recencia y aspiración')
p('Se selecciona el vecino admisible de menor costo, incluso si empeora la ruta actual. Se conserva por separado la mejor ruta global encontrada; por ello, explorar un empeoramiento no elimina la mejor solución previa.')
p('La memoria guarda el par no ordenado de identidades de las ciudades intercambiadas, no los números de sus posiciones. Si se acepta el par en la iteración k, su vencimiento es k+5: queda prohibido en k+1, …, k+5 y disponible en k+6. Esta memoria restringe intercambios recientes, pero no garantiza impedir toda repetición de una ruta completa.')
p('Como criterio adicional de aspiración se permite un movimiento tabú cuando su costo mejora estrictamente el mejor global existente antes del barrido. Se usa una tolerancia de 10⁻¹² para las comparaciones de tabú. Esta excepción se distingue de la memoria reciente que describe la presentación.')
p('En empates de costo se elige el par de ciudades de menor orden lexicográfico. Con el arranque fijado, los barridos completos son deterministas; el último barrido parcial utiliza un generador independiente con semilla fija.', 'small')

page()
heading('3. Implementación y diseño experimental')
p('Se generaron 50 pares enteros distintos con np.random.default_rng(42).integers(0, 101, (50, 2)). Cada instancia usa un prefijo de esa tabla: las primeras 10, 15, 30 o 50 filas. Las primeras 15 coinciden con la Tarea 5. Los CSV incluidos conservan las coordenadas explícitas para repetir el experimento sin depender de generar nuevos datos.')
table(['Aspecto', 'Configuración aplicada'], [
    ['Repeticiones', '20 semillas (0 a 19) × 4 tamaños × 2 métodos = 160 corridas.'],
    ['Emparejamiento', 'Misma instancia y exactamente la misma ruta inicial en ambos métodos para cada semilla.'],
    ['Presupuesto', '91 700 evaluaciones de vecinos por método y corrida. Se incluyen los vecinos tabú evaluados para comprobar aspiración.'],
    ['Tabú', 'Horizonte 5; mejor vecino admisible; vecindario completo salvo el último barrido parcial.'],
    ['Barrido final', 'Muestra uniforme sin reemplazo del número restante de pares; generador independiente del usado para iniciar la ruta.'],
    ['Templado', 'T₀ = 100; Tmín = 0.01; α = 0.99; 100 propuestas por temperatura; 917 niveles.'],
    ['Medición', 'Ejecuciones secuenciales; orden de los algoritmos alternado por semilla. Se excluyen creación de distancias, ruta inicial y verificaciones.'],
], [1.18, 5.87])
p('Se conserva el algoritmo de templado original. Para minimizar, Δ = L(vn) − L(vc): las mejoras estrictas se aceptan siempre; los demás cambios se aceptan con p = 1/(1 + exp(Δ/T)). Es la variante logística usada en la Tarea 5, no la regla exponencial de Metropolis. Ambos métodos llaman a la misma función de longitud completa de orden O(n).')
heading('Esquema de la búsqueda tabú implementada')
blocks.append(('code', 'Crear ruta inicial y guardar mejor global\nMientras queden evaluaciones:\n  Eliminar marcas vencidas\n  Evaluar intercambios (todos o muestra final)\n  Excluir tabú, salvo mejora del mejor global anterior\n  Elegir el admisible de menor costo\n  Moverse aunque empeore; marcar par hasta k+5\n  Actualizar mejor global si corresponde\nDevolver la mejor ruta, no necesariamente la última'))
p('Igualar evaluaciones no equivale a igualar movimientos ni tiempo. Tabú realiza 2 038, 874, 211 y 75 selecciones para n = 10, 15, 30 y 50; el templado realiza 91 700 propuestas y acepta sólo una parte de ellas. Los costos se evalúan con recorridos cerrados en ambos casos.', 'small')

page()
heading('4. Calidad de las soluciones')
p('La tabla resume el mejor costo encontrado en cada corrida. La desviación estándar es muestral (20 semillas). Un costo menor representa una ruta más corta. Los valores mostrados se redondean sólo para la presentación.')
quality_rows = []
for n in [10, 15, 30, 50]:
    for alg in ['Templado', 'Tabu']:
        s = SUMMARY[n, alg]
        quality_rows.append([str(n), 'Templado' if alg == 'Templado' else 'Tabú',
                             f'{s["costo_medio"]:.3f}', f'{s["desviacion_costos"]:.3f}',
                             f'{s["mejor_costo"]:.3f}', f'{s["peor_costo"]:.3f}'])
table(['n', 'Método', 'Media', 'Desv. est.', 'Mínimo', 'Máximo'], quality_rows,
      [.38, 1.17, 1.12, 1.12, 1.12, 1.12])
figure('costos_por_tamano.png')
p('Figura 1. Cada punto corresponde a una semilla; la línea gruesa indica la media. La línea discontinua marca el óptimo exacto sólo en 10 y 15 ciudades. En 30 y 50 no se ha calculado una referencia exacta.', 'small')
p('Para 10 ciudades ambos métodos alcanzaron el óptimo 268.342757 en 20/20 corridas. Para 15, el templado alcanzó 288.609288 en 20/20 y tabú en 19/20. El costo restante de tabú fue 362.848480 (semilla 3). Las referencias de 10 y 15 se calcularon por programación dinámica exacta Held–Karp, de forma independiente de las heurísticas.')
p('En 30 y 50 ciudades, las medias de tabú fueron mayores. Estos resultados describen las instancias y la configuración ensayadas; no demuestran la calidad respecto al óptimo, que se desconoce para esos tamaños.')

page()
heading('5. Tiempo y comparaciones emparejadas')
p('Los tiempos se midieron con perf_counter en el equipo de ejecución. Se informa mediana y cuartiles Q1–Q3, en segundos, para describir la variación entre las veinte corridas. Se cronometró el bucle del algoritmo, incluyendo sus decisiones y registros; no las referencias exactas ni la generación de figuras.')
time_rows = []
for n in [10, 15, 30, 50]:
    for alg in ['Templado', 'Tabu']:
        s = SUMMARY[n, alg]
        time_rows.append([str(n), 'Templado' if alg == 'Templado' else 'Tabú',
                          f'{s["tiempo_mediano_s"]:.3f}',
                          f'{s["tiempo_q1_s"]:.3f}–{s["tiempo_q3_s"]:.3f}',
                          f'{s["movimientos_medios"]:.2f}'])
table(['n', 'Método', 'Mediana (s)', 'Q1–Q3 (s)', 'Movimientos medios'], time_rows,
      [.38, 1.15, 1.2, 1.7, 1.75])
p('Tabú tardó menos en las cuatro instancias: sus medianas fueron aproximadamente 0.55, 0.57, 0.67 y 0.71 veces las del templado. El presupuesto de costo es igual, pero el templado hace más muestreos aleatorios y pruebas de aceptación. La medición compara estas implementaciones, no una garantía general de velocidad.')
paired_rows = []
for x in R['comparaciones_emparejadas']:
    paired_rows.append([str(x['n']), str(x['tabu_mejor']), str(x['empates']), str(x['templado_mejor']),
                        f'{x["diferencia_media_porcentaje_tabu_vs_templado"]:.2f}%'])
table(['n', 'Gana tabú', 'Empates', 'Gana templado', 'Diferencia media'], paired_rows,
      [.38, 1.2, 1.1, 1.6, 1.9])
p('Cada fila compara las mismas 20 semillas. “Gana” significa obtener menor longitud, con tolerancia 10⁻⁸; los empates incluyen rutas distintas con igual costo. La última columna promedia 100 × (Ltabú − Ltemplado) / Ltemplado por pareja. Un valor positivo indica mayor longitud de tabú. No es el porcentaje de diferencia entre las dos medias ni una brecha al óptimo.', 'small')
p('En 30 ciudades tabú ganó una pareja y empató otra, aunque su media fue peor. En 50, el templado obtuvo menor costo en las veinte parejas. Por tanto, menor tiempo de tabú no implicó mejor calidad bajo este presupuesto fijo.')

page()
heading('6. Comparación directa con la Tarea 5: 15 ciudades')
p('Se preservaron las coordenadas, las veinte rutas iniciales y el código del templado de la Tarea 5. Las veinte mejores longitudes del templado se reprodujeron dentro de una tolerancia 10⁻⁸. Los tiempos se midieron de nuevo en esta comparación, sin mezclarlos con mediciones históricas.')
figure('rutas_15.png')
p('Figura 2. Rutas de la semilla 0. Las etiquetas 1 a 15 representan C01 a C15. Ambos métodos encontraron una ruta óptima de longitud 288.609288 desde un inicio de longitud 631.089690: una reducción de 54.27%. Se incluye el regreso a la ciudad de inicio.', 'small')
figure('convergencia_15.png')
p('Figura 3. Mejor costo acumulado de la semilla 0 frente al presupuesto consumido. En tabú los puntos corresponden a barridos ya terminados; en templado, a niveles de temperatura terminados. Esta gráfica es una trayectoria ilustrativa, no el promedio de las veinte corridas.', 'small')
p('La comparación de las veinte semillas es más informativa que una sola trayectoria: tabú obtuvo media 292.321248, desviación 16.600388 y éxito exacto 19/20; el templado, media 288.609288 y éxito 20/20. La brecha media de tabú al óptimo fue 1.29%, explicada por la semilla 3. Se conservó la mejor ruta de cada ejecución aunque su ruta final tuviera mayor costo.')

page()
heading('7. Análisis, límites y conclusión')
p('Con este conjunto de pruebas, la búsqueda tabú de recencia fue más rápida, pero el templado entregó menor costo medio para 15, 30 y 50 ciudades. En 10 ambos coincidieron con el óptimo en todas las semillas; en 15 tabú lo alcanzó en 19 de 20. Así, el balance observado favorece al templado en calidad y a tabú en tiempo para estas implementaciones y este presupuesto.')
p('Al crecer n, el vecindario de intercambio aumenta como n(n−1)/2. Con 91 700 evaluaciones, tabú pasa de 2 038 selecciones en 10 ciudades a sólo 75 en 50. Esta reducción del número de pasos es una explicación compatible con el deterioro observado, pero el experimento no aísla su efecto de los demás parámetros.')
p('Se usó una sola instancia por tamaño y veinte rutas iniciales, por lo que las repeticiones miden sensibilidad al arranque, no variación entre mapas. Las instancias están anidadas y el horizonte se fijó en 5; su restricción relativa cambia con n. Tampoco se ajustó el enfriamiento al tamaño. No se realizaron pruebas de significación ni se afirma superioridad universal. Los tiempos dependen del equipo, las bibliotecas y el código utilizado.')
p('Un estudio posterior puede añadir mapas independientes, variar el horizonte y contrastar presupuestos de evaluaciones o de tiempo, conservando el emparejamiento. Eso permitiría distinguir el efecto del tamaño del de la configuración; no forma parte de los resultados aquí reportados.')
heading('8. Reproducción y archivos')
p('El paquete incluye tabu_tsp.py, templado_base.py, referencia_exacta.py, experimento.py, los CSV de ciudades, las 160 corridas y sus resúmenes. El Colab autocontenido ejecuta las 160 corridas con datos y funciones incluidos; genera CSV, JSON, trazas, figuras y un ZIP. Puede repetirse en CPU con “Ejecutar todas”, sin credenciales ni archivos externos. El informe se regenera desde resultados/experimento.json mediante generar_documento.py.')
blocks.append(('code', 'python -m pip install numpy pandas matplotlib python-docx reportlab\npython experimento.py\npython generar_documento.py'))
p('Entorno de las corridas: Python ' + R['versiones']['python'] + ', NumPy ' + R['versiones']['numpy'] + ' y pandas ' + R['versiones']['pandas'] + '. Este informe conserva los tiempos de la primera ejecución; el Colab mide una segunda ejecución completa y comprueba sus 160 mejores costos contra ella. Los tiempos pueden diferir al repetirlo.', 'small')
heading('Referencias')
p('Material del curso: presentación 9, “Heurísticas modernas”, archivo 9-Heuristicas-modernas.ppt; enunciado de la Tarea 6 y ejemplo de memoria reciente para TSP. Trabajo previo: Tarea 5, implementación y resultados del templado simulado incluidos como referencia.', 'reference')
link('Glover, F. (1989). Tabu Search—Part I. ORSA Journal on Computing, 1(3), 190–206. DOI: 10.1287/ijoc.1.3.190. Marco de memoria tabú y criterios de aspiración.',
     'https://leeds-faculty.colorado.edu/glover/TS%20-%20Part%20I-ORSA-aw.pdf')
link('MathWorks. How Simulated Annealing Works. Documentación de la probabilidad logística de aceptación empleada en el método de referencia.',
     'https://www.mathworks.com/help/gads/how-simulated-annealing-works.html')
link('Held, M. y Karp, R. M. A Dynamic Programming Approach to Sequencing Problems. Registro de IBM Research; fundamento de la programación dinámica usada para verificar los óptimos de 10 y 15 ciudades.',
     'https://research.ibm.com/publications/a-dynamic-programming-approach-to-sequencing-problems')

# Un mismo conjunto de bloques alimenta las dos entregas.
doc = Document()
doc.core_properties.title = 'Tarea 6 · Búsqueda tabú para el TSP'
doc.core_properties.author = ''
section = doc.sections[0]
section.page_width, section.page_height = Inches(8.5), Inches(11)
section.top_margin = section.bottom_margin = Inches(.57)
section.left_margin = section.right_margin = Inches(.65)
normal = doc.styles['Normal']
normal.font.name, normal.font.size = 'Arial', Pt(9.5)
normal.paragraph_format.line_spacing = 1.04
normal.paragraph_format.space_after = Pt(5)
normal.paragraph_format.widow_control = True
for name, size in [('Title', 18), ('Subtitle', 10.5), ('Heading 1', 12)]:
    style = doc.styles[name]
    style.font.name, style.font.size = 'Arial', Pt(size)
    style.font.color.rgb = RGBColor.from_string(NAVY[1:])
    style.paragraph_format.keep_with_next = True
    style.paragraph_format.space_before = Pt(6 if name == 'Heading 1' else 0)
    style.paragraph_format.space_after = Pt(5)
footer = section.footer.paragraphs[0]
footer.alignment = 2
footer.add_run('Tarea 6 · ')
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'PAGE')
footer._p.append(field)

def word_p(value, role='body'):
    style = {'title': 'Title', 'subtitle': 'Subtitle', 'heading': 'Heading 1'}.get(role)
    paragraph = doc.add_paragraph(value, style=style)
    if role in ('small', 'reference'):
        for run in paragraph.runs:
            run.font.size = Pt(8)
    if role == 'formula':
        paragraph.paragraph_format.keep_together = True
        for run in paragraph.runs:
            run.font.name, run.font.size = 'DejaVu Sans', Pt(9)
    return paragraph

def word_link(paragraph, url):
    rel = paragraph.part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), rel)
    run = OxmlElement('w:r')
    props = OxmlElement('w:rPr')
    color = OxmlElement('w:color'); color.set(qn('w:val'), '175F87'); props.append(color)
    size = OxmlElement('w:sz'); size.set(qn('w:val'), '15'); props.append(size)
    run.append(props)
    value = OxmlElement('w:t'); value.text = url; run.append(value)
    hyperlink.append(run); paragraph._p.append(hyperlink)

for block in blocks:
    kind = block[0]
    if kind == 'paragraph':
        word_p(block[1], block[2])
    elif kind == 'page':
        doc.add_page_break()
    elif kind == 'image':
        doc.add_picture(str(block[1]), width=Inches(block[2]))
    elif kind == 'code':
        para = doc.add_paragraph()
        para.paragraph_format.keep_together = True
        run = para.add_run(block[1]); run.font.name, run.font.size = 'Consolas', Pt(7.8)
    elif kind == 'table':
        _, headers, rows, widths = block
        t = doc.add_table(rows=1, cols=len(headers))
        t.style = 'Light Shading Accent 1'; t.autofit = False
        for cell, value in zip(t.rows[0].cells, headers):
            cell.text = value
        repeat = OxmlElement('w:tblHeader'); t.rows[0]._tr.get_or_add_trPr().append(repeat)
        for row in rows:
            for cell, value in zip(t.add_row().cells, row):
                cell.text = value
        for row in t.rows:
            no_split = OxmlElement('w:cantSplit'); row._tr.get_or_add_trPr().append(no_split)
            for i, cell in enumerate(row.cells):
                cell.width = Inches(widths[i] / sum(widths) * 7.2)
                for para in cell.paragraphs:
                    para.paragraph_format.space_before = para.paragraph_format.space_after = Pt(2)
                    for run in para.runs:
                        run.font.size = Pt(8.6)
        doc.add_paragraph().paragraph_format.space_after = Pt(0)
    elif kind == 'reference_link':
        para = word_p(block[1], 'reference')
        para.paragraph_format.keep_together = True
        para.add_run('\n'); word_link(para, block[2])
doc.save(OUT / 'Tarea_6_TSP_Busqueda_Tabu.docx')

font_dir = Path(matplotlib.get_data_path()) / 'fonts/ttf'
for name, filename in [('DVS', 'DejaVuSans.ttf'), ('DVS-Bold', 'DejaVuSans-Bold.ttf'),
                       ('DVS-Mono', 'DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
pdfmetrics.registerFontFamily('DVS', normal='DVS', bold='DVS-Bold')
styles = {
    'body': ParagraphStyle('Body', fontName='DVS', fontSize=9.1, leading=12.3, spaceAfter=6, allowWidows=0, allowOrphans=0),
    'title': ParagraphStyle('Title', fontName='DVS-Bold', fontSize=17.5, leading=22, spaceAfter=7, textColor=colors.HexColor(NAVY)),
    'subtitle': ParagraphStyle('Subtitle', fontName='DVS', fontSize=10, leading=14, spaceAfter=6),
    'small': ParagraphStyle('Small', fontName='DVS', fontSize=7.8, leading=10.4, spaceAfter=5),
    'reference': ParagraphStyle('Reference', fontName='DVS', fontSize=7.6, leading=10, spaceAfter=5),
    'heading': ParagraphStyle('Heading', fontName='DVS-Bold', fontSize=11.8, leading=16, spaceBefore=7, spaceAfter=6, keepWithNext=True, textColor=colors.HexColor(NAVY)),
    'formula': ParagraphStyle('Formula', fontName='DVS', fontSize=9.8, leading=15, leftIndent=12, spaceAfter=7),
    'cell': ParagraphStyle('Cell', fontName='DVS', fontSize=8.1, leading=10.5),
    'headcell': ParagraphStyle('HeadCell', fontName='DVS-Bold', fontSize=8, leading=10.5, textColor=colors.white),
    'code': ParagraphStyle('Code', fontName='DVS-Mono', fontSize=7.8, leading=10.2, leftIndent=8, spaceAfter=7),
}
width, height = letter
body_width = width - 1.3 * inch
story = []
for block in blocks:
    kind = block[0]
    if kind == 'paragraph':
        story.append(Paragraph(escape(block[1]).replace('\n', '<br/>'), styles[block[2]]))
    elif kind == 'page':
        story.append(PageBreak())
    elif kind == 'image':
        with Image.open(block[1]) as im:
            w, h = im.size
        target = block[2] * inch
        story.append(PDFImage(str(block[1]), width=target, height=target*h/w))
    elif kind == 'code':
        story.append(Preformatted(block[1], styles['code']))
    elif kind == 'table':
        _, headers, rows, widths = block
        data = [[Paragraph(escape(str(x)), styles['headcell']) for x in headers]]
        data += [[Paragraph(escape(str(x)), styles['cell']) for x in row] for row in rows]
        t = Table(data, colWidths=[x / sum(widths) * body_width for x in widths], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(NAVY)),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#EFF4F6'), colors.white]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LINEBELOW', (0, -1), (-1, -1), .5, colors.HexColor('#CCD7DC')),
        ]))
        story.extend([KeepTogether([t]), Spacer(1, 7)])
    elif kind == 'reference_link':
        value = escape(block[1]) + '<br/><link color="#175F87" href="' + escape(block[2]) + '">' + escape(block[2]) + '</link>'
        story.append(KeepTogether([Paragraph(value, styles['reference'])]))

def footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#D6E0E4'))
    canvas.line(.65*inch, .43*inch, width-.65*inch, .43*inch)
    canvas.setFont('DVS', 7.2); canvas.setFillColor(colors.HexColor('#52646C'))
    canvas.drawString(.65*inch, .27*inch, 'Tarea 6 · TSP con búsqueda tabú')
    canvas.drawRightString(width-.65*inch, .27*inch, str(document.page))
    canvas.restoreState()

SimpleDocTemplate(str(OUT / 'Tarea_6_TSP_Busqueda_Tabu.pdf'), pagesize=letter,
    leftMargin=.65*inch, rightMargin=.65*inch, topMargin=.55*inch, bottomMargin=.57*inch,
    title='Tarea 6 · TSP con búsqueda tabú', author='').build(story, onFirstPage=footer, onLaterPages=footer)
print('Generados Word, PDF y tres figuras a partir de las 160 corridas guardadas.')

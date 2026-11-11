"""Genera las figuras y la entrega Word/PDF de la tarea 5 con datos ya ejecutados."""
from pathlib import Path
import csv
import json
import math
import sys
from xml.sax.saxutils import escape

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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
with (ROOT / 'datos' / 'ciudades.csv').open(encoding='utf-8') as f:
    cities = list(csv.DictReader(f))
experiment = json.loads((RESULTS / 'experimento.json').read_text(encoding='utf-8'))
exact = json.loads((RESULTS / 'optimo_exacto.json').read_text(encoding='utf-8'))
main = experiment['principal']
params = experiment['parametros']
coordinates = np.array([[float(c['x']), float(c['y'])] for c in cities])
names = [c['ciudad'] for c in cities]
assert len(cities) == 15 and len(set(names)) == 15
distances = np.linalg.norm(coordinates[:, None] - coordinates[None, :], axis=2)


def length(route):
    return sum(float(distances[a, b]) for a, b in zip(route, route[1:] + route[:1]))


for route, cost in [(main['ruta_inicial'], main['costo_inicial']),
                    (main['mejor_ruta'], main['mejor_costo']),
                    (exact['permutacion_indices'], exact['costo_optimo'])]:
    assert sorted(route) == list(range(15))
    assert math.isclose(length(route), cost, rel_tol=0, abs_tol=1e-9)
reduction = 100 * (main['costo_inicial'] - main['mejor_costo']) / main['costo_inicial']
hits = sum(math.isclose(run['mejor_costo'], exact['costo_optimo'], rel_tol=0, abs_tol=1e-8)
           for run in experiment['corridas'])
assert hits == experiment['repeticiones'] == 20
assert main['semilla'] == 0 and main['propuestas'] == 91700 and main['niveles'] == 917

NAVY = '#16485B'
ORANGE = '#B95722'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False})
label_offsets = [(-16, 8), (7, -1), (4, 7), (-15, -14), (-10, -16),
                 (-13, 9), (8, -12), (-34, 8), (4, -14), (6, 4),
                 (-36, -5), (-14, 8), (7, -1), (-31, -14), (-12, 9)]

fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.25), sharex=True, sharey=True)
for ax, route, cost, title, color in zip(
        axes, [main['ruta_inicial'], main['mejor_ruta']],
        [main['costo_inicial'], main['mejor_costo']],
        ['Ruta inicial', 'Mejor ruta encontrada'], ['#87959C', NAVY]):
    closed = route + route[:1]
    ax.plot(coordinates[closed, 0], coordinates[closed, 1], color=color,
            linewidth=1.25, alpha=.9, zorder=1)
    ax.scatter(coordinates[:, 0], coordinates[:, 1], s=22, color=NAVY, zorder=3)
    for label, (x, y), offset in zip(names, coordinates, label_offsets):
        ax.annotate(label, (x, y), xytext=offset, textcoords='offset points',
                    fontsize=8.5, color='#24333B', zorder=4)
    ax.set_title(f'{title}\nLongitud = {cost:.6f}', fontsize=11, pad=9)
    ax.set(xlabel='x', xlim=(-2, 104), ylim=(-4, 112), aspect='equal')
    ax.grid(alpha=.17)
axes[0].set_ylabel('y')
fig.tight_layout(pad=.8, w_pad=1.2)
fig.savefig(RESULTS / 'rutas.png', dpi=190, facecolor='white')
plt.close(fig)

history = main['historial']
x = np.array([row['iteracion'] for row in history])
current = np.array([row['costo_actual'] for row in history])
best = np.array([row['mejor_costo'] for row in history])
temperature = np.array([row['temperatura'] for row in history])
assert np.all(np.diff(best) <= 1e-9)
fig, axes = plt.subplots(2, 1, figsize=(8.6, 4.5), sharex=True,
                         gridspec_kw={'height_ratios': [1.7, 1]})
axes[0].plot(x, current, color='#9BA5AA', linewidth=.7, label='Costo actual', alpha=.8)
axes[0].plot(x, best, color=NAVY, linewidth=1.5, label='Mejor costo acumulado')
axes[0].axhline(exact['costo_optimo'], color=ORANGE, linestyle='--', linewidth=1,
               label='Óptimo de referencia')
axes[0].set_ylabel('Longitud del ciclo')
axes[0].legend(loc='upper right', fontsize=8.1, frameon=False)
axes[0].grid(alpha=.17)
axes[1].semilogy(x, temperature, color=ORANGE, linewidth=1.5)
axes[1].axhline(params['t_minima'], color='#8D969B', linewidth=.8, linestyle='--')
axes[1].set(xlabel='Vecinos propuestos', ylabel='Temperatura T')
axes[1].grid(alpha=.17, which='both')
axes[1].ticklabel_format(axis='x', style='plain')
fig.tight_layout(pad=.7, h_pad=.9)
fig.savefig(RESULTS / 'convergencia.png', dpi=190, facecolor='white')
plt.close(fig)

# Una sola estructura de contenido se representa en ambos formatos.
blocks = []


def p(text, role='body'):
    blocks.append(('paragraph', text, role))


def table(headers, rows, widths):
    blocks.append(('table', headers, rows, widths))


def new_page():
    blocks.append(('page',))


def picture(path, width):
    blocks.append(('image', path, width))


p('Tarea 5 · TSP con Templado Simulado', 'title')
p('15 ciudades · Intercambio de dos posiciones · Minimización', 'subtitle')
p('Material: presentación 8, láminas 27–32. Fecha: 3 de noviembre de 2026.', 'small')
p('Problema y datos utilizados', 'heading')
p('Se busca un ciclo que visite las 15 ciudades exactamente una vez y regrese a la ciudad inicial, minimizando su longitud. La solución se representa mediante una permutación vc de las ciudades; la ciudad de inicio se añade únicamente al cerrar el ciclo para evaluarlo o dibujarlo. [1]')
p('Se utilizaron las 15 ciudades sintéticas autorizadas para esta práctica, identificadas como C01–C15. Sus coordenadas enteras se generaron con semilla 42 y se conservan en datos/ciudades.csv. Las longitudes se expresan en unidades del plano, no en kilómetros.')
p('d(i,j) = √[(xᵢ − xⱼ)² + (yᵢ − yⱼ)²]', 'formula')
p('L(v) = d(v₀,v₁) + … + d(v₁₃,v₁₄) + d(v₁₄,v₀)', 'formula')
p('La última suma incluye explícitamente el regreso al origen. La matriz es simétrica; se calcula con distancias euclidianas de doble precisión, sin redondearlas durante la optimización.')
coordinate_rows = []
for row in range(5):
    record = []
    for offset in (0, 5, 10):
        c = cities[row + offset]
        record += [c['ciudad'], c['x'], c['y']]
    coordinate_rows.append(record)
table(['Ciudad', 'x', 'y'] * 3, coordinate_rows, [1.0, .55, .55] * 3)
p('Parámetros reproducibles', 'heading')
table(['Parámetro', 'Valor usado'], [
    ['Temperatura inicial T₀', str(params['t_inicial'])],
    ['Umbral de parada Tmín', str(params['t_minima'])],
    ['Enfriamiento por nivel', f"T ← {params['enfriamiento']} · T (disminución del 1 %)"],
    ['Propuestas por temperatura', str(params['vecinos_por_temperatura'])],
    ['Ruta inicial de la corrida principal', 'Permutación aleatoria; semilla 0'],
    ['Repeticiones de comprobación', '20 corridas, semillas 0 a 19'],
], [2.55, 3.85])
p('La ruta inicial, los intercambios y las decisiones probabilísticas usan un generador con semilla. Repetir los mismos datos y parámetros permite reproducir el experimento.')

new_page()
p('Vecindad y regla de aceptación', 'heading')
p('En cada propuesta se eligen uniformemente dos posiciones distintas i y j de vc y se intercambian para obtener vn. La vecina conserva las 15 ciudades sin repeticiones. Hay 15 × 14 / 2 = 105 intercambios distintos posibles para una permutación; se propone sólo uno por iteración, como pide el enunciado.')
blocks.append(('code', '''i, j = rng.sample(range(15), 2)
vn = vc.copy()
vn[i], vn[j] = vn[j], vn[i]'''))
p('Para minimizar se invierte la resta del exponente de la lámina 27: se define Δ = L(vn) − L(vc). La regla completa sigue la lámina 30: una mejora estricta se acepta siempre; el resto se somete a la probabilidad logística. Esta variante también está documentada por MathWorks. [1–2]')
p('p = 1 / (1 + exp((L(vn) − L(vc)) / T))', 'formula')
table(['Situación', 'Decisión'], [
    ['Δ < 0: la vecina es mejor', 'Aceptar con probabilidad 1'],
    ['Δ = 0: igual longitud', 'Aceptar con probabilidad 0.5'],
    ['Δ > 0: la vecina es peor', 'Aceptar si u < p; u uniforme en [0,1)'],
], [2.8, 3.6])
p('Para Δ ≥ 0 se evalúa a = exp(−Δ/T) y p = a/(1+a), expresión equivalente que evita exponenciales positivas enormes cuando T es muy pequeña. La temperatura siempre permanece positiva. Al enfriarse, disminuye la posibilidad de aceptar empeoramientos.')
p('Esquema de ejecución', 'heading')
blocks.append(('code', '''vc = permutación_aleatoria(15)
actual = L(vc); mejor = vc.copy(); T = 100
mientras T >= 0.01:
    repetir 100 veces:
        vn = intercambio_aleatorio_de_dos_posiciones(vc)
        delta = L(vn) - actual
        p = 1 si delta < 0; en otro caso, logística(delta, T)
        si delta < 0 o uniforme(0,1) < p:
            vc = vn; actual = L(vn)
            si actual < L(mejor): mejor = vc.copy()
    T = 0.99 * T
devolver mejor'''))
p('Se almacena la mejor ruta por separado de la actual: aceptar temporalmente una peor permite explorar y no borra el mejor resultado. Con este calendario se realizaron 917 niveles y 91 700 propuestas; después del último nivel T = 0.009941993 < 0.01.')
example = main.get('ejemplo_intercambio')
if example:
    p(f"Ejemplo realmente observado: el primer intercambio aumentó L de {example['costo_vc']:.6f} a {example['costo_vn']:.6f}. Con T = {example['temperatura']:g}, Δ = {example['delta']:.6f}, p = {example['p']:.6f} y u = {example['u']:.6f}, se aceptó esa vecina peor porque u < p.")

new_page()
p('Resultado de la corrida principal', 'heading')
p(f"Con semilla {main['semilla']}, la longitud pasó de {main['costo_inicial']:.9f} a {main['mejor_costo']:.9f} unidades del plano. La reducción respecto a esa ruta inicial fue de {reduction:.4f} %.")
picture(RESULTS / 'rutas.png', 6.75)
p('Figura 1. Los dos dibujos incluyen la arista que cierra el recorrido. Las coordenadas y la escala son las mismas; sólo cambia el orden de visita.', 'small')
table(['Medida', 'Valor observado'], [
    ['Longitud inicial', f"{main['costo_inicial']:.9f}"],
    ['Mejor longitud', f"{main['mejor_costo']:.9f}"],
    ['Reducción', f'{reduction:.4f} %'],
    ['Niveles / vecinos propuestos', f"{main['niveles']} / {main['propuestas']:,}".replace(',', ' ')],
    ['Aceptaciones totales', str(main['aceptadas'])],
    ['Mejoras / empeoramientos aceptados', f"{main['mejoras_aceptadas']} / {main['empeoramientos_aceptados']}"],
    ['Empates aceptados', str(main['empates_aceptados'])],
    ['Óptimo de referencia Held–Karp', f"{exact['costo_optimo']:.9f}"],
], [3.8, 2.6])
rotation = main['mejor_ruta'].index(0)
canonical = main['mejor_ruta'][rotation:] + main['mejor_ruta'][:rotation]
cycle_text = ' → '.join(names[i] for i in canonical + canonical[:1])
p('Mejor ciclo, presentado desde C01:', 'subheading')
p(cycle_text, 'route')
p('Cambiar el punto de inicio de la escritura conserva el mismo ciclo y la misma longitud. El algoritmo permite intercambiar cualquier par de posiciones; no fija C01 durante la búsqueda.', 'small')

new_page()
p('Convergencia y verificación del resultado', 'heading')
picture(RESULTS / 'convergencia.png', 6.75)
p('Figura 2. Valores registrados al terminar cada nivel. El costo actual puede subir por las aceptaciones probabilísticas; el mejor acumulado sólo disminuye o permanece constante. La gráfica inferior usa escala logarítmica para T.', 'small')
p('La temperatura graficada es la usada en cada nivel. Tras el último se aplica otro enfriamiento y se alcanza el valor de parada. La corrida principal aceptó 3331 empeoramientos, evidencia de que la búsqueda no se limitó a aceptar mejoras.')
p('Referencia exacta', 'heading')
p(f"Se resolvió la misma matriz por programación dinámica Held–Karp [3], obteniendo {exact['costo_optimo']:.9f}. El mejor costo del Templado Simulado coincide con esta referencia con tolerancia absoluta de 10⁻⁸. El cálculo de referencia procesó {exact['subproblemas']} subproblemas; además se contrastó su implementación con fuerza bruta sobre seis ciudades y las 120 permutaciones con origen fijo, coincidiendo ambos resultados.")
p(f"En las {experiment['repeticiones']} corridas con semillas 0–19, {hits} alcanzaron ese costo óptimo de referencia para esta instancia. Es una frecuencia observada de este experimento; no garantiza el óptimo en otras corridas, datos o calendarios de enfriamiento.")
p('El procedimiento satisface el enunciado: ciclo de 15 ciudades, vecindad por intercambio de dos posiciones y aceptación adaptada a minimización. La comparación exacta permite afirmar que el costo alcanzado es óptimo para esta matriz numérica, sin convertir al Templado Simulado en un método de garantía general.')
p('Fuentes consultadas', 'heading')
p('[1] Material de clase, sin fecha. 8-BúsquedasNoInf-Inf y heuristicas modernas(TempSim).ppt. Láminas 27–29: aceptación y empates; 30–31: algoritmo y enfriamiento; 32: Tarea 5.', 'reference')
blocks.append(('reference_link', '[2] MathWorks. How Simulated Annealing Works. Regla de aceptación; consulta: 3 de noviembre de 2026.', 'https://www.mathworks.com/help/gads/how-simulated-annealing-works.html'))
blocks.append(('reference_link', '[3] Held, M. y Karp, R. M. (1961). A dynamic programming approach to sequencing problems. ACM National Meeting. Ficha de IBM Research.', 'https://research.ibm.com/publications/a-dynamic-programming-approach-to-sequencing-problems'))


def hyperlink(paragraph, label, url):
    link = OxmlElement('w:hyperlink')
    link.set(qn('r:id'), paragraph.part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True))
    run = OxmlElement('w:r')
    prop = OxmlElement('w:rPr')
    color = OxmlElement('w:color'); color.set(qn('w:val'), '175F87'); prop.append(color)
    run.append(prop)
    node = OxmlElement('w:t'); node.text = label; run.append(node)
    link.append(run); paragraph._p.append(link)


doc = Document()
doc.core_properties.title = 'Tarea 5 · TSP con Templado Simulado'
doc.core_properties.subject = '15 ciudades, vecindad por intercambio y minimización'
doc.core_properties.author = ''
section = doc.sections[0]
section.page_width = Inches(8.5); section.page_height = Inches(11)
section.top_margin = section.bottom_margin = Inches(.6)
section.left_margin = section.right_margin = Inches(.65)
normal = doc.styles['Normal']
normal.font.name = 'Arial'; normal.font.size = Pt(10)
normal.paragraph_format.line_spacing = 1.08
normal.paragraph_format.space_after = Pt(5)
normal.paragraph_format.widow_control = True
for name, size in [('Title', 18), ('Subtitle', 10.5), ('Heading 1', 12.5), ('Heading 2', 10.5)]:
    style = doc.styles[name]
    style.font.name = 'Arial'; style.font.size = Pt(size)
    style.font.color.rgb = RGBColor.from_string('16485B')
    style.paragraph_format.keep_with_next = True
    style.paragraph_format.space_after = Pt(5)
    style.paragraph_format.space_before = Pt(6 if 'Heading' in name else 0)
footer = section.footer.paragraphs[0]
footer.alignment = 2
footer.add_run('Tarea 5 · ')
field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)


def word_p(text, role='body'):
    style = {'title': 'Title', 'subtitle': 'Subtitle', 'heading': 'Heading 1', 'subheading': 'Heading 2'}.get(role)
    paragraph = doc.add_paragraph(text, style=style)
    if role in ('small', 'reference'):
        for run in paragraph.runs:
            run.font.size = Pt(8)
    if role in ('formula', 'route'):
        paragraph.paragraph_format.keep_together = True
        for run in paragraph.runs:
            run.font.name = 'DejaVu Sans' if role == 'formula' else 'Arial'
            run.font.size = Pt(9)
    return paragraph


for block in blocks:
    kind = block[0]
    if kind == 'paragraph':
        word_p(block[1], block[2])
    elif kind == 'page':
        doc.add_page_break()
    elif kind == 'image':
        doc.add_picture(str(block[1]), width=Inches(block[2]))
    elif kind == 'code':
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.keep_together = True
        paragraph.paragraph_format.space_after = Pt(7)
        run = paragraph.add_run(block[1])
        run.font.name = 'Consolas'; run.font.size = Pt(8)
    elif kind == 'table':
        _, headers, rows, widths = block
        table_doc = doc.add_table(rows=1, cols=len(headers))
        table_doc.style = 'Light Shading Accent 1'; table_doc.autofit = False
        for i, label in enumerate(headers):
            table_doc.rows[0].cells[i].text = label
        repeating = OxmlElement('w:tblHeader'); table_doc.rows[0]._tr.get_or_add_trPr().append(repeating)
        for row in rows:
            for cell, value in zip(table_doc.add_row().cells, row):
                cell.text = str(value)
        for row in table_doc.rows:
            no_split = OxmlElement('w:cantSplit'); row._tr.get_or_add_trPr().append(no_split)
            for i, cell in enumerate(row.cells):
                cell.width = Inches(widths[i])
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_before = Pt(1.8)
                    paragraph.paragraph_format.space_after = Pt(1.8)
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
        doc.add_paragraph().paragraph_format.space_after = Pt(0)
    elif kind == 'reference_link':
        paragraph = word_p(block[1], 'reference')
        paragraph.paragraph_format.keep_together = True
        paragraph.add_run('\n')
        hyperlink(paragraph, block[2], block[2])
doc.save(OUT / 'Tarea_5_TSP_Templado_Simulado.docx')

font_dir = Path(matplotlib.get_data_path()) / 'fonts' / 'ttf'
for name, filename in [('DVS', 'DejaVuSans.ttf'), ('DVS-Bold', 'DejaVuSans-Bold.ttf'),
                       ('DVS-Mono', 'DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
pdfmetrics.registerFontFamily('DVS', normal='DVS', bold='DVS-Bold')
styles = {
    'body': ParagraphStyle('Body', fontName='DVS', fontSize=9.6, leading=13, spaceAfter=6, allowWidows=0, allowOrphans=0),
    'title': ParagraphStyle('Title', fontName='DVS-Bold', fontSize=17.5, leading=22, spaceAfter=7, textColor=colors.HexColor(NAVY)),
    'subtitle': ParagraphStyle('Subtitle', fontName='DVS', fontSize=10.2, leading=14, spaceAfter=6),
    'small': ParagraphStyle('Small', fontName='DVS', fontSize=7.9, leading=10.2, spaceAfter=5),
    'reference': ParagraphStyle('Reference', fontName='DVS', fontSize=7.8, leading=10.1, spaceAfter=5),
    'heading': ParagraphStyle('Heading', fontName='DVS-Bold', fontSize=12, leading=16, spaceBefore=7, spaceAfter=6, keepWithNext=True, textColor=colors.HexColor(NAVY)),
    'subheading': ParagraphStyle('Subheading', fontName='DVS-Bold', fontSize=10, leading=13, spaceBefore=5, spaceAfter=5, keepWithNext=True),
    'formula': ParagraphStyle('Formula', fontName='DVS', fontSize=10, leading=14.5, leftIndent=12, spaceAfter=7),
    'route': ParagraphStyle('Route', fontName='DVS', fontSize=9, leading=13, spaceAfter=5),
    'cell': ParagraphStyle('Cell', fontName='DVS', fontSize=8.7, leading=11.3),
    'headcell': ParagraphStyle('HeadCell', fontName='DVS-Bold', fontSize=8.5, leading=11.3, textColor=colors.white),
    'code': ParagraphStyle('Code', fontName='DVS-Mono', fontSize=7.6, leading=10.2, leftIndent=8, spaceAfter=8),
}
page_width, page_height = letter
body_width = page_width - 1.3 * inch
story = []
for block in blocks:
    kind = block[0]
    if kind == 'paragraph':
        story.append(Paragraph(escape(block[1]), styles[block[2]]))
    elif kind == 'page':
        story.append(PageBreak())
    elif kind == 'image':
        from PIL import Image
        with Image.open(block[1]) as image:
            width_px, height_px = image.size
        width = block[2] * inch
        story.append(PDFImage(str(block[1]), width=width, height=width * height_px / width_px))
    elif kind == 'code':
        story.append(Preformatted(block[1], styles['code']))
    elif kind == 'table':
        _, headers, rows, widths = block
        data = [[Paragraph(escape(str(value)), styles['headcell']) for value in headers]]
        data += [[Paragraph(escape(str(value)), styles['cell']) for value in row] for row in rows]
        t = Table(data, colWidths=[w / sum(widths) * body_width for w in widths], repeatRows=1)
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


def pdf_footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#D6E0E4'))
    canvas.line(.65*inch, .43*inch, page_width-.65*inch, .43*inch)
    canvas.setFont('DVS', 7.2)
    canvas.setFillColor(colors.HexColor('#52646C'))
    canvas.drawString(.65*inch, .27*inch, 'Tarea 5 · TSP con Templado Simulado')
    canvas.drawRightString(page_width-.65*inch, .27*inch, str(document.page))
    canvas.restoreState()


SimpleDocTemplate(str(OUT / 'Tarea_5_TSP_Templado_Simulado.pdf'), pagesize=letter,
    leftMargin=.65*inch, rightMargin=.65*inch, topMargin=.55*inch, bottomMargin=.57*inch,
    title='Tarea 5 · TSP con Templado Simulado', author='').build(story, onFirstPage=pdf_footer, onLaterPages=pdf_footer)
print('Generados Word, PDF y las dos figuras de la tarea 5.')
print('Reducción porcentual:', f'{reduction:.6f}')
print('Corridas que coinciden con el óptimo:', hits, '/', experiment['repeticiones'])

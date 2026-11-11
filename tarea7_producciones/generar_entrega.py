"""Entrega Word/PDF de Tarea 7 a partir de las trazas realmente ejecutadas."""
from pathlib import Path
from xml.sax.saxutils import escape
import json
import zipfile

import matplotlib
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak, KeepTogether
from razonamiento import resolver

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'entrega'
OUT.mkdir(exist_ok=True)
RESULTS = ROOT / 'resultados'
RESULTS.mkdir(exist_ok=True)
NAME = 'Tarea_7_Sistemas_de_Produccion'
R = resolver()
(RESULTS / 'trazas.json').write_text(json.dumps(R, ensure_ascii=False, indent=2), encoding='utf-8')
NAVY = '#16485B'
blocks = []

def p(text, role='body'):
    blocks.append(('paragraph', text, role))
def h(text):
    p(text, 'heading')
def table(headers, rows, widths):
    blocks.append(('table', headers, rows, widths))
def page():
    blocks.append(('page',))
def ref(label, url):
    blocks.append(('reference', label, url))
def mt(hechos):
    return '{' + ', '.join(hechos) + '}'

p('Tarea 7 · Sistemas de producción', 'title')
p('Trazas de razonamiento hacia adelante y hacia atrás', 'subtitle')
p('Fuente: presentación 10-Sistemas de procesamiento del conocimiento-C5.ppt, apartado «Tarea 7».', 'small')
h('1. Partes del modelo computacional')
p('Los símbolos p, q, r, s, t, u, v, w, Inicio y objetivo son hechos proposicionales. El símbolo ∧ indica que todas las condiciones deben cumplirse. Las reglas de producción se numeran en el orden del enunciado:')
table(['Regla', 'Condiciones', 'Efectos al dispararse'], [
    [regla['id'], ' ∧ '.join(regla['si']), ' ∧ '.join(regla['entonces'])]
    for regla in R['reglas']], [.7, 2.6, 3.8])
p('Memoria de trabajo (MT): conjunto de hechos conocidos. Se empieza con MT₀ = {Inicio}. R6 es una sola producción con acción compuesta: un disparo agrega simultáneamente v, r y q. No se divide en tres reglas. Los hechos se conservan y no se duplican; por tanto, Inicio también permanece en la MT.')
p('Meta: demostrar objetivo. El proceso termina con éxito al incorporarlo a la MT; termina sin éxito si no quedan reglas o justificaciones que permitan avanzar.')
h('Estrategia de control definida')
p('Hacia adelante: recorrer R1 a R6 y seleccionar la primera regla no disparada cuyas condiciones estén en MT y que agregue algún hecho. Tras ejecutarla, reiniciar el recorrido desde R1. Se aplica refracción: no repetir una producción ya disparada.')
p('Hacia atrás: comenzar con objetivo; consultar primero si la meta ya está en MT. Si no, buscar de R1 a R6 una regla que la contenga entre sus efectos y probar sus condiciones de izquierda a derecha, en profundidad. Sólo se dispara cuando todas quedan demostradas. Se guardan todos sus efectos, se evitan metas activas repetidas y se retrocede si falla una alternativa.')
p('Se distingue seleccionar una regla para investigarla de dispararla después de justificar sus condiciones. El razonamiento hacia atrás busca una prueba a partir de la conclusión; no convierte las implicaciones en implicaciones inversas. [1]', 'small')
h('Estado inicial y primera transición')
p('{Inicio} ──R6──→ {Inicio, v, r, q}', 'formula')
p('En adelante, R6 se reconoce directamente por Inicio. En atrás, se llega a R6 al intentar justificar r; se verifica Inicio y se incorporan también v y q. Así ambas ejecuciones respetan la misma producción y el mismo estado inicial.')

page()
h('2. Ejecución hacia adelante')
p('Se parte de los hechos y se agregan conclusiones. En cada ciclo sólo se dispara una regla. El conjunto conflicto de la tabla es el conjunto lógico de reglas aplicables que aportarían hechos; la estrategia implementada se detiene en la primera coincidencia y no necesita construirlo completo.')
forward_rows = [['0', '{Inicio}', '—', '—', '—']]
for step in R['adelante']['traza']:
    forward_rows.append([str(step['paso']), mt(step['mt_despues']),
                         '{' + step['regla'] + '}', step['regla'], ', '.join(step['nuevos'])])
table(['Paso', 'MT después del paso', 'Conflicto antes', 'Disparo', 'Hechos nuevos'], forward_rows,
      [.45, 3.0, 1.1, .65, 1.1])
p('R6 agrega v, r y q. Con v, R5 obtiene s. Con r y s, R2 obtiene p. Finalmente, p y q permiten disparar R1 y obtener objetivo. R3 y R4 no se activan: no hay soporte para w, ni para t y u; además, q ya fue obtenido por R6.')
h('3. Ejecución hacia atrás')
p('La meta inicial es objetivo. La tabla registra la selección de reglas, la consulta de hechos y el regreso que confirma sus conclusiones. No se agrega un hecho sólo por haberlo planteado como submeta.')
backward_rows = []
for i, event in enumerate(R['atras']['traza'], 1):
    if event['tipo'] == 'seleccion':
        action = f"Probar {event['meta']}: seleccionar {event['regla']}; pedir " + ' y '.join(event['submetas']) + '.'
    elif event['tipo'] == 'hecho':
        action = f"Confirmar {event['meta']}: ya está en MT."
    else:
        action = f"Disparar {event['regla']}: agregar " + ', '.join(event['nuevos']) + '.'
    backward_rows.append([str(i), action, mt(event['mt'])])
table(['Paso', 'Acción de control o inferencia', 'MT después del paso'], backward_rows,
      [.45, 3.55, 2.3])
p('Selección de reglas: R1 → R2 → R6 → R5. Disparos efectivos: R6 → R5 → R2 → R1. Cuando se revisa q, ya está en MT por R6: no se abren las alternativas R3 y R4 para intentar probarla.', 'small')

page()
h('4. Comparación de eficiencia')
p('Se comparan dos métricas explícitas, verificadas mediante el programa razonamiento.py: número de disparos y número de entradas de reglas inspeccionadas durante la selección lineal. No se usan tiempos de ejecución para declarar un ganador en un problema tan pequeño.')
table(['Métrica', 'Hacia adelante', 'Hacia atrás'], [
    ['Reglas disparadas', 'R6, R5, R2, R1', 'R6, R5, R2, R1'],
    ['Número de disparos', str(len(R['adelante']['disparadas'])), str(len(R['atras']['disparadas']))],
    ['Hechos nuevos', '6: v, r, q, s, p, objetivo', '6: v, r, q, s, p, objetivo'],
    ['Entradas de reglas inspeccionadas', str(R['adelante']['inspecciones']), str(R['atras']['inspecciones'])],
    ['MT final', mt(R['adelante']['mt']), mt(R['atras']['mt'])],
], [2.4, 2.35, 2.35])
p('En adelante se inspeccionan 6 entradas para elegir R6, 5 para R5, 2 para R2 y 1 para R1: 6 + 5 + 2 + 1 = 14. Este contador exige detenerse en la primera regla aplicable, tal como se definió; construir toda la agenda en cada ciclo tendría otro costo.')
p('En atrás se inspecciona 1 entrada para encontrar R1, 2 para R2, 6 para R6 y 5 para R5: 1 + 2 + 6 + 5 = 14. Inicio, v y q se confirman directamente en MT y no generan otra búsqueda de reglas. Las siete consultas a MT son: objetivo, p, r, Inicio, s, v y q.')
h('Respuesta: ¿qué método resulta más eficiente aquí?')
p('Con las métricas y la estrategia definidas hay empate: ambos necesitan cuatro disparos y catorce inspecciones. No hay una ventaja estricta en cantidad de inferencias para este conjunto. Todas las conclusiones que produce adelante forman parte de la justificación del objetivo.')
p('Hacia atrás dirige la búsqueda por la meta y evita intentar justificar q con R3 o R4 cuando ya la conoce. Eso no reduce los disparos frente a esta ejecución hacia adelante. Tampoco catorce inspecciones significan el mismo tiempo: adelante verifica condiciones y atrás busca efectos y administra la prueba. Cambiar la indexación o la estrategia puede cambiar el costo. [1]')
p('Si «Inicio → v ∧ r ∧ q» se considera sólo una anotación de carga inicial, se comienza con {v, r, q} y se excluye R6 del conteo en ambos métodos. En ese convenio ambos usan tres disparos y ocho inspecciones con el mismo control lineal. La conclusión de empate se mantiene.', 'small')
h('Reproducción y fuentes')
p('python razonamiento.py\npython generar_entrega.py', 'formula')
p('El primer programa sólo necesita Python estándar y guarda las trazas completas en resultados/trazas.json. El generador de documentos necesita python-docx, reportlab y matplotlib. Se comprobó que cada disparo tiene todas sus condiciones en la MT anterior y que ambas ejecuciones llegan al mismo estado final.', 'small')
p('Material del curso: presentación 10-Sistemas de procesamiento del conocimiento-C5.ppt, enunciado «Tarea 7» y apartados sobre memoria de trabajo, control y refracción. Las trazas y los conteos son elaboración propia.', 'small')
ref('[1] Poole, D. L., y Mackworth, A. K. Artificial Intelligence: Foundations of Computational Agents, 2.ª ed., sección 5.3.2, Proofs. Procedimientos hacia adelante y hacia atrás.',
    'https://www.cs.ubc.ca/~poole/aibook/2e/html2e/ArtInt2e.Ch5.S3.SS2.html')

# Word editable.
doc = Document()
doc.core_properties.title = 'Tarea 7: Sistemas de producción'
doc.core_properties.author = ''
section = doc.sections[0]
section.page_width, section.page_height = Inches(8.5), Inches(11)
section.top_margin = section.bottom_margin = Inches(.6)
section.left_margin = section.right_margin = Inches(.65)
normal = doc.styles['Normal']
normal.font.name, normal.font.size = 'Arial', Pt(9.5)
normal.paragraph_format.line_spacing = 1.02
normal.paragraph_format.space_after = Pt(6)
for name, size in [('Title', 18), ('Subtitle', 10.5), ('Heading 1', 11.5)]:
    style = doc.styles[name]
    style.font.name, style.font.size = 'Arial', Pt(size)
    style.font.color.rgb = RGBColor.from_string(NAVY[1:])
    style.paragraph_format.keep_with_next = True
    style.paragraph_format.space_before = Pt(7 if name == 'Heading 1' else 0)
    style.paragraph_format.space_after = Pt(6)
footer = section.footer.paragraphs[0]
footer.alignment = 2
footer.add_run('Tarea 7 · ')
field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)

for block in blocks:
    if block[0] == 'paragraph':
        _, text, role = block
        paragraph = doc.add_paragraph(text, style={'title': 'Title', 'subtitle': 'Subtitle', 'heading': 'Heading 1'}.get(role))
        if role == 'small':
            for run in paragraph.runs:
                run.font.size = Pt(8)
        if role == 'formula':
            paragraph.paragraph_format.keep_together = True
            for run in paragraph.runs:
                run.font.name, run.font.size = 'Cambria Math', Pt(9.5)
    elif block[0] == 'page':
        doc.add_page_break()
    elif block[0] == 'table':
        _, headers, rows, widths = block
        t = doc.add_table(rows=1, cols=len(headers)); t.style = 'Light Shading Accent 1'; t.autofit = False
        for cell, value in zip(t.rows[0].cells, headers):
            cell.text = value
        t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
        for row in rows:
            for cell, value in zip(t.add_row().cells, row):
                cell.text = value
        for row in t.rows:
            row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
            for i, cell in enumerate(row.cells):
                cell.width = Inches(widths[i] / sum(widths) * 7.2)
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_before = paragraph.paragraph_format.space_after = Pt(2)
                    for run in paragraph.runs:
                        run.font.size = Pt(8)
        doc.add_paragraph().paragraph_format.space_after = Pt(0)
    elif block[0] == 'reference':
        paragraph = doc.add_paragraph(block[1])
        paragraph.paragraph_format.keep_together = True
        for run in paragraph.runs:
            run.font.size = Pt(8)
        paragraph.add_run('\n')
        link = OxmlElement('w:hyperlink')
        link.set(qn('r:id'), paragraph.part.relate_to(block[2], RELATIONSHIP_TYPE.HYPERLINK, is_external=True))
        run = OxmlElement('w:r'); props = OxmlElement('w:rPr')
        color = OxmlElement('w:color'); color.set(qn('w:val'), '175F87'); props.append(color)
        size = OxmlElement('w:sz'); size.set(qn('w:val'), '15'); props.append(size)
        run.append(props); value = OxmlElement('w:t'); value.text = block[2]; run.append(value)
        link.append(run); paragraph._p.append(link)
doc.save(OUT / f'{NAME}.docx')

# PDF: se incorporan fuentes con los símbolos de lógica.
font_dir = Path(matplotlib.get_data_path()) / 'fonts/ttf'
for name, filename in [('DVS', 'DejaVuSans.ttf'), ('DVS-Bold', 'DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
styles = {
    'body': ParagraphStyle('Body', fontName='DVS', fontSize=9.2, leading=12.6, spaceAfter=7),
    'title': ParagraphStyle('Title', fontName='DVS-Bold', fontSize=18, leading=23, spaceAfter=7, textColor=colors.HexColor(NAVY)),
    'subtitle': ParagraphStyle('Subtitle', fontName='DVS', fontSize=10.2, leading=14, spaceAfter=7),
    'heading': ParagraphStyle('Heading', fontName='DVS-Bold', fontSize=11.3, leading=15.5, spaceBefore=7, spaceAfter=6, keepWithNext=True, textColor=colors.HexColor(NAVY)),
    'small': ParagraphStyle('Small', fontName='DVS', fontSize=7.8, leading=10.7, spaceAfter=6),
    'formula': ParagraphStyle('Formula', fontName='DVS', fontSize=9.5, leading=14, leftIndent=8, spaceAfter=8),
    'cell': ParagraphStyle('Cell', fontName='DVS', fontSize=7.8, leading=10.5),
    'headcell': ParagraphStyle('HeadCell', fontName='DVS-Bold', fontSize=7.8, leading=10.5, textColor=colors.white),
}
body_width = letter[0] - 1.3 * inch
story = []
for block in blocks:
    if block[0] == 'paragraph':
        story.append(Paragraph(escape(block[1]).replace('\n', '<br/>'), styles[block[2]]))
    elif block[0] == 'page':
        story.append(PageBreak())
    elif block[0] == 'table':
        _, headers, rows, widths = block
        data = [[Paragraph(escape(str(text)), styles['headcell' if i == 0 else 'cell']) for text in row]
                for i, row in enumerate([headers, *rows])]
        t = Table(data, colWidths=[x / sum(widths) * body_width for x in widths], repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(NAVY)),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#EFF4F6'), colors.white]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.extend([KeepTogether([t]), Spacer(1, 8)])
    elif block[0] == 'reference':
        value = escape(block[1]) + '<br/><link color="#175F87" href="' + escape(block[2]) + '">' + escape(block[2]) + '</link>'
        story.append(KeepTogether([Paragraph(value, styles['small'])]))

def footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#D6E0E4'))
    canvas.line(.65 * inch, .43 * inch, letter[0] - .65 * inch, .43 * inch)
    canvas.setFont('DVS', 7.3); canvas.setFillColor(colors.HexColor('#52646C'))
    canvas.drawString(.65 * inch, .27 * inch, 'Tarea 7 · Sistemas de producción')
    canvas.drawRightString(letter[0] - .65 * inch, .27 * inch, str(document.page))
    canvas.restoreState()

SimpleDocTemplate(str(OUT / f'{NAME}.pdf'), pagesize=letter,
                  leftMargin=.65 * inch, rightMargin=.65 * inch,
                  topMargin=.55 * inch, bottomMargin=.6 * inch,
                  title='Tarea 7: Sistemas de producción', author='').build(
                      story, onFirstPage=footer, onLaterPages=footer)

textos = []
for block in blocks:
    if block[0] == 'paragraph':
        textos.append(block[1])
    elif block[0] == 'table':
        textos.append('\n'.join(' | '.join(row) for row in [block[1], *block[2]]))
    elif block[0] == 'reference':
        textos.append(block[1] + '\n' + block[2])
(OUT / f'{NAME}.txt').write_text('\n\n'.join(textos), encoding='utf-8')

with zipfile.ZipFile(OUT / f'{NAME}.docx') as documento:
    assert documento.testzip() is None
with zipfile.ZipFile(OUT / 'Tarea_7_Completa.zip', 'w', zipfile.ZIP_DEFLATED) as paquete:
    archivos = [ROOT / 'razonamiento.py', ROOT / 'generar_entrega.py', RESULTS / 'trazas.json']
    archivos += [OUT / f'{NAME}.{extension}' for extension in ['docx', 'pdf', 'txt']]
    archivos += [ROOT / 'material/presentacion10_texto.txt']
    for archivo in archivos:
        paquete.write(archivo, Path('Tarea_7') / archivo.relative_to(ROOT))
print('Word, PDF, texto y paquete generados con trazas verificadas.')

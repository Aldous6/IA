"""Genera Word, PDF y texto de la Tarea 8 desde un contenido común."""
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'entrega'
OUT.mkdir(exist_ok=True)
NAME = 'Tarea_8_Logica_de_Primer_Orden'
NAVY = '#16485B'

vocabulario = [
    ('Persona(x)', 'x es una persona.'),
    ('Tiempo(t)', 't es un instante del intervalo temporal considerado.'),
    ('Estudiante(x)', 'x es estudiante.'),
    ('Inteligente(x)', 'x es inteligente.'),
    ('Lleva(x, c)', 'La persona x cursa el curso c.'),
    ('Aprueba(x, c)', 'La persona x aprueba el curso c.'),
    ('Politico(x)', 'x es político.'),
    ('PuedeEnganar(p, x, t)', 'La persona p puede engañar a la persona x en el instante t.'),
    ('Peluquero(x)', 'x es peluquero.'),
    ('Hombre(x)', 'x es un hombre.'),
    ('ViveEn(x, l)', 'La persona x vive en la localidad l.'),
    ('CortaPelo(x, y)', 'La persona x corta el pelo a la persona y.'),
]

F1 = ('∀x [(Estudiante(x) ∧ Inteligente(x) ∧ Lleva(x, ia))\n'
      '     → Aprueba(x, ia)]')
F2 = ('∀p [Politico(p) → (\n'
      '  ∃x [Persona(x) ∧ ∀t (Tiempo(t) → PuedeEnganar(p, x, t))]\n'
      '  ∧ ∃t [Tiempo(t) ∧ ∀x (Persona(x) → PuedeEnganar(p, x, t))]\n'
      '  ∧ ¬∀x∀t [(Persona(x) ∧ Tiempo(t)) → PuedeEnganar(p, x, t)]\n'
      ')]')
F2_NEG = '∃x∃t [Persona(x) ∧ Tiempo(t) ∧ ¬PuedeEnganar(p, x, t)]'
F2_ALT = ('∀x [Persona(x) →\n'
          '    ∃t (Tiempo(t) ∧ PuedeEnganar(p, x, t))]')
F3 = ('∃b [Peluquero(b) ∧\n'
      '    ∀x ((Hombre(x) ∧ ViveEn(x, pueblo) ∧ ¬CortaPelo(x, x))\n'
      '        → CortaPelo(b, x))]')
F3_EXTRA = ('∃b [Peluquero(b) ∧ Hombre(b) ∧ ViveEn(b, pueblo) ∧\n'
            '    ∀x ((Hombre(x) ∧ ViveEn(x, pueblo)) →\n'
            '        (CortaPelo(b, x) ↔ ¬CortaPelo(x, x)))]')

blocks = []
def p(text, role='body'):
    blocks.append(('paragraph', text, role))
def formula(text):
    p(text, 'formula')
def heading(text):
    p(text, 'heading')
def page():
    blocks.append(('page',))
def reference(label, url):
    blocks.append(('reference', label, url))

p('Tarea 8 · Lógica de primer orden', 'title')
p('Representación de expresiones con un vocabulario consistente', 'subtitle')
p('Fuente del enunciado: presentación 12-Logica-ProcedSkolem_Est.pptx, lámina 10.', 'small')
heading('Vocabulario común')
p('El dominio contiene personas, instantes, cursos y localidades. Las constantes ia y pueblo designan, respectivamente, el curso de Inteligencia Artificial y el pueblo mencionado. Se usan los mismos símbolos y el mismo orden de argumentos en las tres expresiones.')
blocks.append(('vocabulary', vocabulario))
p('Estudiante, Inteligente, Politico, Peluquero y Hombre se interpretan sobre personas. Lleva y Aprueba relacionan personas con cursos; ViveEn, personas con localidades. Persona y Tiempo restringen explícitamente las variables cuando corresponde.', 'small')
p('Notación: ∀ = para todo; ∃ = existe al menos uno; ∧ = y; ¬ = no; → = si… entonces; ↔ = si y sólo si.', 'small')
heading('1. Estudiantes y curso de IA')
p('«Cada estudiante inteligente que lleva el curso de IA lo pasa».', 'quote')
formula(F1)
p('Para cualquier individuo x, si es estudiante, es inteligente y cursa IA, entonces aprueba ese mismo curso. Las tres condiciones se unen mediante conjunción y forman el antecedente de la implicación. La constante ia evita cambiar de curso entre el antecedente y la conclusión.')

page()
heading('2. Políticos, personas y tiempo')
p('«Los políticos pueden engañar a algunas personas todo el tiempo y ellos pueden engañar a todas las personas algún tiempo, pero ellos no pueden engañar a toda la gente todo el tiempo».', 'quote')
p('Se toma como lectura principal que, para cada político, hay algún instante común en el que puede engañar a todas las personas. Ese instante puede ser diferente para cada político. PuedeEnganar representa capacidad; no afirma que el engaño ocurra efectivamente.')
formula(F2)
p('La primera conjunción elige al menos una persona x y después exige que ese político pueda engañarla en todo instante. El orden ∃x∀t mantiene a la misma persona a través del tiempo; esa persona puede depender del político.')
p('La segunda conjunción elige un instante t antes de cuantificar a todas las personas. El orden ∃t∀x exige un momento común para ellas. No exige un mismo momento para todos los políticos, porque ∃t queda dentro de ∀p.')
p('La tercera conjunción niega la combinación «todas las personas, todo el tiempo». No dice que el político nunca pueda engañar a nadie. Para un político p, esa negación equivale a:')
formula(F2_NEG)
p('Es decir, hay al menos una persona y un instante en los que ese político no puede engañarla. «Pero» se representa como conjunción: añade una condición, sin introducir un conector lógico distinto.')
heading('Lectura alternativa del tiempo')
p('Si «a todas las personas algún tiempo» permite que cada persona tenga un instante diferente, se reemplaza únicamente la segunda conjunción por:')
formula(F2_ALT)
p('Ahora el orden es ∀x∃t. No es equivalente a la lectura principal: podría engañar siempre a C, a A sólo en t₀ y a B sólo en t₁, sin poder engañar a las tres en un mismo instante. Por eso se declara expresamente la lectura utilizada. [1]', 'small')

page()
heading('3. El peluquero y los hombres del pueblo')
p('«Existe un peluquero quien corta el pelo a todos los hombres del pueblo quienes no se lo cortan por sí mismos».', 'quote')
formula(F3)
p('Existe al menos un peluquero b tal que, para cada x, si x es hombre, vive en el pueblo y no se corta el pelo a sí mismo, entonces b le corta el pelo. La misma variable b permanece bajo el alcance del existencial para todos los hombres considerados.')
p('CortaPelo(x, x) expresa que x se corta el pelo a sí mismo. Su negación describe a los hombres a quienes debe atender el peluquero. El existencial no exige que haya un único peluquero.')
heading('Precisión sobre la paradoja del barbero')
p('El texto dice que atiende a todos los hombres que cumplen la condición; no añade que atienda solamente a ellos. Por eso se usa → y no ↔. Tampoco afirma que el peluquero sea un hombre del pueblo. La traducción literal no obliga a una contradicción.')
p('Por ejemplo, puede haber dos hombres del pueblo, b y m: b es peluquero, se corta el pelo a sí mismo y también se lo corta a m; m no se lo corta a sí mismo. Este caso satisface la fórmula literal.')
p('La versión clásica requiere condiciones adicionales: que b sea hombre del pueblo y que atienda a esos hombres si y sólo si no se cortan el pelo por sí mismos. [2] Esa versión más fuerte sería:')
formula(F3_EXTRA)
p('Al sustituir x = b en esa versión se obtiene CortaPelo(b, b) ↔ ¬CortaPelo(b, b), que es contradictorio. Estas condiciones adicionales no se incorporan a la respuesta literal de la tarea.', 'small')
heading('Fuentes de consulta')
p('Material del curso: 12-Logica-ProcedSkolem_Est.pptx, lámina 10. Las formalizaciones y los ejemplos de interpretación son elaboración propia.', 'small')
reference('[1] Stanford University, CS103. First-Order Translation Checklist. Alcance de variables y combinación de cuantificadores y conectivos.',
          'https://web.stanford.edu/class/cs103/fol_checklist')
reference('[2] William J. Rapaport, University at Buffalo. The Barber Paradox. Explicita «todos y solamente», y la pertenencia del barbero al pueblo.',
          'https://cse.buffalo.edu/~rapaport/191/barber.html')

# Word editable.
doc = Document()
doc.core_properties.title = 'Tarea 8: Lógica de primer orden'
doc.core_properties.author = ''
section = doc.sections[0]
section.page_width, section.page_height = Inches(8.5), Inches(11)
section.top_margin = section.bottom_margin = Inches(.65)
section.left_margin = section.right_margin = Inches(.7)
normal = doc.styles['Normal']
normal.font.name, normal.font.size = 'Arial', Pt(10)
normal.paragraph_format.line_spacing = 1.05
normal.paragraph_format.space_after = Pt(7)
for name, size in [('Title', 18), ('Subtitle', 11), ('Heading 1', 12)]:
    style = doc.styles[name]
    style.font.name, style.font.size = 'Arial', Pt(size)
    style.font.color.rgb = RGBColor.from_string(NAVY[1:])
    style.paragraph_format.space_before = Pt(7 if name == 'Heading 1' else 0)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.keep_with_next = True
footer = section.footer.paragraphs[0]
footer.alignment = 2
footer.add_run('Tarea 8 · ')
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'PAGE')
footer._p.append(field)

def word_link(paragraph, url):
    hyperlink = OxmlElement('w:hyperlink')
    relation = paragraph.part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink.set(qn('r:id'), relation)
    run = OxmlElement('w:r')
    props = OxmlElement('w:rPr')
    color = OxmlElement('w:color'); color.set(qn('w:val'), '175F87'); props.append(color)
    size = OxmlElement('w:sz'); size.set(qn('w:val'), '16'); props.append(size)
    run.append(props)
    text = OxmlElement('w:t'); text.text = url; run.append(text)
    hyperlink.append(run); paragraph._p.append(hyperlink)

for block in blocks:
    if block[0] == 'paragraph':
        _, text, role = block
        paragraph = doc.add_paragraph(text, style={'title': 'Title', 'subtitle': 'Subtitle', 'heading': 'Heading 1'}.get(role))
        if role == 'formula':
            paragraph.paragraph_format.left_indent = Inches(.12)
            paragraph.paragraph_format.keep_together = True
            for run in paragraph.runs:
                run.font.name, run.font.size = 'Cambria Math', Pt(10)
        if role == 'small':
            for run in paragraph.runs:
                run.font.size = Pt(8.4)
        if role == 'quote':
            for run in paragraph.runs:
                run.italic = True
    elif block[0] == 'page':
        doc.add_page_break()
    elif block[0] == 'vocabulary':
        table = doc.add_table(rows=1, cols=2)
        table.style = 'Light Shading Accent 1'
        table.autofit = False
        table.rows[0].cells[0].text, table.rows[0].cells[1].text = 'Símbolo', 'Significado'
        for symbol, meaning in block[1]:
            cells = table.add_row().cells
            cells[0].text, cells[1].text = symbol, meaning
        for row in table.rows:
            row.cells[0].width, row.cells[1].width = Inches(2), Inches(5.1)
            row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_after = Pt(3)
                    paragraph.paragraph_format.space_before = Pt(3)
                    for run in paragraph.runs:
                        run.font.size = Pt(8.8)
        doc.add_paragraph().paragraph_format.space_after = Pt(0)
    elif block[0] == 'reference':
        paragraph = doc.add_paragraph(block[1])
        paragraph.paragraph_format.keep_together = True
        for run in paragraph.runs:
            run.font.size = Pt(8)
        paragraph.add_run('\n')
        word_link(paragraph, block[2])
doc.save(OUT / f'{NAME}.docx')

# PDF con fuentes incorporadas para conservar símbolos lógicos.
fonts = Path(matplotlib.get_data_path()) / 'fonts/ttf'
for name, filename in [('DVS', 'DejaVuSans.ttf'), ('DVS-Bold', 'DejaVuSans-Bold.ttf'),
                       ('DVS-Italic', 'DejaVuSans-Oblique.ttf'), ('DVS-Mono', 'DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))
pdfmetrics.registerFontFamily('DVS', normal='DVS', bold='DVS-Bold', italic='DVS-Italic')
styles = {
    'body': ParagraphStyle('Body', fontName='DVS', fontSize=9.7, leading=13.3, spaceAfter=8),
    'title': ParagraphStyle('Title', fontName='DVS-Bold', fontSize=18, leading=23, spaceAfter=7, textColor=colors.HexColor(NAVY)),
    'subtitle': ParagraphStyle('Subtitle', fontName='DVS', fontSize=10.5, leading=15, spaceAfter=7),
    'heading': ParagraphStyle('Heading', fontName='DVS-Bold', fontSize=11.5, leading=16, spaceBefore=8, spaceAfter=7, keepWithNext=True, textColor=colors.HexColor(NAVY)),
    'small': ParagraphStyle('Small', fontName='DVS', fontSize=8.1, leading=11.1, spaceAfter=7),
    'quote': ParagraphStyle('Quote', fontName='DVS-Italic', fontSize=9.5, leading=13.2, spaceAfter=10),
    'formula': ParagraphStyle('Formula', fontName='DVS-Mono', fontSize=8.6, leading=14.5, leftIndent=8, spaceAfter=12),
    'cell': ParagraphStyle('Cell', fontName='DVS', fontSize=8.3, leading=11),
    'headcell': ParagraphStyle('HeadCell', fontName='DVS-Bold', fontSize=8.5, leading=11, textColor=colors.white),
}
body_width = letter[0] - 1.4 * inch
story = []
for block in blocks:
    if block[0] == 'paragraph':
        _, text, role = block
        if role == 'formula':
            assert all(pdfmetrics.stringWidth(line, 'DVS-Mono', 8.6) < body_width - 8
                       for line in text.splitlines())
        rendered = escape(text).replace(' ', '&nbsp;').replace('\n', '<br/>') if role == 'formula' else escape(text).replace('\n', '<br/>')
        paragraph = Paragraph(rendered, styles[role])
        story.append(KeepTogether([paragraph]) if role == 'formula' else paragraph)
    elif block[0] == 'page':
        story.append(PageBreak())
    elif block[0] == 'vocabulary':
        rows = [['Símbolo', 'Significado'], *block[1]]
        data = [[Paragraph(escape(text), styles['headcell' if i == 0 else 'cell']) for text in row]
                for i, row in enumerate(rows)]
        table = Table(data, colWidths=[2.0 * inch, body_width - 2.0 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(NAVY)),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#EFF4F6'), colors.white]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.extend([KeepTogether([table]), Spacer(1, 9)])
    elif block[0] == 'reference':
        text = escape(block[1]) + '<br/><link color="#175F87" href="' + escape(block[2]) + '">' + escape(block[2]) + '</link>'
        story.append(KeepTogether([Paragraph(text, styles['small'])]))

def footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#D6E0E4'))
    canvas.line(.7 * inch, .45 * inch, letter[0] - .7 * inch, .45 * inch)
    canvas.setFont('DVS', 7.5)
    canvas.setFillColor(colors.HexColor('#52646C'))
    canvas.drawString(.7 * inch, .28 * inch, 'Tarea 8 · Lógica de primer orden')
    canvas.drawRightString(letter[0] - .7 * inch, .28 * inch, str(document.page))
    canvas.restoreState()

SimpleDocTemplate(str(OUT / f'{NAME}.pdf'), pagesize=letter,
                  leftMargin=.7 * inch, rightMargin=.7 * inch,
                  topMargin=.6 * inch, bottomMargin=.65 * inch,
                  title='Tarea 8: Lógica de primer orden', author='').build(
                      story, onFirstPage=footer, onLaterPages=footer)

# Versión de texto y archivo de fórmulas para facilitar la revisión.
text = []
for block in blocks:
    if block[0] == 'paragraph':
        text.append(block[1])
    elif block[0] == 'vocabulary':
        text.extend(f'{symbol}: {meaning}' for symbol, meaning in block[1])
    elif block[0] == 'reference':
        text.append(block[1] + '\n' + block[2])
(OUT / f'{NAME}.txt').write_text('\n\n'.join(text), encoding='utf-8')
(ROOT / 'formulas.json').write_text(json.dumps({
    'fuente_enunciado': '12-Logica-ProcedSkolem_Est.pptx, lámina 10',
    'vocabulario': dict(vocabulario), 'constantes': {'ia': 'curso de IA', 'pueblo': 'pueblo mencionado'},
    'expresion_1': F1, 'expresion_2_lectura_tiempo_comun': F2,
    'alternativa_segunda_conjuncion_tiempo_individual': F2_ALT,
    'expresion_3_literal': F3, 'version_barbero_con_condiciones_adicionales': F3_EXTRA,
}, ensure_ascii=False, indent=2), encoding='utf-8')

with zipfile.ZipFile(OUT / f'{NAME}.docx') as archivo:
    assert archivo.testzip() is None
print('Generados Word, PDF y texto de Tarea 8; DOCX íntegro.')

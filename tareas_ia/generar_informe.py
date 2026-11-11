"""Construye una misma entrega académica en Word y PDF, con resultados reales."""
from pathlib import Path
import csv
import importlib.util
import json
import re
import shutil
import sys
import textwrap
import zipfile
from xml.sax.saxutils import escape

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PDFImage,
    PageBreak, Preformatted, KeepTogether,
)

from tarea2_aspiradora import resolver

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'entrega'
OUT.mkdir(exist_ok=True)
RESULTS = ROOT / 'resultados'
task2 = resolver(RESULTS)
spec = importlib.util.spec_from_file_location('tarea3', ROOT / 'revision_tarea3' / 'simulacion_tarea3.py')
task3_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(task3_module)
task3 = task3_module.verificar_todas()

FONTDIR = Path(sys.prefix) / 'Lib/site-packages/matplotlib/mpl-data/fonts/ttf'
for name, filename in [('DVS', 'DejaVuSans.ttf'), ('DVS-Bold', 'DejaVuSans-Bold.ttf'),
                       ('DVS-Oblique', 'DejaVuSans-Oblique.ttf'), ('DVS-Mono', 'DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONTDIR / filename)))
pdfmetrics.registerFontFamily('DVS', normal='DVS', bold='DVS-Bold', italic='DVS-Oblique', boldItalic='DVS-Bold')

SOURCES = [
    ('P3', 'Material de clase, sin fecha. 3-Estado del Arte de la IA-e.ppt.', None),
    ('P5', 'Material de clase, sin fecha. 5-Agentes inteligentes-1de2.pdf, página 9 (Tarea 2).', None),
    ('P6', 'Material de clase, sin fecha. 6-Agentes inteligentes-2de2.pdf, páginas 10–13 (Tarea 3).', None),
    ('A1', 'OpenAI. Use ChatGPT. Documentación oficial, s.f.', 'https://learn.chatgpt.com/docs/use-chatgpt'),
    ('A2', 'OpenAI. Models. Documentación oficial, s.f.', 'https://learn.chatgpt.com/docs/models'),
    ('A3', 'Anthropic. Models overview. Documentación oficial, s.f.', 'https://platform.claude.com/docs/en/models/overview'),
    ('A4', 'Anthropic. Computer use tool. Documentación oficial, s.f.', 'https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool'),
    ('A5', 'Gemini Team, Google DeepMind (2025). Gemini 2.5: Pushing the Frontier with Advanced Reasoning, Multimodality, Long Context, and Next Generation Agentic Capabilities, sección 2.1.', 'https://storage.googleapis.com/deepmind-media/gemini/gemini_v2_5_report.pdf'),
    ('A6', 'Google. Using tools with Gemini API. Documentación oficial, s.f.', 'https://aistudio.google.com/docs/tools'),
    ('A7', 'Microsoft. Microsoft Copilot overview. Documentación oficial, s.f.', 'https://learn.microsoft.com/en-us/microsoft-365/copilot/copilot-overview'),
    ('A8', 'GitHub. About GitHub Copilot. Documentación oficial, s.f.', 'https://docs.github.com/en/copilot/get-started/about-github-copilot'),
    ('A9', 'GitHub. GitHub Copilot on GitHub.com and GitHub Mobile. Incluye la experiencia disponible desde el 28 de octubre de 2026.', 'https://docs.github.com/en/copilot/concepts/copilot-surfaces/copilot-on-github'),
    ('B1', 'Perplexity. Rethinking Search as Code Generation. Publicación técnica oficial, s.f.', 'https://www.perplexity.ai/en-GB/hub/blog/rethinking-search-as-code-generation'),
    ('B2', 'Perplexity. What is Pro Search? Documentación oficial, s.f.', 'https://www.perplexity.ai/help-center/en/articles/10352903-what-is-pro-search'),
    ('B3', 'Amazon. How Amazon rebuilt Alexa with generative AI. Publicación técnica oficial, s.f.', 'https://www.aboutamazon.com/news/devices/new-alexa-tech-generative-artificial-intelligence'),
    ('B4', 'Yoshitake, M. (26 de febrero de 2025). Introducing AI-native SDKs for Alexa+. Amazon Developer.', 'https://developer.amazon.com/en-US/blogs/alexa/alexa-skills-kit/2025/02/new-alexa-announce-blog'),
    ('B5', 'Apple Machine Learning Research (8 de junio de 2026; actualización 9 de septiembre de 2026). Introducing the Third Generation of Apple’s Foundation Models.', 'https://machinelearning.apple.com/research/introducing-third-generation-of-apple-foundation-models'),
    ('B6', 'Apple (14 de septiembre de 2026). Siri AI, a profoundly more capable and personal assistant powered by the next generation of Apple Intelligence, is here. Apple Newsroom.', 'https://www.apple.com/newsroom/2026/09/siri-ai-a-profoundly-more-capable-and-personal-assistant-is-here/'),
    ('B7', 'Isomorphic Labs (8 de mayo de 2024; actualización 11 de noviembre de 2024). AlphaFold 3 predicts the structure and interactions of all of life’s molecules.', 'https://www.isomorphiclabs.com/articles/alphafold-3-predicts-the-structure-and-interactions-of-all-of-lifes-molecules'),
    ('B8', 'Google DeepMind. AlphaFold 3 inference pipeline. Repositorio oficial, s.f.', 'https://github.com/google-deepmind/alphafold3'),
    ('B9', 'Waymo. Waymo Driver: Self-Driving Car Technology for a Reliable Ride. Descripción técnica oficial, s.f.', 'https://waymo.com/waymo-driver/'),
    ('B10', 'The Waymo Team (6 de julio de 2021). Simulation City: Introducing Waymo’s most advanced simulation system yet for autonomous driving.', 'https://waymo.com/blog/2021/07/simulation-city/'),
    ('C1', 'Ritter, F. E., Kim, J. W. y Oury, J. D. (20 de junio de 2017). ACT-R: Frequently Asked Questions List. Penn State, secciones G1, G4 y G8.', 'https://acs.ist.psu.edu/projects/act-r-faq/act-r-faq.html'),
    ('C2', 'Dulam, S., Gay, J. R. y Dancy, C. L. (2026). New knowledge source pipelines for sociocultural representations in a cognitive architecture. Frontiers in Psychology, 17, 1874556.', 'https://doi.org/10.3389/fpsyg.2026.1874556'),
    ('C3', 'Wang, P. (agosto de 2026). A Logical Model of Intelligence — An introduction to NARS. Temple University.', 'https://cis.temple.edu/~pwang/NARS-Intro.html'),
    ('C4', 'OpenNARS. OpenNARS for Research 3.0+. Repositorio oficial, s.f.', 'https://github.com/opennars/opennars'),
    ('G1', 'Morris, M. R. y colaboradores (2023; revisión 2025). Levels of AGI for Operationalizing Progress on the Path to AGI. arXiv:2311.02462.', 'https://arxiv.org/abs/2311.02462'),
    ('T1', 'Jones, C. R. y Bergen, B. K. (19 de mayo de 2026). Large language models pass a standard three-party Turing test. PNAS, 123(21), e2524472123. Tablas 1 y 2.', 'https://doi.org/10.1073/pnas.2524472123'),
    ('L1', 'Russell, S. y Norvig, P. Artificial Intelligence: A Modern Approach. Capítulo 2, Intelligent Agents, página impresa 36 del capítulo público: supuestos del mundo aspiradora.', 'https://aima.eecs.berkeley.edu/4th-ed/pdfs/newchap02.pdf'),
]


def entries(filename):
    text = (ROOT / filename).read_text(encoding='utf-8')
    matches = re.findall(r'^\*\*(.+?)\*\*\s*(.+?)(?=\n\n|\Z)', text, flags=re.M | re.S)
    result = []
    for title, body in matches:
        title = re.sub(r'^\d+\.\s*', '', title).rstrip('.')
        body = re.sub(r'Fuentes (B\d+) y (B\d+)\.', r'[\1, \2]', body)
        body = re.sub(r'\s+', ' ', body).strip()
        result.append((title, body))
    return result


fichas = entries('investigacion_a.md') + entries('investigacion_b.md') + entries('investigacion_cognitiva.md')
assert len(fichas) == 12

blocks = []


def p(text, style='body'):
    blocks.append(('p', text, style))


def table(headers, rows, widths=None):
    blocks.append(('table', headers, rows, widths))


def heading(text):
    p(text, 'heading')


def page():
    blocks.append(('page',))


p('Inteligencia Artificial · Tareas 1, 2 y 3', 'title')
p('Estado del arte, agente aspiradora y reglas de navegación', 'subtitle')
p('Consulta de fuentes: 3 de noviembre de 2026. Enunciados: carpeta presentaciones.', 'small')

heading('Tarea 1. Agentes, asistentes y entidades inteligentes')
p('Se analizan doce sistemas: diez asistentes o entidades de uso e investigación actuales, más ACT-R y NARS para conectar la investigación con los antecedentes de la presentación 3. Se describe la arquitectura pública de cada sistema y se distingue la aplicación del modelo que utiliza: un asistente puede cambiar de modelo, herramientas o permisos. Cuando la topología neuronal es propietaria y no está publicada en las fuentes revisadas, se indica expresamente. [P3]')
p('AGI es la sigla habitual de inteligencia artificial general; corresponde a la GAI de la consigna. Para valorar avances se consideran amplitud de tareas, desempeño y autonomía, dimensiones del marco de Morris y colaboradores. Las valoraciones siguientes son análisis propio de capacidades documentadas. Satisfacer objetivos parciales —por ejemplo, transferir conocimientos entre tareas— no demuestra haber alcanzado competencia general humana. [G1]')

for i, (title, body) in enumerate(fichas, 1):
    p(f'{i}. {title}', 'subheading')
    # Dos párrafos por ficha cuando hay una frontera natural entre descripción y valoración.
    markers = ['Relación con AGI:', 'Valoración sobre AGI:', 'Como objetivo relacionado con AGI,']
    split_at = next((body.find(marker) for marker in markers if body.find(marker) > 0), -1)
    if split_at > 0:
        p(body[:split_at].strip())
        p(body[split_at:].strip())
    else:
        p(body)

heading('Turing: porcentajes publicados y su interpretación')
p('El porcentaje siguiente es la fracción de partidas en que un juez eligió a la IA como el interlocutor humano, frente a una persona real. No representa “porcentaje de inteligencia” ni una probabilidad universal de aprobar. El estudio de Jones y Bergen empleó conversaciones por texto, tres participantes y configuraciones específicas; en la condición PERSONA se pidió imitar una personalidad humana. [T1]')
table(['Sistema y condición del estudio', 'Duración', 'Elegido como humano'], [
    ['GPT-4.5, PERSONA', '5 minutos', '73 %'],
    ['Llama-3.1-405B, PERSONA', '5 minutos', '56 %'],
    ['GPT-4o, sin PERSONA', '5 minutos', '21 %'],
    ['ELIZA, referencia histórica', '5 minutos', '23 %'],
    ['GPT-5, PERSONA', '15 minutos', '59.3 % (89/150 partidas)'],
], [3.65, 1.05, 1.65])
p('Fuente: [T1], tablas 1–2. El 50 % es la referencia de elección al azar en este protocolo. Los autores concluyen que GPT-4.5, Llama-3.1 y GPT-5 cumplen su criterio bajo las condiciones estudiadas. El estilo conversacional y las instrucciones influyen en el resultado. Estos datos no pueden transferirse a ChatGPT, Claude, Gemini u otros productos con versiones y configuraciones diferentes. Para los doce sistemas descritos se conserva “sin porcentaje verificable” o “no aplica directamente”, según sus interfaces. No se inventan estimaciones numéricas.')
p('La prueba examina semejanza conversacional; por sí sola no acredita AGI. Los asistentes de propósito amplio aportan versatilidad; Copilot se concentra en trabajo o programación; AlphaFold y Waymo demuestran capacidades especializadas; ACT-R y NARS exploran integración cognitiva y razonamiento. Las fuentes consultadas permiten reconocer avances parciales, pero no acreditar AGI completa en ninguno de estos sistemas. [G1; T1]')

page()
heading('Tarea 2. Agente aspiradora de reflejo simple')
p('La página 9 de la presentación 5 pide implementar el agente, simular todas las configuraciones iniciales y registrar puntajes y promedio. Se sigue ese enunciado, identificado allí como ejercicio 2.9; la numeración varía entre ediciones del libro. [P5]')
p('Se utiliza el mundo de dos casillas A y B del libro: posición inicial desconocida para el diseñador del ensayo, suciedad inicial en cualquiera de las casillas, suciedad estática y acciones deterministas. El agente sólo percibe su posición y si esa casilla está sucia. El horizonte es de 1000 pasos y se otorga un punto por casilla limpia en cada paso, sin penalización de movimiento. Estos supuestos proceden del capítulo público del libro. [L1]')
p('Hay 2 posiciones iniciales × 2 estados de A × 2 estados de B = 8 casos. La regla es: si la casilla actual está sucia, aspirar; si está limpia y el agente está en A, ir a B; si está limpia y está en B, ir a A. El programa del agente no guarda historial ni conoce directamente la suciedad de la otra casilla.')
blocks.append(('code', '''def agente_reflejo(posicion, sucio):
    if sucio:
        return 'aspirar'
    return 'derecha' if posicion == 'A' else 'izquierda'
'''))
p('Convención principal de puntuación: observar y puntuar el estado antes de ejecutar la acción de cada paso. El máximo es 2 × 1000 = 2000 puntos. Se calcula también la alternativa de puntuar después de actuar, porque ese desplazamiento temporal cambia los valores y debe quedar explícito. En ambas columnas se evalúan exactamente los mismos casos.')
p('S = suma, para t = 0,…,999, de [1 si A está limpia en s_t] + [1 si B está limpia en s_t].', 'formula')
table(['A inicial', 'B inicial', 'Inicio', 'Antes de actuar', 'Después de actuar'], [
    [r['A_inicial'], r['B_inicial'], r['inicio'], str(r['puntaje_antes']), str(r['puntaje_despues'])]
    for r in task2['resultados']
] + [['Promedio', '', '', '1998.25', '1999.25']], [1.25, 1.25, .65, 1.6, 1.6])
p('Resultados de la ejecución de tarea2_aspiradora.py. Los ocho casos tienen el mismo peso para el promedio. No se ha supuesto una distribución probabilística distinta sobre los estados iniciales.')
p('Ejemplo del puntaje mínimo: con A y B sucias e inicio en A, los primeros estados puntuados tienen 0, 1 y 1 casillas limpias. Las acciones son aspirar, derecha y aspirar; desde el estado siguiente hay dos casillas limpias. Por ello S = 0 + 1 + 1 + 997 × 2 = 1996. Si ambas estaban limpias, S = 2000. El programa deja las dos limpias en un máximo de tres acciones.')
p('El archivo tarea2_aspiradora.py incluye el simulador completo, la enumeración de los ocho casos, los cálculos de ambas convenciones, la exportación CSV/JSON y las verificaciones de estos resultados.')
p('Una vez limpio, el agente sigue alternando A y B: funciona para esta medida sin coste de movimiento, pero no sabe cuándo dejar de moverse. Una penalización energética cambiaría el problema y justificaría memoria para reconocer que ya limpió ambas casillas. Se resolvió el ejercicio solicitado, no la variante con penalización. [L1]')

heading('Tarea 3. Reglas complementarias de navegación')
p('La presentación 6 define un cuarto de 3 × 3, inicio (0,0,norte) y tres acciones: avanzar una casilla, aspirar y girar 90° a la derecha. Se debe recorrer continuamente el cuarto. Los ejes son x al este e y al norte; los giros siguen N → E → S → O → N. [P6, pp. 10–13]')
p('Ida requerida: (0,0) → (0,1) → (0,2) → (1,2) → (1,1) → (1,0) → (2,0) → (2,1) → (2,2). La diapositiva no fija el regreso; se propone (2,2) → (2,1) → (2,0) → (1,0) → (0,0), y un giro final para recuperar el norte. Todos los cambios de rumbo se hacen con giros físicos a la derecha.')
blocks.append(('image', ROOT / 'revision_tarea3' / 'recorrido_tarea3.png', 6.0))
p('Figura propia. Las flechas representan avances; los giros conservan la casilla. La ruta de regreso es una elección de esta solución.', 'small')
p('Extensión declarada: se añade el bit interno fase = ida o regreso, ausente de los tres predicados iniciales. No es una acción física nueva. La actualización de estado cambia a regreso al llegar a (2,2), y a ida al recuperar (0,0,norte).')
p('La distinción evita un conflicto real: en (1,0,oeste), durante la ida se debe girar para continuar a (2,0), pero en el regreso se debe avanzar hacia (0,0). Sin distinguir fases no se pueden asignar ambas decisiones a la misma percepción. Volver desde (0,1,sur) tampoco evita el problema conservando las reglas originales: en (0,1,norte) éstas fuerzan avanzar, y en (0,2,este) fuerzan salir al este antes de poder girar al sur. La solución es, por tanto, un agente con estado interno, y esta ampliación se hace explícita.')
p('La regla 1.1 tiene prioridad absoluta: en(x,y) y basura(x,y) → Do(aspira). Aspirar conserva posición, rumbo y fase. Cada regla de movimiento incluye que la casilla actual esté limpia; se aplica también esa guarda a 1.5, tal como exige la nota de la presentación. Las letras N, E, S y O significan norte, este, sur y oeste.')
table(['Regla original', 'Posición', 'Rumbo', 'Acción si está limpia'], [
    ['1.2', '(0,0)', 'N', 'avanzar'],
    ['1.3', '(0,1)', 'N', 'avanzar'],
    ['1.4', '(0,2)', 'N', 'girar'],
    ['1.5', '(0,2)', 'E', 'avanzar'],
], [1.3, 1.3, .9, 2.85])
p('Cada fila siguiente representa: en(x,y) y orientación(d) y no basura(x,y) y fase(f) → Do(acción). Así se escriben todas las reglas complementarias sin repetir innecesariamente los mismos predicados.')
rules = []
for phase, mapping in [('ida', task3_module.IDA), ('regreso', task3_module.REGRESO)]:
    for (x, y, orientation), (number, action) in mapping.items():
        rules.append([number, phase, f'({x},{y})', orientation, action])
assert len(rules) == 20
table(['Regla', 'Fase', 'Posición', 'Orientación', 'Acción'], rules, [.8, 1.25, 1.0, 1.55, 1.75])
p('Ejemplo de la regla 1.24 completa: en(1,0) y orientación(oeste) y no basura(1,0) y fase(regreso) → Do(avanzar). La regla 1.10 usa esa misma posición y rumbo, pero fase(ida), y produce girar. En (1,0), pasar de sur a este requiere tres giros a la derecha; ocurre lo mismo al pasar de este a norte en (2,0).')
p('Verificación ejecutada: tarea3_reglas.py comprueba las 2^9 = 512 distribuciones iniciales, dos ciclos cada una, con basura estática. En todas visita las nueve casillas, limpia, permanece dentro del cuarto y recupera (0,0,norte). Un ciclo limpio consume 12 avances + 12 giros = 24 acciones; con k casillas inicialmente sucias, el primero consume 24 + k (33 si las nueve están sucias). El siguiente ciclo limpio consume 24. La ruta no se presenta como óptima. El agente puede seguir repitiendo ciclos; sólo la simulación se limita a dos.')

heading('Referencias y materiales consultados')
p('Se consultaron las páginas y documentos enlazados el 3 de noviembre de 2026. “s.f.” indica que la página no muestra una fecha editorial estable; no se interpreta como una fecha de publicación. Las referencias P3, P5 y P6 son los materiales proporcionados para la clase. Los resultados de las tareas 2 y 3 proceden de los programas ejecutados incluidos en la entrega.', 'small')
for key, title, url in SOURCES:
    blocks.append(('reference', key, title, url))

heading('Archivos de apoyo')
p('tarea2_aspiradora.py reproduce los ocho casos y exporta sus puntajes. tarea3_reglas.py reproduce la verificación de las reglas; tarea3_verificacion.json conserva una traza de un ciclo limpio. La carpeta resultados incluye los datos de la tarea 2 y la figura del recorrido. Los dos programas usan únicamente la biblioteca estándar de Python; pueden ejecutarse con python tarea2_aspiradora.py y python tarea3_reglas.py.')

(ROOT / 'contenido_informe.json').write_text(json.dumps(
    {'blocks': blocks, 'sources': SOURCES}, ensure_ascii=False, default=str, indent=2), encoding='utf-8')


def add_link(paragraph, text, url):
    relation = paragraph.part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    link = OxmlElement('w:hyperlink')
    link.set(qn('r:id'), relation)
    run = OxmlElement('w:r')
    properties = OxmlElement('w:rPr')
    color = OxmlElement('w:color')
    color.set(qn('w:val'), '175F87')
    properties.append(color)
    run.append(properties)
    node = OxmlElement('w:t')
    node.text = text
    run.append(node)
    link.append(run)
    paragraph._p.append(link)


doc = Document()
doc.core_properties.title = 'Inteligencia Artificial · Tareas 1, 2 y 3'
doc.core_properties.subject = 'Estado del arte y ejercicios de agentes inteligentes'
doc.core_properties.author = ''
section = doc.sections[0]
section.page_width = Inches(8.5)
section.page_height = Inches(11)
section.top_margin = section.bottom_margin = Inches(.7)
section.left_margin = section.right_margin = Inches(.75)
normal = doc.styles['Normal']
normal.font.name = 'Arial'
normal.font.size = Pt(10)
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.line_spacing = 1.12
normal.paragraph_format.widow_control = True
for name, size in [('Title', 19), ('Subtitle', 11), ('Heading 1', 13), ('Heading 2', 11)]:
    doc.styles[name].font.name = 'Arial'
    doc.styles[name].font.size = Pt(size)
    doc.styles[name].font.color.rgb = RGBColor.from_string('17465A')
    doc.styles[name].paragraph_format.keep_with_next = True
footer = section.footer.paragraphs[0]
footer.alignment = 2
footer.add_run('Inteligencia Artificial · ')
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'PAGE')
footer._p.append(field)


def word_paragraph(text, role='body'):
    styles = {'title': 'Title', 'subtitle': 'Subtitle', 'heading': 'Heading 1', 'subheading': 'Heading 2'}
    paragraph = doc.add_paragraph(text, style=styles.get(role, 'Normal'))
    if role == 'small':
        for run in paragraph.runs:
            run.font.size = Pt(8.2)
            run.font.color.rgb = RGBColor.from_string('4B5563')
    return paragraph


for block in blocks:
    if block[0] == 'p':
        word_paragraph(block[1], block[2])
    elif block[0] == 'page':
        doc.add_page_break()
    elif block[0] == 'table':
        headers, rows, widths = block[1:]
        t = doc.add_table(rows=1, cols=len(headers))
        t.style = 'Light Shading Accent 1'
        t.autofit = False
        for i, text in enumerate(headers):
            t.rows[0].cells[i].text = text
        repeated = OxmlElement('w:tblHeader')
        t.rows[0]._tr.get_or_add_trPr().append(repeated)
        for row in rows:
            cells = t.add_row().cells
            for cell, text in zip(cells, row):
                cell.text = str(text)
        for row in t.rows:
            cant_split = OxmlElement('w:cantSplit')
            row._tr.get_or_add_trPr().append(cant_split)
            for i, cell in enumerate(row.cells):
                if widths:
                    cell.width = Inches(widths[i])
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_after = Pt(3)
                    paragraph.paragraph_format.space_before = Pt(3)
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
        doc.add_paragraph().paragraph_format.space_after = Pt(0)
    elif block[0] == 'code':
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_after = Pt(8)
        paragraph.paragraph_format.keep_together = True
        run = paragraph.add_run(block[1].rstrip())
        run.font.name = 'Consolas'
        run.font.size = Pt(8.3)
    elif block[0] == 'image':
        doc.add_picture(str(block[1]), width=Inches(block[2]))
    elif block[0] == 'reference':
        _, key, title, url = block
        paragraph = word_paragraph(f'[{key}] {title}', 'small')
        paragraph.paragraph_format.keep_together = True
        if url:
            paragraph.add_run('\n')
            add_link(paragraph, url, url)
doc.save(OUT / 'Tareas_1_2_3_Inteligencia_Artificial.docx')

PAGE_W, PAGE_H = letter
BODY_W = PAGE_W - 1.5 * inch
pdf_styles = {
    'body': ParagraphStyle('Body', fontName='DVS', fontSize=9.6, leading=13.2, spaceAfter=7, allowWidows=0, allowOrphans=0),
    'small': ParagraphStyle('Small', fontName='DVS', fontSize=7.8, leading=10.5, spaceAfter=6, textColor=colors.HexColor('#4B5563')),
    'title': ParagraphStyle('Title', fontName='DVS-Bold', fontSize=18, leading=23, spaceAfter=8, textColor=colors.HexColor('#17465A')),
    'subtitle': ParagraphStyle('Subtitle', fontName='DVS', fontSize=10.5, leading=15, spaceAfter=7),
    'heading': ParagraphStyle('Heading', fontName='DVS-Bold', fontSize=12.5, leading=17, spaceBefore=10, spaceAfter=8, keepWithNext=True, textColor=colors.HexColor('#17465A')),
    'subheading': ParagraphStyle('Subheading', fontName='DVS-Bold', fontSize=10.4, leading=15, spaceBefore=9, spaceAfter=5, keepWithNext=True),
    'formula': ParagraphStyle('Formula', fontName='DVS', fontSize=9.3, leading=13, spaceAfter=8, leftIndent=12),
    'cell': ParagraphStyle('Cell', fontName='DVS', fontSize=8.4, leading=11.1),
    'cellhead': ParagraphStyle('CellHead', fontName='DVS-Bold', fontSize=8.2, leading=11.1, textColor=colors.white),
}
story = []
for block in blocks:
    if block[0] == 'p':
        story.append(Paragraph(escape(block[1]), pdf_styles[block[2]]))
    elif block[0] == 'page':
        story.append(PageBreak())
    elif block[0] == 'table':
        headers, rows, widths = block[1:]
        data = [[Paragraph(escape(str(x)), pdf_styles['cellhead']) for x in headers]]
        data += [[Paragraph(escape(str(x)), pdf_styles['cell']) for x in row] for row in rows]
        col_widths = [v / sum(widths) * BODY_W for v in widths] if widths else None
        t = Table(data, colWidths=col_widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17465A')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F0F5F7'), colors.white]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('LINEBELOW', (0, -1), (-1, -1), .5, colors.HexColor('#CBD5DB')),
        ]))
        story.extend([KeepTogether([t]) if len(rows) <= 5 else t, Spacer(1, 8)])
    elif block[0] == 'code':
        style = ParagraphStyle('Code', fontName='DVS-Mono', fontSize=7.8, leading=11.0,
                               leftIndent=10, spaceBefore=3, spaceAfter=9)
        story.append(Preformatted(block[1].rstrip(), style))
    elif block[0] == 'image':
        from PIL import Image
        with Image.open(block[1]) as im:
            image_w, image_h = im.size
        width = block[2] * inch
        story.append(PDFImage(str(block[1]), width=width, height=width * image_h / image_w))
    elif block[0] == 'reference':
        _, key, title, url = block
        content = f'<b>[{key}]</b> ' + escape(title)
        if url:
            content += '<br/><link href="' + escape(url) + '" color="#175F87">' + escape(url) + '</link>'
        story.append(KeepTogether([Paragraph(content, pdf_styles['small'])]))


def footer_pdf(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#D7E0E4'))
    canvas.line(.75 * inch, .48 * inch, PAGE_W - .75 * inch, .48 * inch)
    canvas.setFont('DVS', 7.5)
    canvas.setFillColor(colors.HexColor('#56656C'))
    canvas.drawString(.75 * inch, .31 * inch, 'Inteligencia Artificial · Tareas 1, 2 y 3')
    canvas.drawRightString(PAGE_W - .75 * inch, .31 * inch, str(document.page))
    canvas.restoreState()


SimpleDocTemplate(str(OUT / 'Tareas_1_2_3_Inteligencia_Artificial.pdf'),
    pagesize=letter, leftMargin=.75 * inch, rightMargin=.75 * inch,
    topMargin=.65 * inch, bottomMargin=.65 * inch,
    title='Inteligencia Artificial · Tareas 1, 2 y 3', author='').build(
        story, onFirstPage=footer_pdf, onLaterPages=footer_pdf)

shutil.copy2(ROOT / 'tarea2_aspiradora.py', OUT / 'tarea2_aspiradora.py')
final_task3 = (ROOT / 'revision_tarea3' / 'simulacion_tarea3.py').read_text(encoding='utf-8')
final_task3 = final_task3.replace("with_name('verificacion_tarea3.json')", "with_name('tarea3_verificacion.json')")
(OUT / 'tarea3_reglas.py').write_text(final_task3, encoding='utf-8')
shutil.copy2(ROOT / 'revision_tarea3' / 'verificacion_tarea3.json', OUT / 'tarea3_verificacion.json')
shutil.copy2(ROOT / 'revision_tarea3' / 'recorrido_tarea3.png', RESULTS / 'recorrido_tarea3.png')
sources_text = '\n\n'.join(f'[{key}] {title}' + ('\n' + url if url else '') for key, title, url in SOURCES)
(OUT / 'fuentes.txt').write_text(sources_text, encoding='utf-8')

# Los archivos de apoyo son autocontenidos y no incluyen las presentaciones originales.
with zipfile.ZipFile(OUT / 'Entrega_Tareas_IA.zip', 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.suffix != '.zip':
            archive.write(path, path.name)
    for path in sorted(RESULTS.iterdir()):
        if path.is_file():
            archive.write(path, 'resultados/' + path.name)
print('Generados Word, PDF y ZIP con programas y resultados.')
print('Sistemas documentados:', len(fichas))
print('Tarea 2: 8 casos, promedio', task2['promedio_principal'])
print('Tarea 3: 512 configuraciones verificadas; 24 acciones por ciclo limpio.')

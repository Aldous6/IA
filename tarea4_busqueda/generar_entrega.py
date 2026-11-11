"""Entrega en Word y PDF de los ejercicios 3.6 y 3.7 proporcionados."""
from pathlib import Path
import json
import shutil
import sys
import zipfile
from xml.sax.saxutils import escape
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak, KeepTogether, Preformatted, Image as PDFImage
from soluciones import verificar

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'entrega'
OUT.mkdir(exist_ok=True)
resultado = verificar()
(ROOT / 'resultados/verificacion.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
blocks = []


def p(text, role='body'):
    blocks.append(('p', text, role))


def h(text):
    p(text, 'heading')


def table(headers, rows, widths):
    blocks.append(('table', headers, rows, widths))


p('Tarea 4 · Formulación de problemas y búsqueda', 'title')
p('Ejercicios 3.6 y 3.7 · Enunciados proporcionados de la tercera edición', 'subtitle')
p('Material de apoyo: presentación 7, páginas 19–20. Fecha: 3 de noviembre de 2026.', 'small')
p('En cada formulación se distinguen el estado, el estado inicial, la prueba de meta, los sucesores y el costo. Las posiciones o los datos que el enunciado no especifica se mantienen como parámetros. Las convenciones elegidas para concretar los modelos se declaran explícitamente. [1]')

h('3.6 a. Colorear un mapa con cuatro colores')
p('Datos: un grafo no dirigido (R,E), donde cada vértice representa una región. Se incluye (rᵢ,rⱼ) en E si las regiones comparten un tramo de frontera; se considera que tocarse sólo en un punto no las hace adyacentes. Los colores disponibles son {1,2,3,4}. Se fija un orden de las regiones r₁,…,rₙ.')
p('Estado: un vector c=(c₁,…,cₙ), con cᵢ∈{0,1,2,3,4}. El 0 significa sin colorear. Una asignación parcial es válida si los extremos ya coloreados de cada arista tienen colores distintos.')
p('Estado inicial: c₀=(0,…,0), con todas las regiones sin colorear. Prueba de meta: todos los componentes son distintos de 0 y, para toda arista (i,j)∈E, cᵢ≠cⱼ.')
p('Función de sucesores: elegir la primera región i con cᵢ=0. Para cada color k∈{1,2,3,4} que no esté usado por un vecino de i ya coloreado, producir c′ igual a c salvo c′ᵢ=k. Si no hay color admisible, ese estado no tiene sucesores. Fijar el orden no elimina ninguna coloración completa factible: sólo evita explorar órdenes equivalentes de asignación.')
p('Costo: 1 por colorear una región. El costo de un camino es el número de asignaciones realizadas; toda solución completa cuesta n. El procedimiento se implementa por búsqueda con retroceso. El código adjunto verifica una instancia planar K₄, que requiere cuatro colores.')

h('3.6 b. El mono, las dos cajas y las bananas')
p('Abstracción: el suelo se representa por un conjunto finito de zonas P y un grafo de movimientos entre ellas. Cada zona permite colocar y maniobrar con ambas cajas. Una zona no es un punto geométrico de volumen nulo. Las bananas están sobre la zona b, a 8 pies. Las cajas C1 y C2 miden 3 pies y el mono 3 pies. Se usa esa altura como alcance vertical del modelo; se abstraen la postura y los detalles de manipulación.')
p('Estado: s=(m,q,p₁,p₂,s₁,s₂,tiene). m es la zona del mono; q∈{suelo,C1,C2} es su soporte; pᵢ es la zona de Ci; sᵢ∈{suelo,la otra caja} es su soporte; tiene es un booleano que indica si posee las bananas. No se permiten ciclos de soporte. Si una caja está sobre otra, comparten zona. Si el mono está sobre una caja, comparte su zona y la parte superior de esa caja debe estar libre de la otra caja.')
p('Estado inicial elegido: (m₀,suelo,p₁₀,p₂₀,suelo,suelo,Falso). Así se concreta la situación inicial con mono y cajas en el suelo y cajas sin apilar; las zonas m₀,p₁₀,p₂₀ y b se suministran al definir la instancia porque el texto no las fija. Si se especifica otra disposición inicial, se reemplaza ese estado por la configuración válida correspondiente.')
p('Prueba de meta: tiene=Verdadero. La altura superior de una caja es 3 pies si descansa en el suelo y 6 si está sobre la otra. La base del mono está a 0 si está en el suelo o a la altura superior de su caja de soporte. Tomar las bananas requiere m=b y altura_base+3≥8: con una caja se llega a 6 pies, y con dos apiladas se puede alcanzar la altura de 8 pies.')
p('Sucesores: se aplican únicamente los operadores cuyas precondiciones se cumplen. “Libre” significa que no hay otra caja encima; en las operaciones de suelo el mono también debe estar en el suelo.')
table(['Operador', 'Precondición y efecto'], [
    ['Caminar a z', 'Mono en el suelo y z adyacente a m. Cambiar m a z.'],
    ['Empujar Ci a z', 'Mono en el suelo, m=pᵢ, Ci sobre el suelo y libre; z adyacente. Cambiar m y pᵢ a z.'],
    ['Apilar Ci sobre Cj', 'Mono en el suelo; m=pᵢ=pⱼ; ambas cajas sobre el suelo y libres. Cambiar sᵢ a Cj.'],
    ['Desapilar Ci', 'Mono en el suelo, misma zona; Ci está sobre Cj y libre. Poner Ci en el suelo de la misma zona.'],
    ['Subir a Ci', 'Mono en el suelo, m=pᵢ y Ci libre. Cambiar q a Ci; puede ser la caja superior de una pila.'],
    ['Bajar', 'Mono sobre una caja. Cambiar q a suelo, conservando la zona.'],
    ['Tomar bananas', 'tiene=Falso, m=b y altura_base+3≥8. Cambiar tiene a Verdadero.'],
], [1.45, 5.3])
p('Costo: 1 por operador. Los desplazamientos son entre zonas adyacentes y subir/bajar son operadores abstractos de escalada; el costo mide operaciones del modelo. Un plan general consiste en llevar ambas cajas a b, apilar una sobre la otra, subir a la superior y tomar las bananas. No se atribuye un número mínimo de movimientos al cuarto original, cuyas posiciones no se proporcionan.')

h('3.6 c. Identificar un registro ilegal')
p('Datos: registros completos r₁,…,rₙ y un oráculo falla(C), que procesa los registros cuyos índices están en C, con el mismo formato y contexto de validación, y devuelve Verdadero si alguno es ilegal. La independencia del procesamiento permite probar subconjuntos sin cambiar la validez de cada registro. No se cortan registros por la mitad.')
p('Estado: un conjunto ordenado no vacío C de índices candidatos, con la invariante falla(C)=Verdadero. Estado inicial: C₀={1,…,n}, ya conocido como fallido por el mensaje del programa. Prueba de meta: |C|=1. La invariante permite identificar su único candidato como ilegal.')
p('Función de sucesores: si |C|>1, dividirlo en mitades no vacías L y R, conservando el orden original. Ejecutar falla(L). Si devuelve Verdadero, el nuevo estado es L; si devuelve Falso, es R. En este último caso, la independencia y falla(C)=Verdadero garantizan que R contiene un registro ilegal. La respuesta del oráculo determina la transición.')
p('Costo: 1 por consulta adicional al programa; la falla inicial ya observada no se vuelve a cobrar. El tamaño de los candidatos se reduce aproximadamente a la mitad en cada consulta. Se necesitan como máximo ⌈log₂ n⌉ consultas adicionales. Esto cuenta invocaciones, no tiempo total de CPU: cada consulta puede procesar varios registros.')
p('No hace falta suponer que existe exactamente un registro ilegal: si hay varios, el procedimiento encuentra al menos uno. Para encontrarlos todos se deben explorar también las otras mitades que fallen. La implementación se verificó con las 255 distribuciones no vacías de registros ilegales en un archivo de ocho registros; siempre identifica uno y utiliza como máximo tres consultas.')

h('3.6 d. Jarras de 12, 8 y 3 galones')
p('Estado: s=(x₁₂,x₈,x₃), con cantidades enteras que satisfacen 0≤x₁₂≤12, 0≤x₈≤8 y 0≤x₃≤3. Para concretar la instancia se eligen inicialmente las tres jarras vacías: s₀=(0,0,0). Si se dan otros contenidos iniciales, se cambia s₀. Los trasvases se modelan hasta vaciar el origen o llenar el destino; así no se presupone la capacidad de medir directamente una cantidad parcial arbitraria.')
p('Prueba de meta: x₁₂=1 o x₈=1 o x₃=1. Basta que alguna jarra contenga exactamente un galón; el contenido de las otras no invalida esa medida.')
table(['Acción', 'Sucesor y condición'], [
    ['Llenar i', 'Si xᵢ<Cᵢ, sustituir xᵢ por Cᵢ.'],
    ['Vaciar i al suelo', 'Si xᵢ>0, sustituir xᵢ por 0.'],
    ['Verter i en j', 'Para i≠j, t=min(xᵢ,Cⱼ−xⱼ)>0. Sustituir xᵢ por xᵢ−t y xⱼ por xⱼ+t.'],
], [1.45, 5.3])
p('Costo: 1 por llenar, vaciar o trasvasar. El costo de un camino es su número de operaciones. La búsqueda en anchura encuentra una solución mínima porque todos los pasos tienen el mismo costo.')
table(['Paso', 'Acción', 'Estado (12,8,3)'], [
    ['0', 'Inicial', '(0,0,0)'],
    ['1', 'Llenar la jarra de 12', '(12,0,0)'],
    ['2', 'Verter de 12 a 8 hasta llenar la de 8', '(4,8,0)'],
    ['3', 'Verter de 12 a 3 hasta llenar la de 3', '(1,8,3)'],
], [.55, 4.3, 1.9])
p('Queda un galón en la jarra de 12. Tres operaciones son mínimas desde el estado vacío: tras una operación sólo se puede disponer de una capacidad completa; en una segunda, un trasvase puede dejar diferencias 12−8=4, 12−3=9 u 8−3=5, o conservar una capacidad completa al pasar de una jarra menor a otra mayor. Ninguna de esas cantidades es 1. La solución de tres pasos fue comprobada por BFS.')

h('3.7. Camino mínimo entre obstáculos poligonales convexos')
p('Se adopta la idealización de un robot puntual. El movimiento no puede entrar en el interior de los obstáculos, pero sí puede tocar sus vértices o recorrer sus bordes. Esta convención permite incluir los vecinos del mismo polígono y que exista una ruta mínima que se apoye en las esquinas. Los obstáculos de la escena se consideran disjuntos. [2–3]')
blocks.append(('image', ROOT / 'material/figura_331.png', 6.45))
p('Figura 3.31 del material proporcionado: presentación 7, página 20. Se conserva la geometría del dibujo; no se le atribuyen coordenadas ni distancias numéricas que el enunciado no indica.', 'small')

h('3.7 a. Cantidad de estados y caminos')
p('En la formulación continua, el estado es la posición (x,y) del robot fuera de los interiores prohibidos. Hay infinitos estados no numerables: el espacio contiene zonas completas del plano. También hay infinitos caminos factibles no numerables hacia G, porque se pueden variar continuamente sus puntos de paso y sus rodeos. No basta enumerar todas las posiciones o trayectorias posibles.')

h('3.7 b. Por qué bastan los vértices y cuántos estados quedan')
p('En una zona libre, un tramo curvo o un quiebre se puede acortar reemplazándolo por el segmento que une sus extremos. Un giro en el interior de una arista también se puede eliminar localmente, del lado libre del obstáculo. Por tanto, los cambios de dirección de una ruta mínima sólo necesitan ocurrir en vértices de obstáculos; entre ellos, y desde S o hacia G, los tramos son rectos. Recorrer parte de un borde es un caso permitido. [2]')
p('Se define V={S,G}∪{todos los vértices de los obstáculos}. Se conectan dos elementos de V si el segmento entre ellos no entra en ningún interior prohibido. Este es el grafo de visibilidad. Conserva al menos una ruta de longitud mínima del problema continuo bajo las convenciones anteriores. [2–3]')
table(['Obstáculo de la figura', 'Vértices'], [
    ['Pentágono superior izquierdo', '5'],
    ['Triángulo estrecho del centro-izquierda', '3'],
    ['Cuadrilátero superior, a la izquierda del rectángulo central', '4'],
    ['Rectángulo central', '4'],
    ['Cuadrilátero estrecho superior derecho', '4'],
    ['Triángulo inferior central', '3'],
    ['Hexágono inferior derecho', '6'],
    ['Rectángulo inferior izquierdo', '4'],
    ['Total de vértices de obstáculos', '33'],
    ['Total de estados con S y G', '35'],
], [5.6, 1.15])
p('En general, si hay N vértices distintos y S y G no coinciden con ellos, el espacio tiene N+2 estados. En esta figura son 35. Hay como máximo 35×34/2=595 aristas no dirigidas; sólo se mantienen las visibles. El grafo es finito, aunque sus recorridos con repeticiones pueden ser infinitos. Con costos positivos, una ruta mínima puede elegirse sin ciclos.')

h('3.7 c. Funciones de búsqueda y heurística')
table(['Componente', 'Definición implementable'], [
    ['Entrada', 'Coordenadas de S, G y vértices de cada polígono, ordenados por el contorno.'],
    ['Estado inicial', 'El vértice S. Se almacenan índices de vértices y sus coordenadas.'],
    ['GOAL_TEST(v)', 'Verdadero si el identificador de v es el de G.'],
    ['VISIBLE(v,w)', 'Verdadero si el segmento cerrado [v,w] no intersecta el interior de ningún obstáculo.'],
    ['ACTIONS(v)', '{p(w)−p(v) : w∈V, w≠v y VISIBLE(v,w)}. Devuelve vectores de desplazamiento.'],
    ['RESULT(v,a)', 'El vértice w cuya posición es p(v)+a; se conserva el destino asociado al vector.'],
    ['STEP_COST(v,a,w)', '‖a‖₂=√(aₓ²+aᵧ²), la longitud del segmento.'],
    ['Costo del camino', 'Suma de las longitudes de los segmentos recorridos.'],
    ['h(v)', '‖p(G)−p(v)‖₂, distancia euclidiana directa hasta G.'],
    ['Criterio de A*', 'Extraer el estado de menor f(v)=g(v)+h(v); terminar al extraer G.'],
], [1.5, 5.25])
p('ACTIONS incluye los vértices consecutivos de un mismo polígono: su arista se puede recorrer sobre el borde. Una diagonal que entra en el interior no es una acción válida. Un contacto tangencial con una esquina sí puede ser válido, pero cruzar por una esquina y continuar dentro sigue bloqueado. La prueba geométrica debe distinguir contacto de entrada al interior.')
blocks.append(('code', '''ACTIONS(v):
    devolver { p(w)-p(v) para w en V
               si w != v y VISIBLE(v,w) }

RESULT(v,a):
    devolver el destino asociado a (v,a)

STEP_COST(v,a,w): devolver norma_euclidiana(a)
h(v): devolver distancia_euclidiana(p(v),p(G))
'''))
p('La heurística es admisible: ignorar obstáculos no puede aumentar la distancia mínima. También es consistente por la desigualdad triangular: h(v)≤d(v,w)+h(w) para cada arista visible y h(G)=0. Por ello A* con estos costos y esta heurística puede encontrar una ruta de longitud mínima en el grafo. Se minimiza distancia, no número de segmentos.')
p('Para implementar VISIBLE con polígonos convexos, el código adjunto escribe cada punto del segmento como u+t(w−u), 0≤t≤1. Para cada polígono orientado en sentido antihorario, su interior satisface que el producto cruzado con cada arista sea estrictamente positivo. Si existe un intervalo de t que satisface todas esas desigualdades, el segmento entra en el interior y se descarta. La igualdad corresponde al borde y no bloquea por sí sola.')
p('Las coordenadas de la figura no vienen dadas como datos numéricos, por lo que aquí se define el algoritmo sin afirmar una longitud exacta para ese dibujo. La implementación utiliza coordenadas racionales e identificadores para evitar comparar vértices mediante sumas aproximadas de punto flotante. Las longitudes se evalúan numéricamente.')

h('Comprobaciones y archivos de apoyo')
p('soluciones.py contiene el coloreador por retroceso, los operadores del mono, la búsqueda del registro ilegal, las jarras por BFS y el grafo de visibilidad con A*. Se ejecutó y verificó una coloración de K₄, un plan válido del modelo del mono, las 255 distribuciones no vacías de registros ilegales en ocho registros, la solución mínima de tres pasos de las jarras y casos geométricos de borde, diagonal y tangencia.')
p('La prueba de A* usa un rectángulo sintético con vértices (0,0),(2,0),(2,2),(0,2), inicio (−1,1) y meta (3,1). Su resultado coincide con la longitud analítica 2+2√2. Ese ejemplo sirve para verificar el código; no es una digitalización de la figura 3.31. El archivo resultados/verificacion.json conserva los resultados. El programa usa sólo la biblioteca estándar de Python y se ejecuta con python soluciones.py.')

h('Referencias')
refs = [
    ('[1] Material proporcionado: 7-Solución de Problemas.pdf, páginas 19–20. Enunciados 3.6 y 3.7 y figura 3.31.', None),
    ('AIMA Exercises. Enunciado equivalente del ejercicio de formulación; la numeración del repositorio en línea es diferente.', 'https://aimacode.github.io/aima-exercises/search-exercises/ex_8/'),
    ('AIMA Exercises. Enunciado equivalente del problema de obstáculos poligonales.', 'https://aimacode.github.io/aima-exercises/search-exercises/ex_9/'),
    ('[2] De Berg, M., Cheong, O., Van Kreveld, M. y Overmars, M. (2008). Computational Geometry: Algorithms and Applications, 3.ª edición, sección 15.1, páginas impresas 324–325.', 'https://www.cs.cmu.edu/afs/cs/academic/class/15456-s14/Handouts/BKOS.pdf'),
    ('[3] Hauser, K. Robotic Systems. Motion Planning in Simple Geometric Spaces, apartado Visibility graph.', 'https://motion.cs.illinois.edu/RoboticSystems/GeometricMotionPlanning.html'),
]
for title, url in refs:
    blocks.append(('ref', title, url))
p('Fuentes web consultadas el 3 de noviembre de 2026. Las formulaciones, los costos elegidos y las comprobaciones son desarrollo de esta solución.', 'small')

(ROOT / 'contenido.json').write_text(json.dumps(blocks, ensure_ascii=False, default=str, indent=2), encoding='utf-8')


def link_docx(paragraph, title, url):
    rel = paragraph.part.relate_to(url, RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    element = OxmlElement('w:hyperlink'); element.set(qn('r:id'), rel)
    run = OxmlElement('w:r'); prop = OxmlElement('w:rPr')
    color = OxmlElement('w:color'); color.set(qn('w:val'), '175F87')
    prop.append(color); run.append(prop)
    text = OxmlElement('w:t'); text.text = title; run.append(text)
    element.append(run); paragraph._p.append(element)


doc = Document()
doc.core_properties.title = 'Tarea 4 · Ejercicios 3.6 y 3.7'
doc.core_properties.author = ''
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.left_margin = sec.right_margin = Inches(.7)
sec.top_margin = sec.bottom_margin = Inches(.65)
normal = doc.styles['Normal']
normal.font.name, normal.font.size = 'Arial', Pt(10)
normal.paragraph_format.line_spacing = 1.1
normal.paragraph_format.space_after = Pt(6)
normal.paragraph_format.widow_control = True
for name, size in [('Title', 18), ('Subtitle', 10.5), ('Heading 1', 12)]:
    doc.styles[name].font.name = 'Arial'; doc.styles[name].font.size = Pt(size)
    doc.styles[name].font.color.rgb = RGBColor.from_string('17465A')
    doc.styles[name].paragraph_format.keep_with_next = True
footer = sec.footer.paragraphs[0]; footer.alignment = 2
footer.add_run('Tarea 4 · ')
field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)
for b in blocks:
    if b[0] == 'p':
        role = b[2]
        para = doc.add_paragraph(b[1], style={'title':'Title','subtitle':'Subtitle','heading':'Heading 1'}.get(role,'Normal'))
        if role == 'small':
            for run in para.runs: run.font.size = Pt(8)
    elif b[0] == 'table':
        _, headers, rows, widths = b
        t = doc.add_table(rows=1, cols=len(headers)); t.style = 'Light Shading Accent 1'
        for cell, value in zip(t.rows[0].cells, headers): cell.text = value
        repeat = OxmlElement('w:tblHeader'); t.rows[0]._tr.get_or_add_trPr().append(repeat)
        for row in rows:
            for cell,value in zip(t.add_row().cells,row): cell.text = value
        for row in t.rows:
            no_split = OxmlElement('w:cantSplit'); row._tr.get_or_add_trPr().append(no_split)
            for cell,width in zip(row.cells,widths):
                cell.width = Inches(width)
                for para in cell.paragraphs:
                    para.paragraph_format.space_after = Pt(3)
                    for run in para.runs: run.font.size = Pt(9)
        doc.add_paragraph().paragraph_format.space_after = Pt(0)
    elif b[0] == 'page': doc.add_page_break()
    elif b[0] == 'image': doc.add_picture(str(b[1]), width=Inches(b[2]))
    elif b[0] == 'code':
        para = doc.add_paragraph(); para.paragraph_format.keep_together = True
        run = para.add_run(b[1].rstrip()); run.font.name = 'Consolas'; run.font.size = Pt(8.5)
    elif b[0] == 'ref':
        para = doc.add_paragraph(b[1]); para.paragraph_format.keep_together = True
        for run in para.runs: run.font.size = Pt(8)
        if b[2]: para.add_run('\n'); link_docx(para,b[2],b[2])
doc.save(OUT/'Tarea_4_Ejercicios_3_6_y_3_7.docx')

fontdir = Path(sys.prefix)/'Lib/site-packages/matplotlib/mpl-data/fonts/ttf'
for name,filename in [('DVS','DejaVuSans.ttf'),('DVS-Bold','DejaVuSans-Bold.ttf'),('DVS-Mono','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(fontdir/filename)))
pdfmetrics.registerFontFamily('DVS',normal='DVS',bold='DVS-Bold',italic='DVS',boldItalic='DVS-Bold')
styles = {
    'body':ParagraphStyle('Body',fontName='DVS',fontSize=9.6,leading=13,spaceAfter=7,allowWidows=0,allowOrphans=0),
    'small':ParagraphStyle('Small',fontName='DVS',fontSize=7.9,leading=10.5,spaceAfter=6),
    'title':ParagraphStyle('Title',fontName='DVS-Bold',fontSize=17,leading=22,spaceAfter=8,textColor=colors.HexColor('#17465A')),
    'subtitle':ParagraphStyle('Sub',fontName='DVS',fontSize=10,leading=14,spaceAfter=6),
    'heading':ParagraphStyle('Heading',fontName='DVS-Bold',fontSize=12,leading=16,spaceBefore=9,spaceAfter=7,keepWithNext=True,textColor=colors.HexColor('#17465A')),
    'cell':ParagraphStyle('Cell',fontName='DVS',fontSize=8.5,leading=11.3),
    'head':ParagraphStyle('Head',fontName='DVS-Bold',fontSize=8.5,leading=11.3,textColor=colors.white),
    'code':ParagraphStyle('Code',fontName='DVS-Mono',fontSize=8.1,leading=11.5,leftIndent=8,spaceAfter=8),
}
story = []
body_width = letter[0]-1.4*inch
for b in blocks:
    if b[0] == 'p': story.append(Paragraph(escape(b[1]),styles[b[2]]))
    elif b[0] == 'page': story.append(PageBreak())
    elif b[0] == 'image':
        from PIL import Image
        with Image.open(b[1]) as image: w,hp=image.size
        width=b[2]*inch; story.append(PDFImage(str(b[1]),width=width,height=width*hp/w))
    elif b[0] == 'table':
        _,headers,rows,widths=b
        data=[[Paragraph(escape(x),styles['head']) for x in headers]]
        data += [[Paragraph(escape(x),styles['cell']) for x in row] for row in rows]
        t=Table(data,colWidths=[x/sum(widths)*body_width for x in widths],repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#17465A')),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F0F5F7'),colors.white]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('LINEBELOW',(0,-1),(-1,-1),.4,colors.HexColor('#CDD7DD')),
        ]))
        story.extend([KeepTogether([t]) if len(rows)<=5 else t,Spacer(1,8)])
    elif b[0] == 'code': story.append(Preformatted(b[1].rstrip(),styles['code']))
    elif b[0] == 'ref':
        s=escape(b[1])
        if b[2]: s+='<br/><link href="'+escape(b[2])+'" color="#175F87">'+escape(b[2])+'</link>'
        story.append(KeepTogether([Paragraph(s,styles['small'])]))


def pie(canvas,document):
    canvas.saveState(); canvas.setFont('DVS',7.5)
    canvas.setFillColor(colors.HexColor('#536570'))
    canvas.drawString(.7*inch,.3*inch,'Tarea 4 · Ejercicios 3.6 y 3.7')
    canvas.drawRightString(letter[0]-.7*inch,.3*inch,str(document.page)); canvas.restoreState()


SimpleDocTemplate(str(OUT/'Tarea_4_Ejercicios_3_6_y_3_7.pdf'),pagesize=letter,
    leftMargin=.7*inch,rightMargin=.7*inch,topMargin=.6*inch,bottomMargin=.6*inch,
    title='Tarea 4 · Ejercicios 3.6 y 3.7',author='').build(story,onFirstPage=pie,onLaterPages=pie)
shutil.copy2(ROOT/'soluciones.py',OUT/'soluciones.py')
shutil.copy2(ROOT/'resultados/verificacion.json',OUT/'verificacion.json')
with zipfile.ZipFile(OUT/'Entrega_Tarea_4.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for name in ['Tarea_4_Ejercicios_3_6_y_3_7.docx','Tarea_4_Ejercicios_3_6_y_3_7.pdf','soluciones.py','verificacion.json']:
        z.write(OUT/name,name)
    z.write(ROOT/'material/figura_331.png','figura_331.png')
print('Generados Word, PDF y paquete de la Tarea 4.')

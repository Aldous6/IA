"""Extrae texto de los registros de una presentación PowerPoint binaria."""
from pathlib import Path
import struct
import olefile

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'presentaciones/10-Sistemas de procesamiento del conocimiento-C5.ppt'
TARGET = ROOT / 'material/presentacion10_texto.txt'
TARGET.parent.mkdir(parents=True, exist_ok=True)

with olefile.OleFileIO(SOURCE) as archivo:
    stream = archivo.openstream('PowerPoint Document').read()

textos = []
def leer(inicio, fin):
    posicion = inicio
    while posicion + 8 <= fin:
        opciones, tipo, longitud = struct.unpack_from('<HHI', stream, posicion)
        contenido = posicion + 8
        limite = contenido + longitud
        if limite > fin:
            break
        if tipo == 4000:
            textos.append(stream[contenido:limite].decode('utf-16-le', errors='replace'))
        elif tipo == 4008:
            textos.append(stream[contenido:limite].decode('cp1252', errors='replace'))
        elif opciones & 15 == 15:
            leer(contenido, limite)
        posicion = limite

leer(0, len(stream))
TARGET.write_text('\n\n'.join(textos), encoding='utf-8')
print(f'Extraídos {len(textos)} registros de texto.')

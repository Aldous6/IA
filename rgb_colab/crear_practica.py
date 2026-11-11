"""Genera una práctica autocontenida de separación RGB para Google Colab."""
from pathlib import Path
import base64
import json
import os
import sys
import textwrap
import nbformat as nbf

ROOT = Path(__file__).resolve().parent
SOURCE = Path(r'C:\Users\Aldo\Desktop\SID TE AMO.jpeg')
NOTEBOOK = ROOT / 'Separacion_RGB_Sid.ipynb'
encoded = base64.b64encode(SOURCE.read_bytes()).decode('ascii')


def md(text):
    return nbf.v4.new_markdown_cell(textwrap.dedent(text).strip())


def code(text, **metadata):
    return nbf.v4.new_code_cell(textwrap.dedent(text).strip(), metadata=metadata)


cells = [
    md('''
        En esta práctica separamos la foto de Sid en sus tres canales: rojo (R),
        verde (G) y azul (B). La foto está incluida en el notebook para poder
        repetir la práctica en Colab con **Entorno de ejecución → Ejecutar todas**.
    '''),
    code('''
        import numpy as np
        import matplotlib.pyplot as plt
        from PIL import Image
    '''),
    md('''
        La siguiente celda carga la foto incluida. Después trabajaremos con una
        matriz: cada píxel tiene tres valores, en el orden rojo, verde y azul.
        En esta imagen de 8 bits, cada canal toma valores entre 0 y 255.
    '''),
    code(
        '# @title Cargar la foto de Sid (incluida)\n'
        'import base64\n'
        'from io import BytesIO\n\n'
        f'foto_base64 = "{encoded}"\n'
        'imagen = Image.open(BytesIO(base64.b64decode(foto_base64))).convert("RGB")\n'
        'print(f"Foto cargada: {imagen.width} × {imagen.height} píxeles.")',
        cellView='form', jupyter={'source_hidden': True},
    ),
    md('''
        `[:, :, 0]` selecciona el rojo, `[:, :, 1]` el verde y `[:, :, 2]` el azul.
        Los dos primeros `:` conservan todas las filas y columnas. Para ver cada
        canal con su color, mantenemos sus valores y dejamos los otros dos en cero.
    '''),
    code('''
        original = np.array(imagen)

        R = original[:, :, 0]
        G = original[:, :, 1]
        B = original[:, :, 2]

        rojo = np.zeros_like(original)
        rojo[:, :, 0] = R

        verde = np.zeros_like(original)
        verde[:, :, 1] = G

        azul = np.zeros_like(original)
        azul[:, :, 2] = B
    '''),
    code('''
        fig, ejes = plt.subplots(2, 2, figsize=(9, 8))
        fotos = [original, rojo, verde, azul]
        titulos = ['Original', 'Canal rojo (R)', 'Canal verde (G)', 'Canal azul (B)']

        for eje, foto, titulo in zip(ejes.flat, fotos, titulos):
            eje.imshow(foto)
            eje.set_title(titulo)
            eje.axis('off')

        plt.tight_layout()
        plt.savefig('RGB_Sid.png', dpi=150)
        plt.show()
    '''),
    md('''
        Guardamos los tres canales como imágenes PNG y comprobamos que su suma
        recupera exactamente la imagen original. En Colab puedes descargar las
        imágenes desde el panel **Archivos**.
    '''),
    code('''
        Image.fromarray(rojo).save('canal_rojo.png')
        Image.fromarray(verde).save('canal_verde.png')
        Image.fromarray(azul).save('canal_azul.png')

        reconstruida = rojo + verde + azul
        assert np.array_equal(original, reconstruida)
        print('Comprobación correcta: R + G + B reproduce la imagen original.')
        print('Guardados: canal_rojo.png, canal_verde.png, canal_azul.png y RGB_Sid.png.')
    '''),
    md('''
        Se obtuvieron tres imágenes que conservan únicamente su componente rojo,
        verde o azul. Al reunirlas recuperamos todos los colores de la foto.
        Referencias: [modos y canales en Pillow](https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes)
        e [indexación de matrices en NumPy](https://numpy.org/doc/stable/user/basics.indexing.html).
    '''),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python'},
    'colab': {'name': NOTEBOOK.name, 'provenance': []},
})
nbf.write(nb, NOTEBOOK)
print(f'Creado: {NOTEBOOK.name}', flush=True)

if '--ejecutar' in sys.argv:
    from nbclient import NotebookClient

    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    jupyter_path = ROOT / '.jupyter'
    kernel = jupyter_path / 'kernels' / 'rgb-local'
    kernel.mkdir(parents=True, exist_ok=True)
    (kernel / 'kernel.json').write_text(json.dumps({
        'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
        'display_name': 'RGB local', 'language': 'python',
    }), encoding='utf-8')
    os.environ['JUPYTER_PATH'] = str(jupyter_path)
    os.environ['JUPYTER_RUNTIME_DIR'] = str(jupyter_path / 'runtime')
    os.environ['IPYTHONDIR'] = str(ROOT / '.ipython')
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        NotebookClient(nb, timeout=120, kernel_name='rgb-local',
            resources={'metadata': {'path': str(ROOT)}}).execute()
    finally:
        nbf.write(nb, NOTEBOOK)
    nbf.validate(nb)
    assert not [o for c in nb.cells for o in c.get('outputs', [])
                if o.output_type == 'error']
    print('Notebook ejecutado completo, sin errores.', flush=True)

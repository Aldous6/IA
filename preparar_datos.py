from pathlib import Path
import hashlib
import time
import urllib.request
import urllib.error
import zipfile

root = Path(__file__).resolve().parent / 'datos'
root.mkdir(parents=True, exist_ok=True)
dest = root / 'caltech-101.zip'
urls = [
    'https://data.caltech.edu/records/mzrjq-6wc02/files/caltech-101.zip?download=1&fresh=' + str(int(time.time())),
    'https://data.caltech.edu/api/records/mzrjq-6wc02/files/caltech-101.zip/content',
    'https://data.caltech.edu/records/20086/files/caltech-101.zip?download=1',
]
for url in urls:
    try:
        print('Intentando', url, flush=True)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=120) as response, dest.open('wb') as out:
            print('HTTP', response.status, response.headers.get('Content-Type'), flush=True)
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
        digest = hashlib.md5(dest.read_bytes()).hexdigest()
        print('bytes', dest.stat().st_size, 'md5', digest, flush=True)
        if digest != '3138e1922a9193bfa496528edbbc45d0':
            raise ValueError('El archivo no coincide con el MD5 publicado por CaltechDATA')
        print(zipfile.ZipFile(dest).namelist()[:40], flush=True)
        break
    except Exception as exc:
        print(type(exc).__name__, str(exc), flush=True)
else:
    raise RuntimeError('No se pudo descargar el archivo oficial')

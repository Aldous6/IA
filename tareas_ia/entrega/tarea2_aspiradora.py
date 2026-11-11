"""Tarea 2: agente de reflejo simple, ocho estados y puntajes reproducibles."""
from itertools import product
from pathlib import Path
import csv
import json


def agente_reflejo(posicion, sucio):
    """Sólo recibe la posición y la suciedad local; no almacena memoria."""
    if sucio:
        return 'aspirar'
    return 'derecha' if posicion == 'A' else 'izquierda'


def simular(inicio, sucio_a, sucio_b, pasos=1000):
    suciedad = {'A': sucio_a, 'B': sucio_b}
    posicion = inicio
    antes = despues = 0
    limpieza_completa = 0 if not any(suciedad.values()) else None
    primeras_acciones = []
    for tiempo in range(1, pasos + 1):
        # Convención principal: medir el estado observado antes de actuar.
        antes += sum(not sucio for sucio in suciedad.values())
        accion = agente_reflejo(posicion, suciedad[posicion])
        if len(primeras_acciones) < 6:
            primeras_acciones.append(accion)
        if accion == 'aspirar':
            suciedad[posicion] = False
        elif accion == 'derecha':
            posicion = 'B'
        else:
            posicion = 'A'
        # Se calcula también la convención alternativa para hacerla explícita.
        despues += sum(not sucio for sucio in suciedad.values())
        if limpieza_completa is None and not any(suciedad.values()):
            limpieza_completa = tiempo
    assert not any(suciedad.values())
    return {
        'inicio': inicio,
        'A_inicial': 'sucia' if sucio_a else 'limpia',
        'B_inicial': 'sucia' if sucio_b else 'limpia',
        'puntaje_antes': antes,
        'puntaje_despues': despues,
        'paso_limpieza_completa': limpieza_completa,
        'primeras_acciones': ', '.join(primeras_acciones),
    }


def resolver(carpeta=None):
    filas = [simular(inicio, a, b)
             for a, b, inicio in product([False, True], [False, True], ['A', 'B'])]
    # Valores analíticos: pérdidas de 0, 1, 2 o 4 respecto al máximo 2000.
    esperados = [2000, 2000, 1998, 1999, 1999, 1998, 1996, 1996]
    assert [r['puntaje_antes'] for r in filas] == esperados
    for fila in filas:
        limpios_iniciales = int(fila['A_inicial'] == 'limpia') + int(fila['B_inicial'] == 'limpia')
        assert fila['puntaje_despues'] - fila['puntaje_antes'] == 2 - limpios_iniciales
        assert fila['paso_limpieza_completa'] <= 3
    promedio = sum(r['puntaje_antes'] for r in filas) / len(filas)
    promedio_despues = sum(r['puntaje_despues'] for r in filas) / len(filas)
    assert promedio == 1998.25 and promedio_despues == 1999.25
    resumen = {
        'casos': len(filas), 'pasos_por_caso': 1000, 'maximo': 2000,
        'convencion_principal': 'Puntuar el estado antes de la acción en cada paso',
        'promedio_principal': promedio, 'promedio_alternativo_despues': promedio_despues,
        'maximo_pasos_para_limpiar': max(r['paso_limpieza_completa'] for r in filas),
        'resultados': filas,
    }
    if carpeta is not None:
        carpeta = Path(carpeta)
        carpeta.mkdir(parents=True, exist_ok=True)
        with (carpeta / 'tarea2_resultados.csv').open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(filas[0]))
            writer.writeheader()
            writer.writerows(filas)
        (carpeta / 'tarea2_resultados.json').write_text(
            json.dumps(resumen, ensure_ascii=False, indent=2), encoding='utf-8')
    return resumen


if __name__ == '__main__':
    resultado = resolver(Path(__file__).resolve().parent / 'resultados')
    for fila in resultado['resultados']:
        print(fila)
    print('Promedio antes de actuar:', resultado['promedio_principal'])
    print('Promedio después de actuar:', resultado['promedio_alternativo_despues'])

"""Traza reproducible de la Tarea 7. Sólo usa la biblioteca estándar de Python."""
from pathlib import Path
import json

REGLAS = [
    {'id': 'R1', 'si': ['p', 'q'], 'entonces': ['objetivo']},
    {'id': 'R2', 'si': ['r', 's'], 'entonces': ['p']},
    {'id': 'R3', 'si': ['w', 'r'], 'entonces': ['q']},
    {'id': 'R4', 'si': ['t', 'u'], 'entonces': ['q']},
    {'id': 'R5', 'si': ['v'], 'entonces': ['s']},
    {'id': 'R6', 'si': ['Inicio'], 'entonces': ['v', 'r', 'q']},
]
ORDEN_HECHOS = ['Inicio', 'v', 'r', 'q', 's', 'p', 'objetivo', 'w', 't', 'u']


def mostrar_mt(mt):
    return [x for x in ORDEN_HECHOS if x in mt]


def hacia_adelante():
    mt, disparadas = {'Inicio'}, []
    traza = []
    inspecciones = 0
    while 'objetivo' not in mt:
        revisadas = []
        elegida = None
        for regla in REGLAS:
            inspecciones += 1
            revisadas.append(regla['id'])
            if regla['id'] in disparadas or set(regla['entonces']).issubset(mt):
                continue
            if all(hecho in mt for hecho in regla['si']):
                elegida = regla
                break  # Primera aplicable; no se construye toda la agenda.
        if elegida is None:
            return {'exito': False, 'mt': mostrar_mt(mt), 'traza': traza,
                    'disparadas': disparadas, 'inspecciones': inspecciones}
        anterior = mostrar_mt(mt)
        nuevos = [h for h in elegida['entonces'] if h not in mt]
        mt.update(elegida['entonces'])
        disparadas.append(elegida['id'])
        traza.append({'paso': len(traza) + 1, 'mt_antes': anterior,
                      'reglas_revisadas': revisadas, 'regla': elegida['id'],
                      'nuevos': nuevos, 'mt_despues': mostrar_mt(mt)})
    return {'exito': True, 'mt': mostrar_mt(mt), 'traza': traza,
            'disparadas': disparadas, 'inspecciones': inspecciones}


def hacia_atras():
    mt, disparadas, seleccionadas = {'Inicio'}, [], []
    traza, consultas = [], []
    inspecciones = 0

    def probar(meta, activas):
        nonlocal inspecciones
        consultas.append(meta)
        if meta in mt:
            traza.append({'tipo': 'hecho', 'meta': meta,
                          'mt': mostrar_mt(mt)})
            return True
        if meta in activas:
            return False
        for regla in REGLAS:
            inspecciones += 1
            if meta not in regla['entonces'] or regla['id'] in disparadas:
                continue
            seleccionadas.append(regla['id'])
            traza.append({'tipo': 'seleccion', 'meta': meta, 'regla': regla['id'],
                          'submetas': regla['si'], 'mt': mostrar_mt(mt)})
            if all(probar(h, activas | {meta}) for h in regla['si']):
                nuevos = [h for h in regla['entonces'] if h not in mt]
                mt.update(regla['entonces'])  # R6 incorpora sus TRES efectos.
                disparadas.append(regla['id'])
                traza.append({'tipo': 'disparo', 'meta': meta, 'regla': regla['id'],
                              'nuevos': nuevos, 'mt': mostrar_mt(mt)})
                return True
        return False

    exito = probar('objetivo', set())
    return {'exito': exito, 'mt': mostrar_mt(mt), 'traza': traza,
            'seleccionadas': seleccionadas, 'disparadas': disparadas,
            'consultas_mt': consultas, 'inspecciones': inspecciones}


def resolver():
    a, b = hacia_adelante(), hacia_atras()
    esperadas = ['R6', 'R5', 'R2', 'R1']
    assert a['exito'] and b['exito']
    assert a['disparadas'] == b['disparadas'] == esperadas
    assert b['seleccionadas'] == ['R1', 'R2', 'R6', 'R5']
    assert a['mt'] == b['mt'] == ORDEN_HECHOS[:7]
    assert a['inspecciones'] == b['inspecciones'] == 14
    assert len(b['consultas_mt']) == 7
    # Cada disparo debe estar justificado por hechos ya presentes; no se
    # invierten implicaciones al efectuar la búsqueda hacia atrás.
    for resultado in [a, b]:
        mt = {'Inicio'}
        por_id = {r['id']: r for r in REGLAS}
        for identificador in resultado['disparadas']:
            regla = por_id[identificador]
            assert set(regla['si']).issubset(mt)
            assert not set(regla['entonces']).issubset(mt)
            mt.update(regla['entonces'])
        assert mostrar_mt(mt) == resultado['mt']
    return {'reglas': REGLAS, 'mt_inicial': ['Inicio'], 'meta': 'objetivo',
            'adelante': a, 'atras': b,
            'metricas': {'disparos_adelante': len(a['disparadas']),
                         'disparos_atras': len(b['disparadas']),
                         'inspecciones_adelante': a['inspecciones'],
                         'inspecciones_atras': b['inspecciones'],
                         'hechos_nuevos_ambos': 6}}


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    out = root / 'resultados'
    out.mkdir(exist_ok=True)
    resultado = resolver()
    (out / 'trazas.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Trazas verificadas: 4 disparos, 14 inspecciones por método y la misma MT final.')

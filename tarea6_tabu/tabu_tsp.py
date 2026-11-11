"""Tabú por recencia: pares de identidades de ciudades, horizonte fijo y aspiración."""
from itertools import combinations
import math
import random
import time
import numpy as np
from templado_base import longitud

EPS = 1e-12


def atributo_intercambio(ruta, i, j):
    return tuple(sorted((ruta[i], ruta[j])))


def admision(costo, mejor_global, atributo, iteracion, vencimientos):
    es_tabu = iteracion <= vencimientos.get(atributo, -1)
    aspiracion = es_tabu and costo < mejor_global - EPS
    return not es_tabu or aspiracion, es_tabu, aspiracion


def busqueda_tabu(distancias, semilla=0, horizonte=5, presupuesto=91700):
    d = np.asarray(distancias, dtype=float).tolist()
    n = len(d)
    if n < 3 or any(len(row) != n for row in d):
        raise ValueError('Se requiere una matriz cuadrada de al menos tres ciudades.')
    if horizonte < 1 or presupuesto < 1:
        raise ValueError('Horizonte y presupuesto deben ser positivos.')
    ruta = list(range(n))
    random.Random(semilla).shuffle(ruta)
    # Se usa un generador independiente sólo para el último barrido parcial.
    rng_parcial = random.Random(1_000_003 + semilla)
    inicial = ruta.copy()
    costo = longitud(ruta, d)
    costo_inicial = costo
    mejor_ruta, mejor_costo = ruta.copy(), costo
    pares = list(combinations(range(n), 2))
    vencimientos = {}
    evaluaciones = iteracion = peores = aspiraciones = excluidos = 0
    historial = [{'iteracion': 0, 'evaluaciones': 0, 'costo_actual': costo,
                  'mejor_costo': mejor_costo, 'tabues_activos': 0}]
    traza = []
    motivo = 'presupuesto'
    iniciado = time.perf_counter()
    while evaluaciones < presupuesto:
        iteracion += 1
        vencimientos = {a: t for a, t in vencimientos.items() if t >= iteracion}
        restantes = presupuesto - evaluaciones
        candidatos = pares if restantes >= len(pares) else rng_parcial.sample(pares, restantes)
        elegido = None
        mejor_vecino = math.inf
        atributo_elegido = None
        asp_elegida = False
        era_tabu_elegido = False
        # La aspiración se contrasta con el mejor global anterior al barrido.
        referencia_global = mejor_costo
        for i, j in candidatos:
            vecino = ruta.copy()
            vecino[i], vecino[j] = vecino[j], vecino[i]
            costo_vecino = longitud(vecino, d)
            evaluaciones += 1  # Incluye los tabú evaluados para comprobar aspiración.
            atributo = atributo_intercambio(ruta, i, j)
            permitido, era_tabu, asp = admision(costo_vecino, referencia_global, atributo,
                                               iteracion, vencimientos)
            if not permitido:
                excluidos += 1
                continue
            mejor = costo_vecino < mejor_vecino - EPS
            empate = abs(costo_vecino - mejor_vecino) <= EPS
            if elegido is None or mejor or (empate and atributo < atributo_elegido):
                elegido, mejor_vecino, atributo_elegido = vecino, costo_vecino, atributo
                asp_elegida, era_tabu_elegido = asp, era_tabu
        if elegido is None:
            motivo = 'sin_vecino_admisible'
            break
        delta = mejor_vecino - costo
        peores += int(delta > EPS)
        aspiraciones += int(asp_elegida)
        ruta, costo = elegido, mejor_vecino
        # Un cambio aceptado en k queda prohibido en k+1,...,k+horizonte.
        vencimientos[atributo_elegido] = iteracion + horizonte
        if costo < mejor_costo - EPS:
            mejor_ruta, mejor_costo = ruta.copy(), costo
        historial.append({'iteracion': iteracion, 'evaluaciones': evaluaciones,
                          'costo_actual': costo, 'mejor_costo': mejor_costo,
                          'tabues_activos': len(vencimientos)})
        if len(traza) < 10:
            traza.append({'iteracion': iteracion, 'evaluaciones': evaluaciones,
                          'ciudades_intercambiadas_base0': atributo_elegido,
                          'tabu_hasta_inclusive': vencimientos[atributo_elegido],
                          'aspiracion': asp_elegida, 'era_tabu': era_tabu_elegido,
                          'costo_actual': costo, 'mejor_costo': mejor_costo})
    segundos = time.perf_counter() - iniciado
    assert sorted(mejor_ruta) == list(range(n))
    assert math.isclose(longitud(mejor_ruta, d), mejor_costo, rel_tol=0, abs_tol=1e-8)
    assert all(b['mejor_costo'] <= a['mejor_costo'] for a, b in zip(historial, historial[1:]))
    return {'semilla': semilla, 'ruta_inicial': inicial, 'costo_inicial': costo_inicial,
            'mejor_ruta': mejor_ruta, 'mejor_costo': mejor_costo,
            'ruta_final': ruta, 'costo_final': costo, 'evaluaciones': evaluaciones,
            'iteraciones': len(historial) - 1, 'empeoramientos_aceptados': peores,
            'aspiraciones': aspiraciones, 'vecinos_excluidos': excluidos,
            'segundos': segundos, 'motivo_parada': motivo,
            'historial': historial, 'traza': traza}


def verificar_tabu():
    clave = (2, 6)
    memoria = {clave: 7}  # Cambio en k=2, horizonte5.
    assert [t for t in range(3, 9) if admision(11, 10, clave, t, memoria)[1]] == [3, 4, 5, 6, 7]
    assert admision(9, 10, clave, 3, memoria) == (True, True, True)
    assert admision(10, 10, clave, 3, memoria) == (False, True, False)
    assert admision(11, 10, clave, 8, memoria) == (True, False, False)
    ruta = [7, 3, 5, 6, 1, 2, 4, 8]
    assert atributo_intercambio(ruta, 3, 5) == (2, 6)
    ruta[3], ruta[5] = ruta[5], ruta[3]
    assert atributo_intercambio(ruta, 3, 5) == (2, 6)
    from templado_base import matriz_distancias
    d = matriz_distancias([[0, 0], [1, 0], [1, 1], [0, 1]])
    r = busqueda_tabu(d, horizonte=2, presupuesto=31)
    assert r['evaluaciones'] == 31 and r['motivo_parada'] == 'presupuesto'
    assert r['iteraciones'] == 6  # Cinco barridos de6 y uno parcial de1.
    assert math.isclose(r['mejor_costo'], 4.0, abs_tol=1e-12)

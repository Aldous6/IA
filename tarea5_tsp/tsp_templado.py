"""Tarea 5: TSP de 15 ciudades con vecindad por intercambio de dos posiciones."""
from pathlib import Path
import csv
import json
import math
import random
import time
import numpy as np


def matriz_distancias(coordenadas):
    puntos = np.asarray(coordenadas, dtype=float)
    diferencias = puntos[:, None, :] - puntos[None, :, :]
    return np.sqrt(np.sum(diferencias ** 2, axis=2))


def longitud(ruta, distancias):
    """Longitud del ciclo: incluye la vuelta de la última ciudad a la primera."""
    return sum(distancias[a][b] for a, b in zip(ruta, ruta[1:] + ruta[:1]))


def vecino_intercambio(vc, generador):
    """Elegir dos posiciones distintas; el vecino conserva las 15 ciudades."""
    i, j = generador.sample(range(len(vc)), 2)
    vn = vc.copy()
    vn[i], vn[j] = vn[j], vn[i]
    return vn, i, j


def probabilidad_aceptar(delta, temperatura):
    """Mejoras estrictas: 1. Resto: logística de clase, para minimización."""
    if temperatura <= 0:
        raise ValueError('La temperatura debe ser positiva.')
    if delta < 0:
        return 1.0
    # Equivale a 1/(1+exp(delta/T)), evitando desbordar el exponencial.
    z = math.exp(-delta / temperatura)
    return z / (1.0 + z)


def templado_simulado(distancias, semilla=0, t_inicial=100.0, t_minima=0.01,
                     enfriamiento=0.99, vecinos_por_temperatura=100):
    if not (0 < t_minima < t_inicial and 0 < enfriamiento < 1):
        raise ValueError('Se requiere 0 < Tmin < T0 y 0 < alpha < 1.')
    if vecinos_por_temperatura < 1:
        raise ValueError('Se requiere al menos un vecino por temperatura.')
    d = np.asarray(distancias, dtype=float).tolist()
    n = len(d)
    if n < 2 or any(len(fila) != n for fila in d):
        raise ValueError('La matriz debe ser cuadrada, con al menos dos ciudades.')
    rng = random.Random(semilla)
    vc = list(range(n))
    rng.shuffle(vc)
    ruta_inicial = vc.copy()
    costo_actual = longitud(vc, d)
    costo_inicial = costo_actual
    mejor_ruta, mejor_costo = vc.copy(), costo_actual
    temperatura = t_inicial
    propuestas = aceptadas = empeoramientos = mejoras = empates = 0
    nivel = 0
    historial = [{
        'nivel': 0, 'iteracion': 0, 'temperatura': temperatura,
        'costo_actual': costo_actual, 'mejor_costo': mejor_costo,
        'aceptados_nivel': 0, 'empeoramientos_aceptados_nivel': 0,
    }]
    ejemplo_intercambio = None
    inicio = time.perf_counter()
    while temperatura >= t_minima:
        aceptados_nivel = peores_nivel = 0
        for _ in range(vecinos_por_temperatura):
            vn, i, j = vecino_intercambio(vc, rng)
            costo_nuevo = longitud(vn, d)
            delta = costo_nuevo - costo_actual
            p = probabilidad_aceptar(delta, temperatura)
            # El azar se consulta sólo cuando no hay una mejora estricta.
            u = None if delta < 0 else rng.random()
            aceptar = delta < 0 or u < p
            propuestas += 1
            if ejemplo_intercambio is None:
                ejemplo_intercambio = {
                    'vc': vc.copy(), 'vn': vn.copy(), 'posiciones_base0': [i, j],
                    'costo_vc': costo_actual, 'costo_vn': costo_nuevo,
                    'delta': delta, 'temperatura': temperatura, 'p': p,
                    'u': u, 'aceptado': aceptar,
                }
            if aceptar:
                vc, costo_actual = vn, costo_nuevo
                aceptadas += 1
                aceptados_nivel += 1
                if delta > 0:
                    empeoramientos += 1
                    peores_nivel += 1
                elif delta < 0:
                    mejoras += 1
                else:
                    empates += 1
                if costo_actual < mejor_costo:
                    mejor_ruta, mejor_costo = vc.copy(), costo_actual
        nivel += 1
        historial.append({
            'nivel': nivel, 'iteracion': propuestas, 'temperatura': temperatura,
            'costo_actual': costo_actual, 'mejor_costo': mejor_costo,
            'aceptados_nivel': aceptados_nivel,
            'empeoramientos_aceptados_nivel': peores_nivel,
        })
        temperatura *= enfriamiento
    segundos = time.perf_counter() - inicio
    assert sorted(mejor_ruta) == list(range(n))
    assert math.isclose(longitud(mejor_ruta, d), mejor_costo, abs_tol=1e-10)
    assert mejor_costo <= costo_inicial
    assert all(b['mejor_costo'] <= a['mejor_costo']
               for a, b in zip(historial, historial[1:]))
    return {
        'semilla': semilla, 'ruta_inicial': ruta_inicial, 'costo_inicial': costo_inicial,
        'mejor_ruta': mejor_ruta, 'mejor_costo': mejor_costo,
        'ruta_final': vc.copy(), 'costo_final': costo_actual,
        'propuestas': propuestas, 'aceptadas': aceptadas,
        'empeoramientos_aceptados': empeoramientos,
        'mejoras_aceptadas': mejoras, 'empates_aceptados': empates,
        'niveles': nivel, 'temperatura_final': temperatura,
        'segundos': segundos, 'historial': historial,
        'ejemplo_intercambio': ejemplo_intercambio,
    }


def verificar_implementacion():
    d = matriz_distancias([[0, 0], [3, 0], [3, 4]]).tolist()
    assert longitud([0, 1, 2], d) == 12.0
    assert probabilidad_aceptar(-13, 10) == 1.0
    assert probabilidad_aceptar(0, 10) == 0.5
    assert math.isclose(probabilidad_aceptar(13, 10), 0.2141650169574414)
    assert 0 <= probabilidad_aceptar(13, 1) < probabilidad_aceptar(13, 10) < 0.5
    assert probabilidad_aceptar(1e8, 0.01) == 0.0
    original = list(range(15))
    vecinos = set()
    for i in range(15):
        for j in range(i + 1, 15):
            vecino = original.copy()
            vecino[i], vecino[j] = vecino[j], vecino[i]
            assert sorted(vecino) == original
            assert sum(a != b for a, b in zip(original, vecino)) == 2
            vecinos.add(tuple(vecino))
    assert len(vecinos) == 105
    aleatorio = random.Random(17)
    vecino, i, j = vecino_intercambio(original, aleatorio)
    assert original == list(range(15)) and i != j
    assert sum(a != b for a, b in zip(original, vecino)) == 2


def experimentar(carpeta, repeticiones=20):
    carpeta = Path(carpeta)
    resultados = carpeta / 'resultados'
    resultados.mkdir(parents=True, exist_ok=True)
    verificar_implementacion()
    with (carpeta / 'datos' / 'ciudades.csv').open(encoding='utf-8') as f:
        filas = list(csv.DictReader(f))
    coordenadas = np.array([[float(f['x']), float(f['y'])] for f in filas])
    assert coordenadas.shape == (15, 2) and len(np.unique(coordenadas, axis=0)) == 15
    d = matriz_distancias(coordenadas)
    assert np.allclose(d, d.T) and np.all(np.diag(d) == 0)
    registros = []
    principal = None
    for semilla in range(repeticiones):
        r = templado_simulado(d, semilla=semilla)
        registros.append({k: v for k, v in r.items() if k not in ['historial', 'ejemplo_intercambio']})
        if semilla == 0:
            principal = r
        print(f'Semilla {semilla:02d}: {r["costo_inicial"]:.6f} -> {r["mejor_costo"]:.6f}', flush=True)
    resumen = {
        'ciudades': filas, 'unidades': 'unidades de distancia del plano; no kilómetros',
        'semilla_datos': 42,
        'parametros': {'t_inicial': 100.0, 't_minima': 0.01, 'enfriamiento': 0.99,
                       'vecinos_por_temperatura': 100},
        'repeticiones': repeticiones, 'principal': principal, 'corridas': registros,
    }
    (resultados / 'experimento.json').write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding='utf-8')
    with (resultados / 'historial_semilla0.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(principal['historial'][0]))
        writer.writeheader()
        writer.writerows(principal['historial'])
    with (resultados / 'corridas.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[k for k in registros[0] if 'ruta' not in k])
        writer.writeheader()
        writer.writerows({k: v for k, v in r.items() if 'ruta' not in k} for r in registros)
    with (resultados / 'distancias.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ciudad'] + [r['ciudad'] for r in filas])
        for etiqueta, fila in zip(filas, d):
            writer.writerow([etiqueta['ciudad']] + fila.tolist())
    return resumen


if __name__ == '__main__':
    experimentar(Path(__file__).resolve().parent)

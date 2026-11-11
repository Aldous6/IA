"""Funciones originales de Tarea 5; algoritmo de templado conservado."""
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

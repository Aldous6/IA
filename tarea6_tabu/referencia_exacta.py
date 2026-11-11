"""Referencia exacta del TSP cerrado mediante programación dinámica Held-Karp.

No usa el algoritmo de templado simulado ni modifica sus resultados.
Las distancias euclidianas se calculan sin redondear, en doble precisión.
"""
from array import array
from itertools import permutations
from pathlib import Path
import csv
import json
import math
import time


def matriz_distancias(coordenadas):
    """Matriz euclidiana simétrica con diagonal cero."""
    n = len(coordenadas)
    distancias = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            distancia = math.hypot(coordenadas[i][0] - coordenadas[j][0],
                                  coordenadas[i][1] - coordenadas[j][1])
            distancias[i][j] = distancias[j][i] = distancia
    return distancias


def costo_ciclo(ruta, distancias):
    """Admite una permutación o su representación con el origen repetido al final."""
    if len(ruta) == 0:
        raise ValueError('La ruta no puede estar vacía.')
    nodos = list(ruta)
    if len(nodos) > 1 and nodos[-1] == nodos[0]:
        nodos.pop()
    return math.fsum(distancias[nodos[k]][nodos[(k + 1) % len(nodos)]]
                     for k in range(len(nodos)))


def canonicalizar(ruta):
    """Ancla en 0 y elige una orientación estable para un ciclo simétrico."""
    base = list(ruta)
    if len(base) > 1 and base[0] == base[-1]:
        base.pop()
    origen = base.index(0)
    base = base[origen:] + base[:origen]
    inversa = [0] + list(reversed(base[1:]))
    elegida = min(base, inversa)
    return elegida + [0]


def held_karp(distancias):
    """Resuelve exactamente el ciclo Hamiltoniano mínimo, anclando el nodo 0.

    dp[S,j] es el menor costo desde 0 que visita exactamente S y termina en j.
    S representa un subconjunto de las ciudades 1,...,n-1.
    La recurrencia considera todos los predecesores de j dentro de S.
    Tiempo O(n² 2^n); memoria O(n 2^n), incluyendo recuperación de la ruta.
    """
    iniciado = time.perf_counter()
    n = len(distancias)
    if n == 0 or any(len(fila) != n for fila in distancias):
        raise ValueError('La matriz de distancias debe ser cuadrada y no vacía.')
    for i in range(n):
        for j in range(n):
            if not math.isfinite(distancias[i][j]) or distancias[i][j] < 0:
                raise ValueError('Las distancias deben ser finitas y no negativas.')
            if not math.isclose(distancias[i][j], distancias[j][i], abs_tol=1e-12):
                raise ValueError('Esta referencia espera un TSP simétrico.')
    if n == 1:
        return {'costo_optimo': 0.0, 'ruta_indices': [0, 0],
                'permutacion_indices': [0], 'subproblemas': 1,
                'transiciones': 0, 'tiempo_segundos': time.perf_counter() - iniciado}
    m = n - 1
    total_mascaras = 1 << m
    dp = array('d', [math.inf]) * (total_mascaras * m)
    padres = array('h', [-1]) * (total_mascaras * m)
    for j in range(m):
        dp[(1 << j) * m + j] = distancias[0][j + 1]
    subproblemas = m
    transiciones = 0
    for mascara in range(1, total_mascaras):
        finales = mascara
        while finales:
            bit_j = finales & -finales
            j = bit_j.bit_length() - 1
            anteriores = mascara ^ bit_j
            if anteriores:
                mejor = math.inf
                padre = -1
                candidatos = anteriores
                while candidatos:
                    bit_i = candidatos & -candidatos
                    i = bit_i.bit_length() - 1
                    valor = dp[anteriores * m + i] + distancias[i + 1][j + 1]
                    if valor < mejor:
                        mejor, padre = valor, i
                    transiciones += 1
                    candidatos ^= bit_i
                dp[mascara * m + j] = mejor
                padres[mascara * m + j] = padre
                subproblemas += 1
            finales ^= bit_j
    completa = total_mascaras - 1
    ultimo = min(range(m), key=lambda j: dp[completa * m + j] + distancias[j + 1][0])
    optimo_dp = dp[completa * m + ultimo] + distancias[ultimo + 1][0]
    retroceso = []
    mascara = completa
    j = ultimo
    while mascara:
        retroceso.append(j + 1)
        padre = padres[mascara * m + j]
        mascara ^= 1 << j
        j = padre
    ruta = canonicalizar([0] + list(reversed(retroceso)) + [0])
    assert len(ruta) == n + 1 and ruta[0] == ruta[-1] == 0
    assert sorted(ruta[:-1]) == list(range(n))
    costo = costo_ciclo(ruta, distancias)
    assert math.isclose(costo, optimo_dp, rel_tol=1e-12, abs_tol=1e-9)
    assert subproblemas == m * (1 << (m - 1))
    if m > 1:
        assert transiciones == m * (m - 1) * (1 << (m - 2))
    return {
        'costo_optimo': costo,
        'ruta_indices': ruta,
        'permutacion_indices': ruta[:-1],
        'subproblemas': subproblemas,
        'transiciones': transiciones,
        'tiempo_segundos': time.perf_counter() - iniciado,
    }


def verificar_con_fuerza_bruta(distancias):
    """Comparación independiente enumerando los 5! ciclos anclados de seis ciudades."""
    n = min(6, len(distancias))
    submatriz = [fila[:n] for fila in distancias[:n]]
    costos = ((costo_ciclo([0, *resto, 0], submatriz), [0, *resto, 0])
              for resto in permutations(range(1, n)))
    optimo_bruto, ruta_bruta = min(costos)
    exacto = held_karp(submatriz)
    assert math.isclose(exacto['costo_optimo'], optimo_bruto, rel_tol=1e-12, abs_tol=1e-10)
    assert math.isclose(costo_ciclo(ruta_bruta, submatriz), optimo_bruto, abs_tol=1e-10)
    return {
        'numero_ciudades': n,
        'permutaciones_comprobadas': math.factorial(n - 1),
        'costo_fuerza_bruta': optimo_bruto,
        'costo_held_karp': exacto['costo_optimo'],
        'coinciden': True,
        'ruta_fuerza_bruta_indices': canonicalizar(ruta_bruta),
        'ruta_held_karp_indices': exacto['ruta_indices'],
    }


def resolver_csv(archivo):
    with Path(archivo).open(encoding='utf-8', newline='') as f:
        filas = list(csv.DictReader(f))
    etiquetas = [fila['ciudad'] for fila in filas]
    coordenadas = [(float(fila['x']), float(fila['y'])) for fila in filas]
    assert len(etiquetas) == len(set(etiquetas))
    assert len(coordenadas) == len(set(coordenadas))
    distancias = matriz_distancias(coordenadas)
    comprobacion = verificar_con_fuerza_bruta(distancias)
    resultado = held_karp(distancias)
    ruta = resultado['ruta_indices']
    assert costo_ciclo(ruta, distancias) == costo_ciclo(list(reversed(ruta)), distancias)
    resultado.update({
        'metodo': 'Held-Karp: programación dinámica exacta',
        'tipo_problema': 'TSP simétrico euclidiano, ciclo cerrado',
        'numero_ciudades': len(etiquetas),
        'ancla_de_referencia': etiquetas[0],
        'ruta_ciudades': [etiquetas[i] for i in ruta],
        'distancias_redondeadas': False,
        'unidad': 'unidades del plano',
        'comprobacion_6_ciudades': comprobacion,
        'complejidad_tiempo': 'O(n^2 * 2^n)',
        'complejidad_memoria': 'O(n * 2^n)',
        'alcance': ('El resultado es una referencia exacta para esta instancia y sus '
                    'distancias de doble precisión. Coincidir con ella valida el costo '
                    'alcanzado en una corrida; no convierte al templado simulado en '
                    'un método que garantice el óptimo en toda instancia o ejecución.'),
    })
    return resultado


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    resultado = resolver_csv(root / 'datos' / 'ciudades.csv')
    target = root / 'resultados' / 'optimo_exacto.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Costo óptimo exacto:', format(resultado['costo_optimo'], '.12f'))
    print('Ruta:', ' -> '.join(resultado['ruta_ciudades']))
    print('Comprobación seis ciudades: 120 permutaciones, coincide con fuerza bruta.')

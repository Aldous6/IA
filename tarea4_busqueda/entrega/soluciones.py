"""Comprobaciones ejecutables de las formulaciones de la Tarea 4."""
from collections import deque
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import heapq
import json
import math
import sys


def bfs(inicial, meta, sucesores):
    cola = deque([inicial])
    padre = {inicial: None}
    acciones = {}
    while cola:
        estado = cola.popleft()
        if meta(estado):
            camino = []
            while padre[estado] is not None:
                camino.append({'accion': acciones[estado], 'estado': estado})
                estado = padre[estado]
            return list(reversed(camino)), len(padre)
        for accion, siguiente in sucesores(estado):
            if siguiente not in padre:
                padre[siguiente] = estado
                acciones[siguiente] = accion
                cola.append(siguiente)
    return None, len(padre)


def colorear(adyacencias):
    regiones = list(adyacencias)
    n = len(regiones)
    indice = {r: i for i, r in enumerate(regiones)}
    for r, vecinos in adyacencias.items():
        if r in vecinos or any(v not in indice or r not in adyacencias[v] for v in vecinos):
            raise ValueError('Se requiere un grafo no dirigido, sin lazos.')

    def visitar(estado):
        if 0 not in estado:
            return estado
        i = estado.index(0)
        prohibidos = {estado[indice[v]] for v in adyacencias[regiones[i]]}
        for color in range(1, 5):
            if color not in prohibidos:
                siguiente = list(estado)
                siguiente[i] = color
                solucion = visitar(tuple(siguiente))
                if solucion is not None:
                    return solucion
        return None

    resultado = visitar((0,) * n)
    return None if resultado is None else dict(zip(regiones, resultado))


def sucesores_mono(estado, vecinos, bananas):
    """Estado: (zona_mono, soporte_mono, zona_C1, zona_C2, soporte_C1, soporte_C2, tiene).

    Los soportes se codifican 0=suelo, 1=C1, 2=C2. Las zonas permiten
    maniobrar con dos cajas: no se consideran puntos físicos sin extensión.
    """
    m, soporte_mono, p1, p2, s1, s2, tiene = estado
    posiciones, soportes = [p1, p2], [s1, s2]

    def construir(nuevo_m=m, nuevo_soporte=soporte_mono,
                 nuevas_posiciones=None, nuevos_soportes=None, nuevo_tiene=tiene):
        ps = posiciones if nuevas_posiciones is None else nuevas_posiciones
        ss = soportes if nuevos_soportes is None else nuevos_soportes
        return (nuevo_m, nuevo_soporte, ps[0], ps[1], ss[0], ss[1], nuevo_tiene)

    def libre(i):
        return not any(s == i + 1 for s in soportes)

    if soporte_mono == 0:
        for destino in vecinos[m]:
            yield ('caminar', destino), construir(nuevo_m=destino)
        for i in range(2):
            if posiciones[i] == m and soportes[i] == 0 and libre(i):
                for destino in vecinos[m]:
                    ps = posiciones.copy()
                    ps[i] = destino
                    yield ('empujar', f'C{i+1}', destino), construir(nuevo_m=destino, nuevas_posiciones=ps)
            if posiciones[i] == m and libre(i):
                yield ('subir', f'C{i+1}'), construir(nuevo_soporte=i + 1)
        if posiciones[0] == posiciones[1] == m:
            for i, j in [(0, 1), (1, 0)]:
                if soportes[i] == soportes[j] == 0:
                    ss = soportes.copy()
                    ss[i] = j + 1
                    yield ('apilar', f'C{i+1}', f'C{j+1}'), construir(nuevos_soportes=ss)
                elif soportes[i] == j + 1 and libre(i):
                    ss = soportes.copy()
                    ss[i] = 0
                    yield ('desapilar', f'C{i+1}', f'C{j+1}'), construir(nuevos_soportes=ss)
    else:
        yield ('bajar',), construir(nuevo_soporte=0)

    altura_base = 0 if soporte_mono == 0 else (3 if soportes[soporte_mono - 1] == 0 else 6)
    if not tiene and m == bananas and altura_base + 3 >= 8:
        yield ('tomar_bananas',), construir(nuevo_tiene=True)


def buscar_registro_ilegal(indices, falla):
    """Encuentra al menos uno. Precondición: el conjunto inicial ya se sabe que falla.

    falla(C) es True si al menos un registro de C es ilegal. No se presupone
    que haya uno solo. Las consultas mantienen registros completos y su contexto.
    """
    candidatos = tuple(indices)
    if not candidatos:
        raise ValueError('El archivo inicial debe contener algún registro ilegal.')
    consultas = 0
    while len(candidatos) > 1:
        mitad = len(candidatos) // 2
        izquierda, derecha = candidatos[:mitad], candidatos[mitad:]
        consultas += 1
        candidatos = izquierda if falla(izquierda) else derecha
    return candidatos[0], consultas


CAPACIDADES = (12, 8, 3)


def sucesores_jarras(estado):
    for i, capacidad in enumerate(CAPACIDADES):
        if estado[i] < capacidad:
            nuevo = list(estado)
            nuevo[i] = capacidad
            yield f'llenar {capacidad}', tuple(nuevo)
        if estado[i] > 0:
            nuevo = list(estado)
            nuevo[i] = 0
            yield f'vaciar {capacidad}', tuple(nuevo)
        for j in range(3):
            if i == j:
                continue
            cantidad = min(estado[i], CAPACIDADES[j] - estado[j])
            if cantidad > 0:
                nuevo = list(estado)
                nuevo[i] -= cantidad
                nuevo[j] += cantidad
                yield f'verter {capacidad} a {CAPACIDADES[j]}', tuple(nuevo)


def punto(coordenadas):
    return tuple(Fraction(str(x)) for x in coordenadas)


def cruz(a, b):
    return a[0] * b[1] - a[1] * b[0]


def resta(a, b):
    return a[0] - b[0], a[1] - b[1]


def orientar(poligono):
    p = tuple(punto(v) for v in poligono)
    if len(p) < 3 or len(set(p)) != len(p):
        raise ValueError('El polígono requiere al menos tres vértices distintos.')
    area = sum(cruz(a, b) for a, b in zip(p, p[1:] + p[:1]))
    if area == 0:
        raise ValueError('El polígono no puede tener área cero.')
    if area < 0:
        p = tuple(reversed(p))
    if any(cruz(resta(p[(i+1) % len(p)], p[i]),
                resta(p[(i+2) % len(p)], p[(i+1) % len(p)])) < 0 for i in range(len(p))):
        raise ValueError('Se esperan polígonos convexos ordenados por su contorno.')
    return p


def segmento_entra_interior(u, v, poligono):
    """Recorte exacto por semiplanos estrictos de un polígono convexo CCW.

    Busca t en [0,1] que satisfaga cruz(arista, u+t*(v-u)-a)>0
    para todas las aristas. Un contacto o un tramo sobre el borde es admisible.
    """
    inferior, superior = Fraction(0), Fraction(1)
    direccion = resta(v, u)
    for a, b in zip(poligono, poligono[1:] + poligono[:1]):
        arista = resta(b, a)
        A, B = cruz(arista, resta(u, a)), cruz(arista, direccion)
        if B == 0:
            if A <= 0:
                return False
        else:
            limite = -A / B
            if B > 0:
                inferior = max(inferior, limite)
            else:
                superior = min(superior, limite)
            if inferior >= superior:
                return False
    return inferior < superior


class ProblemaVisibilidad:
    """Estados identificados por índices; ACTIONS devuelve vectores exactos."""
    def __init__(self, inicio, meta, poligonos):
        self.poligonos = [orientar(p) for p in poligonos]
        vertices = [punto(inicio), punto(meta)] + [v for p in self.poligonos for v in p]
        self.vertices = list(dict.fromkeys(vertices))
        self.inicio = self.vertices.index(punto(inicio))
        self.meta = self.vertices.index(punto(meta))
        for v in [punto(inicio), punto(meta)]:
            if any(segmento_entra_interior(v, v, p) for p in self.poligonos):
                raise ValueError('Inicio y meta deben estar fuera de los interiores.')
        self.destinos = [dict() for _ in self.vertices]
        for i, j in combinations(range(len(self.vertices)), 2):
            u, v = self.vertices[i], self.vertices[j]
            if not any(segmento_entra_interior(u, v, p) for p in self.poligonos):
                self.destinos[i][resta(v, u)] = j
                self.destinos[j][resta(u, v)] = i

    def actions(self, vertice):
        return tuple(self.destinos[vertice])

    def result(self, vertice, vector):
        return self.destinos[vertice][vector]

    def goal_test(self, vertice):
        return vertice == self.meta

    def step_cost(self, vertice, vector):
        return math.hypot(float(vector[0]), float(vector[1]))

    def h(self, vertice):
        d = resta(self.vertices[self.meta], self.vertices[vertice])
        return math.hypot(float(d[0]), float(d[1]))


def astar(problema):
    inicio = problema.inicio
    costos, padre = {inicio: 0.0}, {inicio: None}
    abiertos = [(problema.h(inicio), 0.0, inicio)]
    while abiertos:
        _, g, v = heapq.heappop(abiertos)
        if g > costos[v]:
            continue
        if problema.goal_test(v):
            camino = []
            while v is not None:
                camino.append(v)
                v = padre[v]
            return list(reversed(camino)), g
        for accion in problema.actions(v):
            w = problema.result(v, accion)
            nuevo = g + problema.step_cost(v, accion)
            if nuevo < costos.get(w, math.inf):
                costos[w], padre[w] = nuevo, v
                heapq.heappush(abiertos, (nuevo + problema.h(w), nuevo, w))
    return None, math.inf


def verificar():
    k4 = {i: {j for j in range(4) if j != i} for i in range(4)}
    colores = colorear(k4)
    assert len(set(colores.values())) == 4
    assert all(colores[i] != colores[j] for i in k4 for j in k4[i])

    # Instancia de prueba del modelo abstracto: no son posiciones dadas por el libro.
    vecinos = {i: tuple(j for j in range(4) if j != i) for i in range(4)}
    inicial = (0, 0, 1, 2, 0, 0, False)
    mono, _ = bfs(inicial, lambda s: s[-1], lambda s: sucesores_mono(s, vecinos, bananas=3))
    assert mono is not None and mono[-1]['estado'][-1]
    assert any(p['accion'][0] == 'apilar' for p in mono)
    for paso in mono:
        m, qm, p1, p2, s1, s2, tiene = paso['estado']
        assert s1 != 1 and s2 != 2 and not (s1 == 2 and s2 == 1)
        if s1 == 2 or s2 == 1:
            assert p1 == p2
        if qm:
            assert m == (p1, p2)[qm - 1]

    casos_archivo = []
    for mascara in range(1, 256):
        ilegales = {i+1 for i in range(8) if mascara & (1 << i)}
        indice, consultas = buscar_registro_ilegal(range(1, 9), lambda C: bool(ilegales.intersection(C)))
        assert indice in ilegales and consultas <= 3
        casos_archivo.append(consultas)

    jarras, descubiertos = bfs((0, 0, 0), lambda s: 1 in s, sucesores_jarras)
    assert [p['estado'] for p in jarras] == [(12, 0, 0), (4, 8, 0), (1, 8, 3)]
    assert len(jarras) == 3
    for p in jarras:
        assert all(0 <= x <= c for x, c in zip(p['estado'], CAPACIDADES))

    rectangulo = orientar([(0, 0), (2, 0), (2, 2), (0, 2)])
    assert not segmento_entra_interior(punto((0, 0)), punto((2, 0)), rectangulo)
    assert segmento_entra_interior(punto((0, 0)), punto((2, 2)), rectangulo)
    assert not segmento_entra_interior(punto((-1, 1)), punto((1, -1)), rectangulo)
    assert segmento_entra_interior(punto((-1, -1)), punto((1, 1)), rectangulo)
    problema = ProblemaVisibilidad((-1, 1), (3, 1), [rectangulo])
    assert len(problema.vertices) == 6
    assert problema.meta not in problema.destinos[problema.inicio].values()
    camino, costo = astar(problema)
    assert math.isclose(costo, 2 + 2 * math.sqrt(2), abs_tol=1e-12)
    for v in range(len(problema.vertices)):
        for a in problema.actions(v):
            w = problema.result(v, a)
            assert problema.h(v) <= problema.step_cost(v, a) + problema.h(w) + 1e-12
    return {
        'colores_prueba_K4': colores,
        'mono_instancia_de_prueba': {'inicial': inicial, 'bananas_en_zona': 3, 'plan': mono},
        'registros': {'distribuciones_ilegales_verificadas': 255, 'registros_por_archivo': 8,
                      'maximo_consultas_adicionales': max(casos_archivo)},
        'jarras': {'inicial': [0, 0, 0], 'camino': jarras, 'acciones_minimas': 3,
                   'estados_descubiertos_hasta_la_meta': descubiertos},
        'visibilidad_prueba_sintetica': {
            'nota': 'Rectángulo de prueba; no es una digitalización de la figura 3.31.',
            'inicio': [-1, 1], 'meta': [3, 1], 'obstaculo': [[0, 0], [2, 0], [2, 2], [0, 2]],
            'estados': len(problema.vertices), 'ruta_indices': camino, 'costo_optimo': costo,
            'costo_analitico': '2 + 2*sqrt(2)', 'heuristica_consistente_verificada': True,
        },
        'figura_331': {'poligonos': 8, 'vertices_obstaculos': 33, 'estados_con_S_y_G': 35},
    }


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    resultado = verificar()
    salida = Path(__file__).resolve().parent / 'resultados'
    salida.mkdir(exist_ok=True)
    (salida / 'verificacion.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Formulaciones comprobadas: coloración K4, mono abstracto, 255 archivos, jarras y visibilidad.')
    print('Jarras: 3 acciones; (0,0,0) → (12,0,0) → (4,8,0) → (1,8,3).')
    print('Grafo sintético: A* coincide con la longitud analítica 2+2*sqrt(2).')

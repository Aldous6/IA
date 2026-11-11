"""Tarea 3: reglas reactivas y una fase interna explícita de ida/regreso.

La fase es una extensión de la base de datos de las diapositivas, no una
cuarta acción física. Sólo se avanza, aspira o gira 90 grados a la derecha.
"""
from itertools import product
import json
from pathlib import Path


N, E, S, O = 'norte', 'este', 'sur', 'oeste'
DERECHA = {N: E, E: S, S: O, O: N}
DESPLAZAMIENTO = {N: (0, 1), E: (1, 0), S: (0, -1), O: (-1, 0)}
CASILLAS = tuple(product(range(3), repeat=2))
INICIO = (0, 0, N)

# Reglas originales 1.2 a 1.5; aspirar siempre tiene prioridad.
ORIGINALES = {
    (0, 0, N): ('1.2', 'avanzar'),
    (0, 1, N): ('1.3', 'avanzar'),
    (0, 2, N): ('1.4', 'girar'),
    (0, 2, E): ('1.5', 'avanzar'),
}

# Todas estas reglas presuponen que la casilla actual está limpia.
IDA = {
    (1, 2, E): ('1.6', 'girar'),
    (1, 2, S): ('1.7', 'avanzar'),
    (1, 1, S): ('1.8', 'avanzar'),
    (1, 0, S): ('1.9', 'girar'),
    (1, 0, O): ('1.10', 'girar'),
    (1, 0, N): ('1.11', 'girar'),
    (1, 0, E): ('1.12', 'avanzar'),
    (2, 0, E): ('1.13', 'girar'),
    (2, 0, S): ('1.14', 'girar'),
    (2, 0, O): ('1.15', 'girar'),
    (2, 0, N): ('1.16', 'avanzar'),
    (2, 1, N): ('1.17', 'avanzar'),
}
REGRESO = {
    (2, 2, N): ('1.18', 'girar'),
    (2, 2, E): ('1.19', 'girar'),
    (2, 2, S): ('1.20', 'avanzar'),
    (2, 1, S): ('1.21', 'avanzar'),
    (2, 0, S): ('1.22', 'girar'),
    (2, 0, O): ('1.23', 'avanzar'),
    (1, 0, O): ('1.24', 'avanzar'),
    (0, 0, O): ('1.25', 'girar'),
}


def actualizar_fase(posicion, rumbo, fase):
    """Actualización de memoria; no consume una acción del robot."""
    if fase == 'ida' and posicion == (2, 2):
        return 'regreso'
    if fase == 'regreso' and posicion == (0, 0) and rumbo == N:
        return 'ida'
    return fase


def decidir(posicion, rumbo, basura, fase):
    if posicion in basura:
        return '1.1', 'aspirar'
    pose = (*posicion, rumbo)
    if pose in ORIGINALES:
        return ORIGINALES[pose]
    return (IDA if fase == 'ida' else REGRESO)[pose]


def simular(basura_inicial=(), ciclos=1):
    basura = set(basura_inicial)
    posicion, rumbo, fase = (0, 0), N, 'ida'
    visitadas = {posicion}
    traza = []
    completados = 0
    for paso in range(1, ciclos * 34 + len(basura_inicial) + 1):
        fase = actualizar_fase(posicion, rumbo, fase)
        regla, accion = decidir(posicion, rumbo, basura, fase)
        anterior = posicion
        anterior_rumbo = rumbo
        if accion == 'aspirar':
            basura.remove(posicion)
        elif accion == 'girar':
            rumbo = DERECHA[rumbo]
        elif accion == 'avanzar':
            dx, dy = DESPLAZAMIENTO[rumbo]
            posicion = (posicion[0] + dx, posicion[1] + dy)
            assert posicion in CASILLAS, 'El agente salió del cuarto'
            visitadas.add(posicion)
        else:
            raise AssertionError('Acción física no permitida')
        fase = actualizar_fase(posicion, rumbo, fase)
        traza.append({
            'paso': paso, 'desde': anterior, 'rumbo_antes': anterior_rumbo,
            'regla': regla, 'accion': accion, 'hacia': posicion,
            'rumbo_despues': rumbo, 'fase_despues': fase,
        })
        if (*posicion, rumbo) == INICIO and fase == 'ida' and accion == 'girar':
            completados += 1
            if completados == ciclos:
                assert visitadas == set(CASILLAS)
                assert not basura, 'Quedó basura inicial sin aspirar'
                return traza
    raise AssertionError('El robot no completó los ciclos requeridos')


def verificar_todas():
    sin_basura = simular()
    assert len(sin_basura) == 24
    assert sum(t['accion'] == 'avanzar' for t in sin_basura) == 12
    assert sum(t['accion'] == 'girar' for t in sin_basura) == 12
    movimientos = [INICIO[:2]] + [t['hacia'] for t in sin_basura if t['accion'] == 'avanzar']
    esperado = [(0, 0), (0, 1), (0, 2), (1, 2), (1, 1), (1, 0),
                (2, 0), (2, 1), (2, 2), (2, 1), (2, 0), (1, 0), (0, 0)]
    assert movimientos == esperado
    for configuracion in product((False, True), repeat=9):
        basura = {p for p, sucia in zip(CASILLAS, configuracion) if sucia}
        traza = simular(basura)
        assert len(traza) == 24 + len(basura)
        assert sum(t['accion'] == 'aspirar' for t in traza) == len(basura)
        # Comprobar además que el siguiente ciclo conserva la navegación.
        assert len(simular(basura, ciclos=2)) == 48 + len(basura)
    return {
        'configuraciones_verificadas': 512,
        'ciclos_verificados_por_configuracion': 2,
        'acciones_sin_basura_por_ciclo': 24,
        'avances_por_ciclo': 12,
        'giros_por_ciclo': 12,
        'acciones_primer_ciclo_todo_sucio': len(simular(CASILLAS)),
        'ruta_de_posiciones_sin_repetir_giros': movimientos,
        'traza_sin_basura': sin_basura,
    }


if __name__ == '__main__':
    resultado = verificar_todas()
    target = Path(__file__).with_name('verificacion_tarea3.json')
    target.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Verificadas 512 configuraciones, dos ciclos cada una, sin salir del cuarto.')
    print('Un ciclo limpio: 12 avances + 12 giros = 24 acciones.')
    print('Primer ciclo con las nueve casillas sucias: 33 acciones.')

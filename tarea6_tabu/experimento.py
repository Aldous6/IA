"""Comparación emparejada y secuencial, con el mismo presupuesto de vecinos."""
from pathlib import Path
import csv
import json
import math
import platform
import sys
import numpy as np
import pandas as pd
from templado_base import matriz_distancias, longitud, templado_simulado
from tabu_tsp import busqueda_tabu, verificar_tabu
from referencia_exacta import held_karp

TAMANOS = [10, 15, 30, 50]
SEMILLAS = list(range(20))
PRESUPUESTO = 91700


def resumir(filas, optimos):
    df = pd.DataFrame(filas)
    filas_resumen = []
    diferencias = []
    for n in sorted(df.n.unique()):
        subset = df[df.n == n]
        for algoritmo in ['Templado', 'Tabu']:
            g = subset[subset.algoritmo == algoritmo]
            opt = optimos.get(str(n), {}).get('costo_optimo')
            filas_resumen.append({
                'n': int(n), 'algoritmo': algoritmo, 'corridas': len(g),
                'mejor_costo': float(g.mejor_costo.min()),
                'costo_medio': float(g.mejor_costo.mean()),
                'desviacion_costos': float(g.mejor_costo.std(ddof=1)),
                'peor_costo': float(g.mejor_costo.max()),
                'reduccion_media_porcentaje': float(g.reduccion_porcentaje.mean()),
                'tiempo_mediano_s': float(g.segundos.median()),
                'tiempo_q1_s': float(g.segundos.quantile(.25)),
                'tiempo_q3_s': float(g.segundos.quantile(.75)),
                'movimientos_medios': float(g.movimientos.mean()),
                'evaluaciones_min': int(g.evaluaciones.min()),
                'evaluaciones_max': int(g.evaluaciones.max()),
                'optimo_conocido': opt,
                'aciertos_optimo': None if opt is None else int(np.isclose(g.mejor_costo, opt, rtol=0, atol=1e-8).sum()),
                'brecha_media_optimo_porcentaje': None if opt is None else float(np.maximum(0, g.mejor_costo - opt).mean() / opt * 100),
            })
        a = subset[subset.algoritmo == 'Templado'].set_index('semilla')
        b = subset[subset.algoritmo == 'Tabu'].set_index('semilla')
        delta = b.mejor_costo - a.mejor_costo
        diferencias.append({'n': int(n), 'tabu_mejor': int((delta < -1e-8).sum()),
                            'empates': int((abs(delta) <= 1e-8).sum()),
                            'templado_mejor': int((delta > 1e-8).sum()),
                            'diferencia_media_porcentaje_tabu_vs_templado': float((100 * delta / a.mejor_costo).mean()),
                            'razon_tiempo_mediano_tabu_vs_templado': float(b.segundos.median() / a.segundos.median())})
    return filas_resumen, diferencias


def ejecutar(carpeta):
    carpeta = Path(carpeta)
    out = carpeta / 'resultados'
    out.mkdir(exist_ok=True)
    verificar_tabu()
    historico = json.loads((carpeta / 'datos/referencia_tarea5.json').read_text(encoding='utf-8'))
    optimos, corridas, historiales, trazas = {}, [], {}, {}
    for n in TAMANOS:
        data = pd.read_csv(carpeta / 'datos' / f'ciudades_{n}.csv')
        coords = data[['x', 'y']].to_numpy(dtype=float)
        assert len(coords) == n and len(np.unique(coords, axis=0)) == n
        d = matriz_distancias(coords)
        if n <= 15:
            optimos[str(n)] = held_karp(d.tolist())
        for semilla in SEMILLAS:
            # Se alterna el orden para repartir efectos temporales del equipo.
            orden = ['Templado', 'Tabu'] if semilla % 2 == 0 else ['Tabu', 'Templado']
            par = {}
            for algoritmo in orden:
                if algoritmo == 'Templado':
                    r = templado_simulado(d, semilla=semilla)
                    evaluaciones, movimientos = r['propuestas'], r['aceptadas']
                    h = [{'evaluaciones': x['iteracion'], 'iteracion': x['nivel'],
                          'costo_actual': x['costo_actual'], 'mejor_costo': x['mejor_costo']}
                         for x in r['historial']]
                else:
                    r = busqueda_tabu(d, semilla=semilla, horizonte=5, presupuesto=PRESUPUESTO)
                    evaluaciones, movimientos = r['evaluaciones'], r['iteraciones']
                    h = r['historial']
                    assert r['motivo_parada'] == 'presupuesto'
                assert evaluaciones == PRESUPUESTO
                assert sorted(r['mejor_ruta']) == list(range(n))
                assert math.isclose(longitud(r['mejor_ruta'], d.tolist()), r['mejor_costo'], rel_tol=0, abs_tol=1e-8)
                registro = {
                    'n': n, 'semilla': semilla, 'algoritmo': algoritmo,
                    'costo_inicial': r['costo_inicial'], 'mejor_costo': r['mejor_costo'],
                    'costo_final': r['costo_final'], 'evaluaciones': evaluaciones,
                    'movimientos': movimientos, 'segundos': r['segundos'],
                    'reduccion_porcentaje': 100 * (r['costo_inicial'] - r['mejor_costo']) / r['costo_inicial'],
                    'ruta_inicial': r['ruta_inicial'], 'mejor_ruta': r['mejor_ruta'],
                    'empeoramientos_aceptados': r['empeoramientos_aceptados'],
                    'aspiraciones': r.get('aspiraciones'),
                }
                corridas.append(registro)
                par[algoritmo] = registro
                if semilla == 0:
                    historiales[f'{n}_{algoritmo}'] = h
                    if algoritmo == 'Tabu':
                        trazas[str(n)] = r['traza']
            assert par['Templado']['ruta_inicial'] == par['Tabu']['ruta_inicial']
            assert par['Templado']['costo_inicial'] == par['Tabu']['costo_inicial']
            if n == 15:
                assert abs(par['Templado']['mejor_costo'] - historico['mejores_costos'][semilla]) < 1e-8
                assert par['Templado']['costo_inicial'] == historico['costos_iniciales'][semilla]
            print(f'n={n:02d} semilla={semilla:02d} SA={par["Templado"]["mejor_costo"]:.6f} TS={par["Tabu"]["mejor_costo"]:.6f}', flush=True)
            # Guardado incremental: las corridas ya terminadas se conservan.
            pd.DataFrame([{k:v for k,v in r.items() if 'ruta' not in k} for r in corridas]).to_csv(out / 'corridas.csv', index=False)
    tabla, comparaciones = resumir(corridas, optimos)
    resultado = {'parametros': {'tamanos': TAMANOS, 'semillas': SEMILLAS, 'presupuesto_vecinos': PRESUPUESTO,
                               'horizonte_tabu': 5, 't0': 100, 'tmin': .01, 'alpha': .99, 'vecinos_por_T': 100,
                               'ultima_vecindad_tabu': 'subconjunto uniforme sin reemplazo con generador independiente',
                               'orden': 'alternado por semilla', 'instancias_por_tamano': 1},
                 'versiones': {'python': platform.python_version(), 'numpy': np.__version__, 'pandas': pd.__version__},
                 'corridas': corridas, 'resumen': tabla, 'comparaciones_emparejadas': comparaciones,
                 'optimos': optimos, 'historiales_semilla0': historiales, 'trazas_tabu': trazas}
    (out / 'experimento.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding='utf-8')
    pd.DataFrame(tabla).to_csv(out / 'resumen.csv', index=False)
    pd.DataFrame(comparaciones).to_csv(out / 'comparaciones_emparejadas.csv', index=False)
    for nombre, historial in historiales.items():
        pd.DataFrame(historial).to_csv(out / f'historial_{nombre}.csv', index=False)
    print('Terminado:160 corridas,80 comparaciones emparejadas.', flush=True)
    return resultado


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    ejecutar(Path(__file__).resolve().parent)

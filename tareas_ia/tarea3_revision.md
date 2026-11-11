# Tarea 3: revisión independiente y solución verificada

Fuente revisada: `presentaciones/6-Agentes inteligentes-2de2.pdf`, páginas 10 a 13. Se inspeccionó también la figura de la página 11, no sólo su extracción de texto.

## Qué pide realmente la presentación

La página 10 define un cuarto de 3 × 3, inicio en (0,0) mirando al norte y sólo tres acciones físicas: avanzar una casilla, aspirar y girar 90° a la derecha. El objetivo es recorrer el cuarto continuamente, sin salir de él. No hay una acción de giro a la izquierda, un giro instantáneo de 180° ni una acción de teletransporte al origen.

Los ejes de la figura de la página 11 son los habituales: x crece hacia el este y y crece hacia el norte. Por tanto, N avanza (0,+1), E (+1,0), S (0,−1) y O (−1,0). Un giro produce N → E → S → O → N.

La serpentina de ida que muestra la figura es:

(0,0) → (0,1) → (0,2) → (1,2) → (1,1) → (1,0) → (2,0) → (2,1) → (2,2).

La presentación exige regresar a (0,0), pero no dibuja ni especifica una ruta única de regreso. Una elección válida, usada en esta solución, es:

(2,2) → (2,1) → (2,0) → (1,0) → (0,0).

Al llegar al origen mirando al oeste se realiza un giro a la derecha para recuperar el rumbo norte y repetir el ciclo. Los giros mantienen fija la casilla. En particular, pasar de sur a este en (1,0), o de este a norte en (2,0), requiere tres acciones de giro a la derecha.

## Detalle de implementación que debe hacerse explícito

Hace falta distinguir ida y regreso. Se introduce el estado interno `fase ∈ {ida, regreso}` como una extensión mínima de un bit de memoria de la base de datos del agente. Este predicado adicional no aparece en la lista de tres predicados del dominio de la diapositiva; no debe presentarse como si estuviera dado por el enunciado. La arquitectura de la presentación ya mantiene estado interno mediante la función `siguiente`, por lo que la ampliación es natural, pero debe declararse.

El conflicto es real: en (1,0) mirando al oeste, durante la ida el robot debe girar para poder continuar al este hasta (2,0); durante el regreso por la ruta propuesta debe avanzar al oeste hasta (0,0). También en (2,0) mirando al oeste debe girar en la ida y avanzar en el regreso. Con sólo la misma posición, orientación y estado de limpieza, una política determinista sin memoria no puede seleccionar ambas acciones.

Más aún, conservar literalmente el recorrido de ida, el único giro a la derecha y los predicados originales no permite solucionar el problema eligiendo simplemente otro regreso sin memoria. Para volver a (0,0) habría que entrar desde (1,0) mirando al oeste o desde (0,1) mirando al sur. El primer caso requiere avanzar en la pose donde la ida exige girar. El segundo no es alcanzable: para generar rumbo sur en (0,1) habría que girar desde este, pero el este sólo puede generarse girando desde norte, y la regla original 1.3 obliga a avanzar al norte; llegar mirando al sur desde (0,2) tampoco es posible, porque la regla original 1.5 obliga a avanzar al este en lugar de girar desde este hacia sur. Los otros vecinos correspondientes están fuera del cuarto.

Se inicia con `fase = ida`. La actualización interna cambia a `regreso` al alcanzar (2,2), y vuelve a `ida` cuando se recupera la pose (0,0,norte). Estas actualizaciones son parte de `siguiente`; no consumen una cuarta acción física.

## Reglas

La regla 1.1 conserva prioridad absoluta: `en(x,y) ∧ basura(x,y) → Do(aspira)`. Aspirar no modifica posición, orientación ni fase. Todas las reglas de movimiento siguientes incluyen `¬basura(x,y)` para la casilla que mencionan; en la tabla se abrevia como **limpia**. Esta condición se agrega explícitamente a 1.5 para respetar la nota de la página 13: cada regla debe verificar si se dispara 1.1.

Se conservan las reglas iniciales:

| Regla | Posición | Orientación | Condición de limpieza | Acción |
|---|---|---|---|---|
| 1.2 | (0,0) | norte | limpia | avanzar |
| 1.3 | (0,1) | norte | limpia | avanzar |
| 1.4 | (0,2) | norte | limpia | girar |
| 1.5 | (0,2) | este | limpia | avanzar |

Cada fila complementaria representa `en(x,y) ∧ orientación(d) ∧ ¬basura(x,y) ∧ fase(f) → Do(acción)`.

| Regla | Fase | Posición | Orientación | Acción |
|---|---|---|---|---|
| 1.6 | ida | (1,2) | este | girar |
| 1.7 | ida | (1,2) | sur | avanzar |
| 1.8 | ida | (1,1) | sur | avanzar |
| 1.9 | ida | (1,0) | sur | girar |
| 1.10 | ida | (1,0) | oeste | girar |
| 1.11 | ida | (1,0) | norte | girar |
| 1.12 | ida | (1,0) | este | avanzar |
| 1.13 | ida | (2,0) | este | girar |
| 1.14 | ida | (2,0) | sur | girar |
| 1.15 | ida | (2,0) | oeste | girar |
| 1.16 | ida | (2,0) | norte | avanzar |
| 1.17 | ida | (2,1) | norte | avanzar |
| 1.18 | regreso | (2,2) | norte | girar |
| 1.19 | regreso | (2,2) | este | girar |
| 1.20 | regreso | (2,2) | sur | avanzar |
| 1.21 | regreso | (2,1) | sur | avanzar |
| 1.22 | regreso | (2,0) | sur | girar |
| 1.23 | regreso | (2,0) | oeste | avanzar |
| 1.24 | regreso | (1,0) | oeste | avanzar |
| 1.25 | regreso | (0,0) | oeste | girar |

Por ejemplo, la regla 1.24 completa es `en(1,0) ∧ orientación(oeste) ∧ ¬basura(1,0) ∧ fase(regreso) → Do(avanzar)`.

La posición y orientación pueden actualizarse a partir de las acciones deterministas realizadas, como indica la función `nueva` de la página 12; no es necesario inventar sensores GPS o una capacidad de observación completa del cuarto.

## Verificación por simulación

Se implementó `revision_tarea3/simulacion_tarea3.py` usando sólo la biblioteca estándar de Python y se ejecutó realmente. El archivo `revision_tarea3/verificacion_tarea3.json` conserva la traza completa de un ciclo sin basura y el resumen de los resultados.

Se comprobaron las 2^9 = 512 distribuciones iniciales de basura con dos ciclos consecutivos por distribución, inicio fijo en (0,0,norte) y basura estática que no reaparece durante la prueba. En todos los casos el agente visitó las nueve casillas, eliminó toda la basura inicial, se mantuvo dentro del cuarto y recuperó la pose inicial para continuar. La prueba no supone ni evalúa una tasa de aparición dinámica de basura.

Un ciclo limpio requiere 12 avances y 12 giros: 24 acciones físicas. Si inicialmente hay k casillas sucias, el primer ciclo requiere 24 + k acciones, porque aspirar añade una acción por casilla sin cambiar la ruta. Con las nueve casillas sucias, el primer ciclo requiere 33 acciones; el segundo, ya limpio, requiere 24. Esto mide las acciones de la ruta propuesta, no afirma que sea la ruta más corta posible bajo cualquier otro recorrido.

El código detiene la simulación después de verificar el número de ciclos solicitado; el agente no tiene una acción física de detenerse y, si se continúa ejecutando, sigue recorriendo y limpiando el cuarto conforme a la consigna.

Figura propia del recorrido: `revision_tarea3/recorrido_tarea3.png`. Las capturas de las páginas revisadas están en `revision_tarea3/pagina_10.png` a `pagina_13.png` para consulta interna.

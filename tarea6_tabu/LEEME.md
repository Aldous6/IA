# Tarea 6 — Búsqueda tabú para el TSP

Entrega de la actividad de `9-Heuristicas-modernas.ppt`. Se implementa búsqueda tabú basada en lo reciente y se compara con el templado simulado de la Tarea 5.

La carpeta `entrega` contiene el informe en Word y PDF y un notebook compatible con Google Colab, ejecutado con sus salidas. El Colab incluye todos los datos y algoritmos: se abre en Colab y se selecciona **Entorno de ejecución → Ejecutar todas**, usando CPU. No necesita credenciales ni descargas de datos. Ejecuta realmente las 160 corridas, no utiliza resultados precargados como sustituto del experimento.

## Reproducción local

Desde esta carpeta, con Python y las dependencias de `requirements.txt` disponibles:

```text
python experimento.py
```

Esta orden vuelve a calcular los experimentos y reemplaza los archivos de `resultados`. Usa 10, 15, 30 y 50 ciudades, 20 semillas por tamaño, los dos algoritmos y 91 700 evaluaciones por corrida. Las instancias son prefijos de un conjunto sintético de 50 puntos; las primeras 15 coordenadas coinciden exactamente con Tarea 5.

`tabu_tsp.py` implementa la memoria de pares no ordenados de identidades de ciudades, horizonte cinco y aspiración por mejora del mejor global anterior al barrido. `templado_base.py` conserva las cinco funciones originales de Tarea 5. `referencia_exacta.py` calcula Held–Karp únicamente para 10 y 15 ciudades. Se conserva el mejor ciclo visitado aunque el estado final empeore.

Los archivos `corridas.csv`, `resumen.csv` y `comparaciones_emparejadas.csv` contienen los resultados tabulares; `experimento.json` añade rutas, parámetros, versiones y las historias de la semilla cero. `datos/referencia_tarea5.json` conserva los 20 costos originales y huellas SHA-256 para comprobar la continuidad del método. `resultados/revision_independiente.txt` documenta las verificaciones adicionales.

## Resultado y alcance

Con 15 ciudades, templado alcanzó el óptimo exacto de 288.609288 unidades en 20 de 20 corridas, y tabú en 19 de 20. La excepción de tabú fue la semilla 3, con mejor costo 362.848480. Para 30 ciudades, templado obtuvo menor costo en 18 parejas, tabú en una y hubo un empate; para 50, templado obtuvo menor costo en las 20 parejas. Tabú tuvo menor tiempo mediano en esta implementación y este equipo.

Se estudia una instancia por tamaño con 20 rutas iniciales, no 20 mapas independientes. El horizonte fijo y el presupuesto fijo limitan la interpretación: al crecer el vecindario, tabú completa menos movimientos. Los mejores valores de 30 y 50 ciudades no se presentan como óptimos. Las mediciones del notebook provienen de una segunda ejecución completa; sus tiempos pueden diferir de la primera ejecución utilizada en Word/PDF, mientras que se comprueba la coincidencia de los 160 mejores costos.

## Regenerar la entrega

```text
python generar_documento.py
python crear_colab.py
```

Estas órdenes requieren también las dependencias de `requirements_entrega.txt`. El generador del notebook lo ejecuta de principio a fin y valida que no existan errores. La generación de Word/PDF toma los datos de `resultados/experimento.json` sin repetir el benchmark.

## Fuentes

Presentación 9 del curso, `9-Heuristicas-modernas.ppt`, y trabajo previo de Tarea 5. El texto extraído de la presentación está en `material/presentacion9_texto.txt`.

Glover, F. (1989). *Tabu Search—Part I*. ORSA Journal on Computing, 1(3), 190–206. [Texto del autor](https://leeds-faculty.colorado.edu/glover/TS%20-%20Part%20I-ORSA-aw.pdf). DOI: 10.1287/ijoc.1.3.190.

MathWorks. [How Simulated Annealing Works](https://www.mathworks.com/help/gads/how-simulated-annealing-works.html), regla de aceptación logística utilizada para conservar la referencia de Tarea 5.

Held, M., y Karp, R. M. (1961). [A dynamic programming approach to sequencing problems](https://research.ibm.com/publications/a-dynamic-programming-approach-to-sequencing-problems). IBM Research.

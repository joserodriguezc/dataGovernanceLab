# Capítulo 11: Operaciones de datos

> **Libro:** *Data Operations*. Parte 2: Las capacidades de gobierno de datos en profundidad.
> **Microproyecto:** Operaciones de datos con SLAs.

**Estado:** ✅ hecho

## Objetivo

Hacer visible el trabajo que mantiene vivos los datos de NovaMercado:
- un **pipeline nocturno orquestado** que ejecuta de verdad los capítulos 10, 6, 7 y 8 sobre el warehouse, con reintentos y un registro de auditoría;
- **SLAs y observabilidad** (frescura y volumen);
- un **sistema de tickets** con revisión de causas raíz;
- el **panel de valor** del equipo que propone el libro.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| Las operaciones de datos son el "pegamento" del ecosistema | El pipeline encadena carga, golden record, metadatos, linaje y calidad | [pipeline.py](pipeline.py) |
| Automatizar los pipelines de datos | Orquestador con orden de dependencias, un reintento y omisión de los pasos dependientes si algo falla | [pipeline.py](pipeline.py) |
| Equipo con accesos amplios: registro de auditoría y controles ("la confianza no es un control") | Cada paso queda registrado con usuario, hora, duración, estado y error | [pipeline.py](pipeline.py) |
| Monitorización y mejora continua | SLAs por paso y de entrega, frescura del dato y variación de volumen entre ejecuciones | [analysis.py](analysis.py) |
| Trabajar desde un sistema de tickets y hacer revisiones posteriores | Tickets por causa raíz y sistema; las combinaciones más repetidas alimentan el backlog de automatización | [history.py](history.py), [analysis.py](analysis.py) |
| Panel de valor: dólares, horas, riesgos evitados y automatizaciones | Valor de las automatizaciones de los capítulos 6 a 11 y causas raíz | [templates/data_operations.md.j2](templates/data_operations.md.j2) |
| Operaciones de TI frente a operaciones de datos: separadas pero aliadas | Tabla de responsabilidades | [inputs/operations.yaml](inputs/operations.yaml) |
| Hacer visible al equipo: champion, KPI y comunicación | Plan de visibilidad | [inputs/operations.yaml](inputs/operations.yaml) |

## Entregables

En `outputs/`:

| Archivo | Contenido |
|---|---|
| `data_operations.md` | Panel de valor, última ejecución real (con diagrama), observabilidad, SLAs, causas raíz, revisión posterior, TI frente a datos y plan de visibilidad |
| `ops_timeline.png` | Hora de fin del pipeline cada noche frente al SLA |
| `ops_root_causes.png` | Tickets por causa raíz |
| `tickets.csv` | Tickets del historial |

En `data/warehouse/operations.duckdb` (**fuera** del warehouse): las tablas `runs` (auditoría de cada paso) y `row_counts` (volumen de cada ejecución).

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch11_operaciones_datos.pipeline            # solo el pipeline nocturno
uv run python -m chapters.ch11_operaciones_datos.run                 # pipeline + informe
uv run python -m chapters.ch11_operaciones_datos.run --sin-pipeline  # solo el informe
uv run pytest chapters/ch11_operaciones_datos
```

El pipeline reconstruye el warehouse desde `data/raw` y vuelve a ejecutar los capítulos 10, 6, 7 y 8. Es la forma cómoda de dejar el warehouse completo tras cualquier cambio.

## Decisiones de modelado

- **El registro de operaciones vive fuera del warehouse.** Si estuviera dentro, cada reconstrucción borraría el historial que sirve para medir los SLAs.
- **Orden del pipeline:** carga → golden record (10) → metadatos (6) → linaje (7) → calidad (8). El 10 va antes del 6 y del 7 para que `dim_customer` quede documentada y con linaje, y el 8 al final porque la certificación necesita los dos.
- **El historial es simulado y el pipeline es real.** La última ejecución mide segundos reales del laboratorio; el historial de 120 noches simula minutos de un entorno real, con la semilla y los parámetros en `operations.yaml`.
- **Los reintentos solo arreglan los fallos transitorios.** La primera versión hacía que el reintento fallara con la misma probabilidad que el primer intento, así que casi nunca fallaba nada (100 % de noches correctas, irreal). Ahora `retry_success` fija qué parte de los fallos se resuelve al reintentar.
- **Los tickets de "fallos de proceso" salen de las noches fallidas,** no de una tasa inventada: los dos registros son coherentes.

## Conclusiones para NovaMercado

1. **Hay 6 automatizaciones con un valor de US$ 523.751/año, 4.911 horas ahorradas y 47 riesgos evitados.** Agregan lo que los capítulos 6 a 11 estimaron por separado: es el panel que el libro recomienda enseñar para que el equipo no sea invisible. Sigue pendiente de validar con el negocio.
2. **No se cumplen los SLAs:** 91,7 % de noches sin fallos y 90,8 % con la cifra de ventas a tiempo, frente a un objetivo del 98 %. El golden record es el paso más frágil (7,6 % de ejecuciones fuera de SLA y 4 fallos).
3. **La frescura es el problema más visible:** el último dato de ventas tiene 12 días y el SLA pide 3. Coincide con la regla DQ-16 del capítulo 8.
4. **La mitad de los tickets son bugs** (26 de 52) y se concentran en el CRM y el POS. La propuesta es llevar pruebas automáticas al SDLC, como la revisión de arquitectura del capítulo 9, en lugar de seguir apagando fuegos.
5. **El volumen de cada tabla curada se vigila entre ejecuciones:** una caída de más del 20 % en, por ejemplo, `fct_sales` se avisa antes de que llegue al comité.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada
- [x] Paso añadido al recorrido del README raíz

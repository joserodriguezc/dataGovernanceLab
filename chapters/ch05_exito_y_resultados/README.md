# Capítulo 5: Definir el éxito y alinearse en resultados

> **Libro:** *Defining Success and Aligning on Outcomes*. Parte 1: Diseñar el camino hacia datos confiables.
> **Microproyecto:** Árbol de resultados y medidas de valor.

**Estado:** ✅ hecho

## Objetivo

Conectar cada capacidad de datos con un resultado de negocio medible, acordado y firmado por su stakeholder, seguir el avance tanto en resultados de datos (medidos en el warehouse) como de negocio, e incorporar las medidas de valor al mapa de stakeholders del capítulo 2.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| Capacidades frente a resultados; hacen falta los dos, y primero va el resultado de negocio | Modelo resultado de negocio → capacidades → entregables → resultados de datos | [framework.py](framework.py) |
| Cinco componentes de una capacidad sólida | Aviso si a una capacidad le falta alguno (habilidades, procesos, tecnología, recursos o cultura) | [framework.py](framework.py) |
| Paso 1: resultado concreto (segundo nivel), no un objetivo genérico | Cada resultado lleva una métrica con línea base, objetivo, responsable y fecha | [inputs/outcomes.yaml](inputs/outcomes.yaml) |
| Paso 2: explicar *por qué* son las capacidades adecuadas | El campo `why` es obligatorio | [framework.py](framework.py) |
| Paso 3: entregables con hitos del tipo "6 de 6" | `done` / `total` por entregable, con plazos | [framework.py](framework.py) |
| Paso 4: el valor lo define el stakeholder y no cuenta hasta que lo firma | El valor sale de la data equity del capítulo 1; aviso si falta la firma | [run.py](run.py) |
| Paso 5: entregar de forma iterativa | Roadmap de entregables por resultado | [run.py](run.py) |
| Paso 6: informar del progreso al menos una vez al mes y explicar las desviaciones | Estado por resultado, entregables vencidos y avance esperado frente al real | [progress.py](progress.py) |
| Pasos 7 y 8: medir el éxito en resultados de datos y después en resultados de negocio | Resultados de datos medidos con los indicadores del warehouse (capítulo 4) | [progress.py](progress.py) |
| Barreras para lograr valor | Registro de las seis barreras del libro, con severidad y mitigación | [framework.py](framework.py) |
| Medidas de valor en el mapa de stakeholders y revisión trimestral (QBR) | Mapa del capítulo 2 ampliado con valor, y un QBR por stakeholder | [templates/value_map.md.j2](templates/value_map.md.j2) |

## Entregables (`outputs/`)

| Archivo | Contenido |
|---|---|
| `outcome_framework.md` | Los pasos 1-4, 7 y 8 de cada resultado |
| `progress_report.md` | Informe mensual: estado, hitos, resultados de datos medidos, desviaciones, barreras y avisos |
| `roadmap.png` | Entregables en el tiempo por resultado, con la fecha de corte |
| `value_map.md` | Mapa de stakeholders con valor y un QBR por stakeholder |

## Cómo ejecutarlo

```bash
uv run dglab build   # warehouse de la Fase 0 (una vez)
uv run python -m chapters.ch05_exito_y_resultados.run
uv run pytest chapters/ch05_exito_y_resultados
```

## Decisiones de modelado

- **El valor no se vuelve a estimar aquí.** Cada resultado apunta a líneas de data equity del capítulo 1 (`equity_lines`), así que hay una sola fuente de verdad. Si una línea no está validada en el capítulo 1, se avisa.
- **Errores frente a avisos.** La estructura rota impide ejecutar: ids repetidos, capacidades sin entregables, métricas sin responsable, objetivos que no mejoran la línea base o métricas de datos que ningún entregable produce. Lo que solo resta credibilidad se avisa: falta de firma, componentes ausentes o entregables sin resultado de datos.
- **Estado del resultado.** Rojo si hay entregables vencidos; amarillo si los hitos van más de medio hito por detrás de un avance lineal entre inicio y entrega; verde en otro caso.
- **Resultados de datos medidos, no declarados.** Se miden con los indicadores del capítulo 4 sobre el warehouse, así que cuando el capítulo 6 documente tablas o el capítulo 10 elimine duplicados, este informe lo reflejará sin tocarlo.
- **La fecha de corte (31/01/2027) es simulada.** Representa el primer informe mensual del programa, con algunos hitos ya completados.

## Conclusiones para NovaMercado

1. **Hay tres resultados con un valor total de US$ 2,47 M/año:** cliente único para la CMO (US$ 1,51 M), localización de PII para la DPO (US$ 0,35 M) y cifra única de ventas para el CFO (US$ 0,61 M).
2. **El resultado del CFO no tiene el valor firmado.** Hasta que lo firme no se puede presentar como éxito. Coincide con la barrera de "falta de apoyo" del registro.
3. **Hay dos resultados en rojo en el primer informe.** O1 tiene vencido el nombramiento de los stewards de cliente (D5), y O3 el linaje de ventas (D8). Hay que explicarlo en el comité con su causa raíz.
4. **Los resultados de datos medidos confirman la línea base:** 5,9 % de duplicados (objetivo 0,5 %), 0 % de tablas documentadas, 0 % de linaje y 93,1 % de controles superados (objetivo 99 %). Los capítulos 6 a 10 mueven estas cifras.
5. **Dos capacidades no tienen componente de cultura** (calidad de contacto y clasificación de PII). Sin un cambio en cómo trabaja el negocio, la herramienta sola no logra el resultado.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada

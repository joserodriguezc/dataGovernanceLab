# Capítulo 4: Establecer la línea base de la organización

> **Libro:** *Baseline Your Organization*. Parte 1: Diseñar el camino hacia datos confiables.
> **Microproyecto:** Evaluación de madurez de gestión de datos.

**Estado:** ✅ hecho

## Objetivo

Medir dónde está NovaMercado hoy en gestión de datos siguiendo los 10 pasos del libro, comunicar los resultados sin romper la colaboración entre áreas y dejar un plan de mejora con métricas cuya línea base sale de los datos reales.

## Ideas del capítulo que aplicamos

| Paso del libro | Cómo lo aplicamos | Módulo |
|---|---|---|
| #1 Alcance (toda la empresa, piloto o por oleadas) | Toda la empresa más la oficina de datos; aviso si falta algún dominio | [model.py](model.py) |
| #2 Stakeholders (RACI, quién participa y quién no) | Stewards de negocio y técnicos del capítulo 3; si un dominio no tiene stewards, se entrevista al ejecutivo | [survey.py](survey.py) |
| #3 Modelo de madurez con los niveles del libro (ad hoc → optimizado) | Modelo propio de 6 niveles y 8 dimensiones | [inputs/maturity_model.yaml](inputs/maturity_model.yaml) |
| #4 Ejecución: talleres por defecto y 1:1 para los escépticos; el riesgo de "gaming the system" | Respuestas simuladas con autoevaluación y consenso del taller; algunos dominios sesgan su autoevaluación | [survey.py](survey.py) |
| #5 Análisis cuantitativo (media simple) y cualitativo (temas, causas raíz, prioridades) | Medias por dimensión y unidad, detección de sesgo y agrupación de hallazgos en temas | [analysis.py](analysis.py) |
| Complemento: medir también la calidad real de los datos | Indicadores del warehouse que acotan el nivel que la evidencia respalda | [evidence.py](evidence.py) |
| #6 Comunicar los resultados agregados, no por área | Informe agregado para el comité e informe desagregado solo para uso interno | [templates/](templates/) |
| #7-#9 Plan (máximo 5 iniciativas), implantación y seguimiento con métricas | Plan ligado a los temas, con métricas cuya línea base sale del warehouse | [model.py](model.py) |
| #10 Reevaluación anual y ante cambios significativos | Próxima fecha y disparadores (adquisición, desinversión, NovaPay) | [inputs/assessment.yaml](inputs/assessment.yaml) |

## Entregables (`outputs/`)

| Archivo | Contenido | Audiencia |
|---|---|---|
| `assessment_plan.md` | Motivos, alcance, RACI, participantes, calendario por fases, email de lanzamiento y agenda del taller | Comité de datos y participantes |
| `maturity_report.md` | Madurez de la empresa por dimensión, evidencia, temas y plan | Comité, comité de dirección y consejo |
| `maturity_by_dimension.png` | Nivel actual frente a objetivo, con el máximo que respalda la evidencia | Comité |
| `maturity_internal.md` | Matriz unidad × dimensión, sesgo de la autoevaluación y participación | **Solo oficina de datos** |
| `improvement_plan.md` | Plan, métricas con su línea base, controles de calidad, reevaluación y medidas de éxito | Comité de datos |
| `responses.csv` | Respuestas (autoevaluación y consenso) por participante y pregunta | Oficina de datos |

## Cómo ejecutarlo

```bash
uv run dglab build   # warehouse de la Fase 0 (una vez)
uv run python -m chapters.ch04_linea_base_madurez.run
uv run pytest chapters/ch04_linea_base_madurez
```

## Decisiones de modelado

- **Modelo propio, no DCAM ni otro estándar.** Así puede publicarse en el laboratorio. El libro recomienda usar un modelo reconocido la primera vez que una empresa se evalúa.
- **Respuestas simuladas, con su lógica explícita en `assessment.yaml`.** El nivel real de cada unidad y dimensión es su nivel base más el ajuste de la dimensión más ruido. El taller refleja ese nivel; la autoevaluación le suma el sesgo de cada dominio. Se reporta siempre el **consenso del taller**.
- **Sesgo:** si la autoevaluación media se aleja 0,75 niveles o más del consenso.
- **Evidencia del warehouse.** Reglas explícitas acotan el nivel máximo de algunas dimensiones: sin tablas documentadas, metadatos y privacidad no pasan de 2; sin linaje documentado, linaje no pasa de 2; con más de un 1 % de teléfonos duplicados en el CRM, datos maestros no pasa de 2; con algún control de calidad por debajo del 98 %, calidad no pasa de 3. La tabla de linaje `meta.lineage_edges` la creará el capítulo 7.
- **Nombre del nivel:** se toma la parte entera de la puntuación, así que 1,9 sigue siendo *Ad hoc* porque aún no alcanza el nivel 2.
- **Gráfico de puntos** en lugar del radar previsto en el plan: compara mejor el nivel actual con el objetivo.

## Conclusiones para NovaMercado

1. **La madurez de la empresa es 2,2 sobre 6 (Básico).** Las dimensiones más débiles son linaje (1,6), metadatos y datos maestros (1,9 cada una). Coinciden con los temas prioritarios de los talleres: definiciones de negocio e identidad de cliente.
2. **Privacidad y seguridad puntúa 2,4, pero la evidencia solo respalda un 2.** Ninguna tabla está documentada, así que nadie puede saber dónde está la PII. Hay que revisar esta puntuación con los participantes antes de presentarla.
3. **Ventas se sobrevalora (+1,0) y Tiendas se infravalora (−0,84)** en la autoevaluación: es el caso de "gaming the system" del libro. Por eso se reporta el consenso del taller y el informe se comunica agregado.
4. **Proveedores no tiene stewards**, así que se entrevista al Director de Compras. Su media interna (1,3) es la más baja, lo que encaja con la iniciativa 5 del plan.
5. **La línea base de las métricas sale de los datos:** 0 % de tablas documentadas, 5,9 % de teléfonos duplicados en el CRM y 93,1 % de controles de calidad superados. Son las cifras contra las que se medirán los capítulos 6, 8 y 10.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada

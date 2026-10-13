# Capítulo 14: Automatización de datos para el impacto

> **Libro:** *Data Automation for Impact and More Powerful Results*. Parte 3: Generar confianza con entregas basadas en valor.
> **Microproyecto:** Automatizar un proceso manual con ROI medido.

**Estado:** ✅ hecho

## Objetivo

Aplicar los 6 pasos del libro a un proceso manual concreto de NovaMercado: el **informe semanal de ventas por región**, que los analistas montan a mano y que no cuadra con la cifra oficial. Hay que elegir el enfoque por ROI, automatizarlo de verdad con monitorización y alertas, y evaluar dos proveedores externos de enriquecimiento de direcciones antes de comprar.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| Paso 1: objetivos (qué lograr, qué mantener, retos, cómo se ve el éxito) | Objetivos del informe regional | [inputs/automation.yaml](inputs/automation.yaml) |
| Paso 2: proceso actual y pasos manuales | 6 pasos con sus minutos y si son propensos a errores | [inputs/automation.yaml](inputs/automation.yaml) |
| Paso 3: enunciado del problema acordado | Antes de proponer soluciones | [inputs/automation.yaml](inputs/automation.yaml) |
| Paso 4: enfoques A/B/C y ROI con la fórmula del libro | Horas eliminadas × coste − mantenimiento; coste puntual de construcción | [roi.py](roi.py) |
| Tipos de automatización: integración, transformación, análisis e informes, monitorización y alertas | El enfoque C los combina | [automation.py](automation.py) |
| Paso 5: ejecutar | Informe semanal por región generado sobre el warehouse, con región por datos de referencia | [automation.py](automation.py) |
| Monitorización y alertas (observabilidad de datos) | Caídas de volumen anómalas, ventas sin región asignable e importes negativos | [automation.py](automation.py) |
| Paso 6: medir e informar | Tiempo antes y después, cuadre con la cifra oficial y horas ahorradas | [templates/automation.md.j2](templates/automation.md.j2) |
| Enriquecimiento de terceros: evaluar calidad, cobertura y precio antes de comprar | Dos proveedores simulados contrastados con el código postal real de cada persona | [enrichment.py](enrichment.py) |
| Dónde empezar: dominios de cliente y de operaciones | Siguientes candidatos con lo que ya hay en el laboratorio | [templates/automation.md.j2](templates/automation.md.j2) |

## Entregables (`outputs/`)

| Archivo | Contenido |
|---|---|
| `automation.md` | Los 6 pasos, los enfoques con su ROI, la ejecución, las alertas, la medición, la evaluación de proveedores y los siguientes candidatos |
| `roi_by_approach.png` | Beneficio neto a 3 años de cada enfoque |
| `weekly_regional_sales.csv` | El informe automatizado: venta neta por semana y región |
| `alerts.csv` | Alertas de monitorización |

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch11_operaciones_datos.pipeline   # incluye los datos de referencia (cap. 10)
uv run python -m chapters.ch14_automatizacion.run
uv run pytest chapters/ch14_automatizacion
```

## Decisiones de modelado

- **El informe automatizado reutiliza la regla oficial** (sin cancelados ni devueltos) y la región de los datos de referencia del capítulo 10. Por eso cuadra al céntimo con `curated.agg_sales_daily_channel`, que era el problema del proceso manual.
- **Caídas de volumen: umbral estadístico, no fijo.** La primera versión avisaba si la venta caía un 30 % frente a la media de 4 semanas, y dio 109 alertas en 92 semanas, porque la venta regional varía un ±40 % de forma natural. Ahora avisa si cae más de 2 desviaciones típicas bajo la media de las 8 semanas anteriores, y se excluyen la primera y la última semana, que están incompletas: quedan 12 alertas. Demasiadas alertas acaban ignoradas.
- **Las alertas de importes negativos se mantienen** (67 semanas) porque reflejan un defecto real, el DQ-08 del capítulo 8. Se apagarán solas cuando se corrija en el POS.
- **Los proveedores se simulan, la evaluación no.** Cada proveedor devuelve códigos postales con su cobertura y exactitud. Lo que devuelven se compara con el código postal real de la persona, obtenido del solucionario a través del CRM o la tarjeta de tienda. Se elige por **coste por corrección neta**, donde cada dato erróneo cuenta en contra.

## Conclusiones para NovaMercado

1. **381 horas al año pasan a 0,02 segundos por ejecución,** y el informe cuadra con la cifra oficial (diferencia de US$ 0,00) por primera vez.
2. **El enfoque C es el mejor:** ahorra US$ 13.560 al año y tiene un ROI del 465 % a 3 años. El beneficio no está en una sola automatización, sino en combinar integración, transformación, informes y alertas, como dice el libro.
3. **La monitorización detecta problemas que antes nadie veía:** 12 caídas de venta anómalas por región, 16 semanas con más del 2 % de la venta online sin región (códigos postales inválidos) y los precios negativos del POS.
4. **El proveedor más barato no es el mejor.** DirecPostal cuesta la mitad por registro, pero devuelve 176 códigos postales erróneos, válidos en apariencia y que ninguna regla de calidad detectaría después. GeoCalidad corrige 438 pedidos con solo 12 errores.
5. **El ROI de este proceso es modesto en dinero,** pero libera a los analistas para analizar anomalías en lugar de cuadrar hojas de cálculo. Hay que medirlo también con una encuesta antes y después.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada
- [x] Paso añadido al recorrido del README raíz

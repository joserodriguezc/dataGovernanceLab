# Capítulo 14: Automatización de datos para el impacto

> **Libro:** *Data Automation for Impact and More Powerful Results*. Parte 3: Generar confianza con entregas basadas en valor.
> **Microproyecto:** Automatizar un proceso manual con ROI medido.

**Estado:** pendiente

## Objetivo
Elegir un proceso manual de NovaMercado, automatizarlo y medir el beneficio con los 6 pasos del libro.

## Conceptos del libro que se aplican
- Qué es la automatización de datos y sus tipos
- Beneficios y cómo medirlos
- Los 6 pasos: objetivos, proceso actual, problema, enfoque y ROI, ejecución, medición
- Enriquecimiento de terceros
- Ejemplos en los dominios de cliente y operaciones

## Entregables
- El proceso manual simulado y su versión automatizada
- Enriquecimiento de terceros simulado (p. ej., códigos postales)
- `outputs/automation_roi.md`

## Dependencias
Capítulo 8, Capítulo 11.

## Cómo ejecutarlo
```bash
uv run python chapters/ch14_automatizacion/run.py
uv run pytest chapters/ch14_automatizacion
```

## Definición de hecho
- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

# Capítulo 4: Establecer la línea base de la organización

> **Libro:** *Baseline Your Organization*. Parte 1: Diseñar el camino hacia datos confiables.
> **Microproyecto:** Evaluación de madurez de gestión de datos.

**Estado:** pendiente

## Objetivo

Medir dónde está NovaMercado hoy con un modelo de madurez, siguiendo los 10 pasos del libro, y comunicar los resultados.

## Conceptos del libro que se aplican

- Qué es un modelo de madurez y por qué establecer una línea base
- #1 alcance, #2 stakeholders, #3 selección del modelo
- #4 ejecución y recogida de datos, #5 análisis
- #6 comunicación de resultados agregados y desagregados
- #7 plan, #8 implementación, #9 seguimiento y #10 reevaluación

## Entregables

- `inputs/maturity_model.yaml`: dimensiones, preguntas y niveles 1–5
- Respuestas sintéticas por área de negocio
- `outputs/maturity_radar.png` y `outputs/maturity_report.md`

## Dependencias

Fase 0 (datos sintéticos), Capítulo 2.

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch04_linea_base_madurez.run
uv run pytest chapters/ch04_linea_base_madurez
```

## Definición de hecho

- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

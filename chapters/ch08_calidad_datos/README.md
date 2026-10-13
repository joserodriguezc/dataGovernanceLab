# Capítulo 8: Calidad de datos

> **Libro:** *Data Quality*. Parte 2: Las capacidades de gobierno de datos en profundidad.
> **Microproyecto:** Calidad de datos y certificación.

**Estado:** pendiente

## Objetivo
Poder responder con evidencia a *¿puedo confiar en este dato?* y certificar los datasets que cumplen.

## Conceptos del libro que se aplican
- Estrategia y habilitación de la calidad de datos
- Profiling, limpieza, validación y estandarización, enriquecimiento
- Bucles de feedback, gestión de excepciones y remediación
- Datos certificados y transparencia
- Peticiones en tiempo real e integración con otros sistemas

## Entregables
- Profiling de las tablas raw
- Reglas de validación con pandera por dimensión de calidad
- `outputs/dq_scorecard.md` y `outputs/dq_issues.csv`
- Marca de *dato certificado* en el catálogo del capítulo 6

## Dependencias
Fase 0 (datos sintéticos), Capítulo 6, Capítulo 7.

## Cómo ejecutarlo
```bash
uv run python chapters/ch08_calidad_datos/run.py
uv run pytest chapters/ch08_calidad_datos
```

## Definición de hecho
- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

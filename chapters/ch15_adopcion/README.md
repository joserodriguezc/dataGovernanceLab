# Capítulo 15: Adopción que impulsa el negocio

> **Libro:** *Adoption That Drives Business Success*. Parte 3: Generar confianza con entregas basadas en valor.
> **Microproyecto:** Medición de la adopción.

**Estado:** pendiente

## Objetivo

Medir la adopción de las capacidades de datos, cuantificar el coste de la baja adopción y diseñar el roadmap.

## Conceptos del libro que se aplican

- Empezar por el porqué, facilitar el uso, la cultura y las barreras
- Costes cuantitativos y cualitativos de la baja adopción
- Por qué falla la adopción: la solución, la empresa o tú
- Recuperarse de lanzamientos fallidos
- Post-despliegue: roadmap, monitorización y adopción en el SDLC

## Entregables

- Logs de uso sintéticos del catálogo y del marketplace
- KPIs de adopción (usuarios activos, retención, cobertura)
- `outputs/adoption_report.md` con el coste de la baja adopción y el roadmap

## Dependencias

Fase 0 (datos sintéticos), Capítulo 6.

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch15_adopcion.run
uv run pytest chapters/ch15_adopcion
```

## Definición de hecho

- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

# Capítulo 2: Construir una coalición de defensores

> **Libro:** *How to Build a Coalition of Advocates*. Parte 1: Diseñar el camino hacia datos confiables.
> **Microproyecto:** Mapa de stakeholders y evaluación del sponsor.

**Estado:** pendiente

## Objetivo
Identificar a los stakeholders de NovaMercado, mapearlos y elegir al sponsor ejecutivo con criterios explícitos.

## Conceptos del libro que se aplican
- Construir confianza relación a relación
- Identificar stakeholders y construir un mapa de stakeholders
- Identificar y evaluar sponsors; caso de negocio para conseguir uno
- Traducir a resultados de negocio
- Bucles de feedback, roles clave de apoyo y apoyo de toda la organización

## Entregables
- `inputs/stakeholders.yaml`: influencia, interés, actitud y dominio
- `outputs/stakeholder_map.png`: matriz poder/interés
- `outputs/sponsor_scoring.md`: ranking de candidatos a sponsor
- `outputs/feedback_loops.md`: plan de cadencias y canales

## Dependencias
Ninguna. Se puede desarrollar de forma independiente.

## Cómo ejecutarlo
```bash
uv run python chapters/ch02_coalicion_defensores/run.py
uv run pytest chapters/ch02_coalicion_defensores
```

## Definición de hecho
- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

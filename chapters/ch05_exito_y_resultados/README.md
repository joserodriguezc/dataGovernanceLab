# Capítulo 5: Definir el éxito y alinearse en resultados

> **Libro:** *Defining Success and Aligning on Outcomes*. Parte 1: Diseñar el camino hacia datos confiables.
> **Microproyecto:** Árbol de outcomes y medidas de valor.

**Estado:** pendiente

## Objetivo

Conectar cada capacidad de datos con un resultado de negocio medible y asignar las medidas de valor a los stakeholders.

## Conceptos del libro que se aplican

- Capacidades vs outcomes: hacen falta ambos
- Qué es el éxito y cómo definir valor
- Los 8 pasos de alineación: del outcome de negocio a medir el éxito
- Barreras para lograr valor de negocio
- Incorporar medidas de valor al mapa de stakeholders

## Entregables

- `inputs/outcomes.yaml`: outcome → capacidad → entregable → métrica
- Modelo pydantic que valida el árbol (sin huérfanos ni métricas sin dueño)
- `outputs/outcome_tree.md` (diagrama Mermaid)
- `outputs/value_measures.md` cruzado con el mapa del capítulo 2

## Dependencias

Capítulo 2.

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch05_exito_y_resultados.run
uv run pytest chapters/ch05_exito_y_resultados
```

## Definición de hecho

- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

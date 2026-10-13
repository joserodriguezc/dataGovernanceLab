# Capítulo 7: Metadatos técnicos y linaje de datos

> **Libro:** *Technical Metadata and Data Lineage*. Parte 2: Las capacidades de gobierno de datos en profundidad.
> **Microproyecto:** Linaje de datos a nivel de columna.

**Estado:** pendiente

## Objetivo
Reconstruir la cadena de suministro de datos de NovaMercado a partir del SQL de las transformaciones y usarla para analizar el impacto de un cambio.

## Conceptos del libro que se aplican
- Metadatos técnicos: valor, métricas, responsables y madurez
- Linaje: por qué importa, cómo medirlo y cómo usarlo
- Construir una capacidad de linaje óptima

## Entregables
- SQL de transformaciones raw → staging → curated
- `lineage.py`: parseo con sqlglot y grafo con networkx
- Análisis de impacto (*¿qué se rompe si cambia esta columna?*)
- `outputs/lineage.md` (Mermaid) y métricas de cobertura

## Dependencias
Fase 0 (datos sintéticos), Capítulo 6.

## Cómo ejecutarlo
```bash
uv run python chapters/ch07_metadatos_tecnicos_linaje/run.py
uv run pytest chapters/ch07_metadatos_tecnicos_linaje
```

## Definición de hecho
- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

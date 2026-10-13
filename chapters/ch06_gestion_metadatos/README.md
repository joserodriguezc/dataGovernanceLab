# Capítulo 6: Gestión de metadatos

> **Libro:** *Metadata Management*. Parte 2: Las capacidades de gobierno de datos en profundidad.
> **Microproyecto:** Glosario de negocio y catálogo de datos.

**Estado:** pendiente

## Objetivo
Responder a dónde están los datos, de quién son, cómo se clasifican y si se pueden usar, con un glosario y un catálogo sobre el warehouse.

## Conceptos del libro que se aplican
- Qué es la gestión de metadatos y por qué importa
- Estándares de metadatos, glosario de negocio y catálogo de datos
- Data marketplace: qué es, qué contiene y por qué importa
- Medir outcomes y ROI

## Entregables
- `inputs/business_glossary.yaml`
- `catalog.py`: extrae el esquema de DuckDB y lo enriquece con owner y clasificación
- Detección y clasificación de PII
- Chequeo de estándares de metadatos (descripciones, owners)
- CLI de búsqueda tipo marketplace

## Dependencias
Fase 0 (datos sintéticos).

## Cómo ejecutarlo
```bash
uv run python chapters/ch06_gestion_metadatos/run.py
uv run pytest chapters/ch06_gestion_metadatos
```

## Definición de hecho
- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

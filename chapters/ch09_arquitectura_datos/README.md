# Capítulo 9: Arquitectura de datos

> **Libro:** *Data Architecture*. Parte 2: Las capacidades de gobierno de datos en profundidad.
> **Microproyecto:** Principios de arquitectura y linter de estándares.

**Estado:** pendiente

## Objetivo
Documentar la arquitectura as-is y to-be de NovaMercado y hacer cumplir los estándares de forma automática.

## Conceptos del libro que se aplican
- Qué es la arquitectura de datos; victorias sencillas
- Por qué se pasa por alto y cómo medir su éxito
- Programa de arquitectura y modelado as-is / to-be
- Principios de diseño y estándares arquitectónicos
- Integración con la arquitectura de negocio y de TI, y con el SDLC

## Entregables
- `outputs/architecture_as_is.md` y `outputs/architecture_to_be.md` (Mermaid)
- `inputs/design_principles.yaml`
- `arch_lint.py`: valida nomenclatura, claves y capas en DuckDB

## Dependencias
Fase 0 (datos sintéticos), Capítulo 7.

## Cómo ejecutarlo
```bash
uv run python chapters/ch09_arquitectura_datos/run.py
uv run pytest chapters/ch09_arquitectura_datos
```

## Definición de hecho
- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

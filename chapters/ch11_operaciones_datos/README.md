# Capítulo 11: Operaciones de datos

> **Libro:** *Data Operations*. Parte 2: Las capacidades de gobierno de datos en profundidad.
> **Microproyecto:** Operaciones de datos con SLAs.

**Estado:** pendiente

## Objetivo
Hacer visibles las operaciones de datos: ejecuciones, SLAs e incidentes.

## Conceptos del libro que se aplican
- Operaciones de datos vs operaciones de TI, y su colaboración
- Capacidades de operaciones de datos
- El héroe silencioso del gobierno de datos; hacerlo visible
- Construir la capacidad y prepararla para el éxito

## Entregables
- `orchestrator.py`: ejecuta los pipelines de los caps. 6–10 y registra cada ejecución
- `inputs/slas.yaml`
- Registro de incidentes y `outputs/ops_dashboard.md`

## Dependencias
Capítulo 6, Capítulo 7, Capítulo 8, Capítulo 10.

## Cómo ejecutarlo
```bash
uv run python chapters/ch11_operaciones_datos/run.py
uv run pytest chapters/ch11_operaciones_datos
```

## Definición de hecho
- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

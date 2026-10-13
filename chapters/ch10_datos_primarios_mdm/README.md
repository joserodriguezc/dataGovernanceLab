# Capítulo 10: Gestión de datos primarios (maestros)

> **Libro:** *Primary Data Management*. Parte 2: Las capacidades de gobierno de datos en profundidad.
> **Microproyecto:** Golden record de cliente.

**Estado:** pendiente

## Objetivo
Unificar los clientes duplicados entre CRM, e-commerce y POS en un registro maestro confiable.

## Conceptos del libro que se aplican
- Datos primarios vs datos de referencia
- Tipos: cliente, producto, proveedor y contacto
- Deduplicación, definiciones comunes y atribución de la fuente dorada
- Jerarquías, trust logic, integración y enriquecimiento de terceros
- CRM vs PDM
- Caso de negocio, arquitectura conceptual y beneficios

## Entregables
- `matching.py`: matching difuso con rapidfuzz
- `inputs/survivorship_rules.yaml`: trust logic por atributo
- Tabla `curated.customer_golden` con jerarquía de hogares
- `outputs/mdm_report.md`: tasa de duplicados antes y después

## Dependencias
Fase 0 (datos sintéticos), Capítulo 8.

## Cómo ejecutarlo
```bash
uv run python chapters/ch10_datos_primarios_mdm/run.py
uv run pytest chapters/ch10_datos_primarios_mdm
```

## Definición de hecho
- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

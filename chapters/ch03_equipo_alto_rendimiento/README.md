# Capítulo 3: Construir un equipo de alto rendimiento

> **Libro:** *Building a High-Performing Team*. Parte 1: Diseñar el camino hacia datos confiables.
> **Microproyecto:** Diseño organizativo del equipo de datos.

**Estado:** pendiente

## Objetivo
Elegir el modelo organizativo adecuado para NovaMercado y definir roles, responsabilidades y el ritmo de los foros de gobierno.

## Conceptos del libro que se aplican
- Optimizar para resultados; funciones core y product management
- Tres modelos: oficina del CDO, hub & spoke y centralizado
- Roles: CDO vs CDAO, gestión de datos, líder de soluciones de datos
- Consideraciones de IA
- Comité y consejo empresarial de datos
- Roles funcionales: domain leader, steward de negocio y técnico
- Desarrollo de talento

## Entregables
- `inputs/org_criteria.yaml`: criterios ponderados para elegir el modelo
- `outputs/org_model_recommendation.md`
- `outputs/raci.csv`: matriz RACI por dominio y actividad
- `outputs/governance_calendar.md`: calendario del comité y del consejo

## Dependencias
Capítulo 2.

## Cómo ejecutarlo
```bash
uv run python chapters/ch03_equipo_alto_rendimiento/run.py
uv run pytest chapters/ch03_equipo_alto_rendimiento
```

## Definición de hecho
- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

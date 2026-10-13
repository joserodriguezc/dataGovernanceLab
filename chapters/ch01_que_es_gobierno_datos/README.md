# Capítulo 1: ¿Qué es el gobierno de datos?

> **Libro:** *What Is Data Governance?*. Parte 1: Diseñar el camino hacia datos confiables.
> **Microproyecto:** Charter del programa y caso de negocio.

**Estado:** pendiente

## Objetivo
Definir qué es (y qué no es) el gobierno de datos para NovaMercado y justificar el programa como habilitador de valor de negocio, no como centro de coste.

## Conceptos del libro que se aplican
- Qué impulsa la necesidad de gobierno de datos
- Qué no es el gobierno de datos; su objetivo es crear valor de negocio
- Componentes: políticas y estándares, roles, foros de gobierno, reporting
- Definir valor: con quién reunirse, el *why statement* y cómo adaptar el mensaje
- Misión de la oficina del CDAO y del programa de gobierno
- Caso de negocio y cuándo lanzar (o esperar)

## Entregables
- `inputs/business_case.yaml`: supuestos de costes y beneficios
- `business_case.py`: calculadora de ROI, payback y VAN
- `outputs/charter.md`: why statement, misión, componentes y timeline

## Dependencias
Ninguna. Se puede desarrollar de forma independiente.

## Cómo ejecutarlo
```bash
uv run python chapters/ch01_que_es_gobierno_datos/run.py
uv run pytest chapters/ch01_que_es_gobierno_datos
```

## Definición de hecho
- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

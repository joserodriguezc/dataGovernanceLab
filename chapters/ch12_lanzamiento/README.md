# Capítulo 12: Lanzar con fuerza

> **Libro:** *Launch Powerfully*. Parte 3: Generar confianza con entregas basadas en valor.
> **Microproyecto:** Kit de lanzamiento del programa.

**Estado:** pendiente

## Objetivo

Evaluar si NovaMercado está lista para lanzar el programa y preparar el mensaje.

## Conceptos del libro que se aplican

- Evaluar la preparación para el lanzamiento; línea base común
- Mensaje central: visión, as-is vs to-be y concreción
- Memo narrativo y diseño basado en outcomes
- Proceso repetible, bucles de feedback y gestión de expectativas

## Entregables

- `inputs/readiness.yaml` y scoring de preparación
- `outputs/narrative_memo.md`, generado con plantilla jinja2 a partir de los caps. 1–5

## Dependencias

Capítulo 1, Capítulo 2, Capítulo 3, Capítulo 4, Capítulo 5.

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch12_lanzamiento.run
uv run pytest chapters/ch12_lanzamiento
```

## Definición de hecho

- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

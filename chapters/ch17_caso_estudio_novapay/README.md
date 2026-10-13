# Capítulo 17: Caso de estudio: institución financiera

> **Libro:** *Case Study – Financial Institution*. Parte 4: Caso de estudio.
> **Microproyecto:** NovaPay de punta a punta.

**Estado:** pendiente

## Objetivo
Aplicar el programa completo a NovaPay, la filial financiera regulada de NovaMercado, como en el caso del libro.

## Conceptos del libro que se aplican
- Escenario: entidad bancaria altamente regulada
- Descubrimiento inicial, temas clave y quick wins
- Mensajes al comité ejecutivo y al regulador
- Diseño para la entrega iterativa con impacto
- Resultados

## Entregables
- Datos sintéticos de NovaPay (cuentas, transacciones, KYC)
- Ejecución de los microproyectos sobre NovaPay
- `outputs/executive_message.md` y `outputs/regulator_message.md`
- `outputs/results.md`

## Dependencias
Todos los capítulos anteriores (1–16).

## Cómo ejecutarlo
```bash
uv run python chapters/ch17_caso_estudio_novapay/run.py
uv run pytest chapters/ch17_caso_estudio_novapay
```

## Definición de hecho
- [ ] `run.py` genera todos los entregables en `outputs/`
- [ ] Tests en verde
- [ ] Este README documenta las decisiones y las conclusiones
- [ ] Checklist de `PLAN.md` actualizada

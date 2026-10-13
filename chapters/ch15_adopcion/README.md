# Capítulo 15: Adopción que impulsa el negocio

> **Libro:** *Adoption That Drives Business Success*. Parte 3: Generar confianza con entregas basadas en valor.
> **Microproyecto:** Medición de la adopción.

**Estado:** ✅ hecho

## Objetivo

Medir si las soluciones de datos de NovaMercado se usan de verdad, cuantificar lo que cuesta que no se usen, diagnosticar por qué fracasa una adopción y planificar la adopción después de la salida en vivo. Se comparan cuatro soluciones; una de ellas es un **lanzamiento fallido** a propósito: la plataforma de visualización que solo usa el equipo de datos, el ejemplo del libro.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| Medir la adopción, no la salida en vivo | Usuarios activos al mes, adopción frente a usuarios objetivo, retención y departamentos con uso | [usage.py](usage.py) |
| La baja adopción es cara: inversión desperdiciada y esfuerzo duplicado | Inversión anual sin aprovechar y horas que se siguen dedicando al método anterior | [diagnosis.py](diagnosis.py) |
| Costes cualitativos (frustración, resistencia, pérdida de confianza) | Explicados en el informe junto a los cuantitativos | [templates/adoption.md.j2](templates/adoption.md.j2) |
| ¿Por qué falla? La solución, la empresa o el líder | Diagnóstico con una encuesta que cubre las tres causas, con una acción por cada punto débil | [diagnosis.py](diagnosis.py) |
| Recuperarse de un lanzamiento fallido: causa raíz, colaboración y campeones | Plan de recuperación con un piloto en un solo grupo | [templates/adoption.md.j2](templates/adoption.md.j2) |
| Después de la salida en vivo: hoja de ruta, hipercuidado y monitorización | Onboarding por grupo con su valor esperado en horas y dólares | [inputs/adoption.yaml](inputs/adoption.yaml) |
| Integrar la adopción en el SDLC | Prácticas que se apoyan en los capítulos 8 y 9 | [templates/adoption.md.j2](templates/adoption.md.j2) |

## Entregables (`outputs/`)

| Archivo | Contenido |
|---|---|
| `adoption.md` | KPI de adopción, adopción por departamento, coste de la baja adopción, diagnóstico y recuperación, hoja de ruta y adopción en el SDLC |
| `monthly_active_users.png` | Usuarios activos al mes de cada solución desde su salida en vivo |
| `usage_log.csv` | Logs de uso simulados (usuario, departamento, solución y mes) |

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch15_adopcion.run
uv run pytest chapters/ch15_adopcion
```

No necesita el warehouse.

## Decisiones de modelado

- **Los logs de uso son simulados, con una lógica explícita por solución** en `adoption.yaml`: qué parte de los usuarios objetivo la adopta, la probabilidad de usarla cada mes y el abandono mensual, que puede ser distinto en el equipo de datos. La primera versión simulaba la adopción semana a semana sin abandono y casi todo el mundo acababa adoptándolo todo (100 %), lo que no era creíble.
- **Adopción = usuarios activos el último mes ÷ usuarios objetivo.** Retención = media de los usuarios activos un mes que siguen activos al siguiente. Se considera adoptada con al menos un 60 % de adopción y un 70 % de retención.
- **Coste de la baja adopción** = (construcción ÷ 3 años + operación anual) × parte no adoptada, más las horas que siguen yendo al método anterior por el coste por hora.
- **Diagnóstico:** cualquier dimensión de la encuesta por debajo de 3 sobre 5 es una causa, agrupada en la solución, la empresa o el líder, con su acción.

## Conclusiones para NovaMercado

1. **Tres de cuatro soluciones están adoptadas:** el catálogo (62 %), el cliente único (60 %) y el informe semanal (90 %, con una retención del 94 %). Las soluciones construidas sobre una necesidad acordada (capítulos 13 y 14) se adoptan mejor.
2. **La plataforma de visualización es un lanzamiento fallido de libro:** 14 % de adopción y 63 % de retención. El 67 % del equipo de datos la usa, pero solo el 5-7 % del resto de departamentos. Cuesta **US$ 473.496 al año** entre la inversión que no se aprovecha y las horas que se siguen dedicando a hojas de cálculo.
3. **Falla por las tres causas a la vez:** la solución (encaje en el flujo de trabajo 2,1, usabilidad 2,4), la empresa (la dirección no la usa, 1,8) y el líder (2,9). La recuperación empieza con un piloto en Finanzas, que está en la hoja de ruta, y no con otra campaña para todos.
4. **Incluso las soluciones adoptadas dejan valor sin capturar:** el 40 % de los usuarios objetivo del cliente único sigue buscando en tres sistemas (US$ 148.427 al año). La hoja de ruta incorpora a Atención al cliente con 4 semanas de hipercuidado.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada
- [x] Paso añadido al recorrido del README raíz

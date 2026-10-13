# Capítulo 3: Construir un equipo de alto rendimiento

> **Libro:** *Building a High-Performing Team*. Parte 1: Diseñar el camino hacia datos confiables.
> **Microproyecto:** Diseño organizativo del equipo de datos.

**Estado:** ✅ hecho

## Objetivo

Elegir el modelo organizativo adecuado para NovaMercado y definir los roles, las responsabilidades, el plan de contratación y el ritmo de los foros de gobierno, empezando por los resultados que debe lograr el equipo.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| Diseñar empezando por los resultados: los 10 resultados habituales de un equipo de datos | Se eligen y priorizan los resultados, justificando también los descartados | [org_model.py](org_model.py) |
| Tres modelos (federado, hub and spoke, centralizado) y cuándo elegir cada uno | Selector basado en reglas con horizonte, evolución y requisitos previos | [org_model.py](org_model.py) |
| Qué hace la oficina del CDO y qué hacen las áreas en cada modelo | Matriz de responsabilidades por modelo | [org_model.py](org_model.py) |
| Roles clave y su orden de contratación (gobierno → soluciones → arquitectura → ingeniería → operaciones) | Organigrama, plan de contratación y aviso si no se respeta el orden | [team.py](team.py) |
| Responsabilidad sobre los datos (no propiedad): ejecutivo de dominio, steward de negocio y steward técnico | Huecos por dominio y contraste con el EDG Scorecard del capítulo 1 | [team.py](team.py) |
| Consideraciones de IA | Checklist de las preguntas de gobierno de la IA y oportunidades de uso | [org_model.py](org_model.py) |
| Ritmo del negocio de datos: revisión del portfolio, consejo y comité, con sus cartas | Cartas, jerarquía sin ciclos, calendario a 12 meses e inventario del portfolio | [rhythm.py](rhythm.py) |
| Revisar resultados para el stakeholder, no resultados de datos | Aviso de los trabajos del portfolio que no tienen un resultado para su stakeholder | [rhythm.py](rhythm.py) |
| Desarrollo del talento: atraer, hacer crecer la cantera y formar | Matriz de habilidades con brechas (formar o contratar) y plan de talento | [team.py](team.py) |
| Matriz de responsabilidades | RACI con un único *Accountable* y aviso de los roles que no ejecutan nada | [raci.py](raci.py) |

## Entregables (`outputs/`)

| Archivo | Contenido |
|---|---|
| `org_model.md` | Resultados priorizados, funciones principales, modelo recomendado, matriz de responsabilidades e IA |
| `team_design.md` | Organigrama (Mermaid), roles, coste frente al caso de negocio, orden de contratación, roles por dominio, habilidades y plan de talento |
| `skills_heatmap.png` | Nivel de cada persona en cada habilidad |
| `raci.md` y `raci.csv` | Matriz RACI del programa |
| `governance_rhythm.md` | Jerarquía y cartas de los foros, calendario de 2027 e inventario del portfolio |

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch03_equipo_alto_rendimiento.run
uv run pytest chapters/ch03_equipo_alto_rendimiento
```

## Decisiones de modelado

- **Selector de modelo por reglas, no por puntuación.** El libro da criterios cualitativos claros, así que se codifican como reglas explícitas y auditables a partir de seis hechos de la organización (`org_facts`).
- **Coste del equipo frente al capítulo 1.** Las posiciones ya cubiertas se pagan con presupuesto existente. Las nuevas (en búsqueda y planificadas) se comparan con el presupuesto anual de construcción de la opción recomendada en el capítulo 1: construcción ÷ duración × 12.
- **Brecha de habilidades a nivel de equipo.** Una habilidad está cubierta si al menos dos personas llegan al objetivo. Si solo llega una, hay que formar a una segunda para no depender de ella. Si el mejor nivel queda a un punto del objetivo, se forma (*upskilling*); si queda más lejos, se contrata.
- **Calendario.** Si un foro se reúne cada N meses, la reunión cae el mismo día del mes; si ese día no existe (por ejemplo, el 31), pasa al último día del mes.

## Conclusiones para NovaMercado

1. **Centralizar durante 12-24 meses y después pasar a hub and spoke.** Las capacidades son inconsistentes y hay problemas graves de confianza (cifras de ventas, duplicados). Además, faltan líderes de datos fuertes en las áreas y la oficina del CDO aún no está consolidada.
2. **El plan de contratación cabe en el presupuesto.** Las posiciones nuevas cuestan US$ 1,56 M/año, el 97 % del presupuesto anual de construcción del capítulo 1. El margen para herramientas es muy estrecho: conviene revisarlo con el CFO.
3. **Faltan stewards en Producto y Proveedores.** En Proveedores se propone al Director de Compras como ejecutivo de dominio, que en el EDG Scorecard del capítulo 1 todavía figura como pendiente.
4. **Datos maestros (MDM) es la brecha crítica.** Nadie del equipo pasa del nivel 1, así que hay que contratar al responsable de datos maestros o incorporar experiencia externa. Metadatos y calidad se resuelven formando al equipo actual.
5. **Dos trabajos del portfolio no tienen un resultado para su stakeholder.** La migración del data warehouse a la nube, además, está bloqueada y compite por ingenieros con la vista única de cliente. Es la primera conversación para la revisión del portfolio con el CIO.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada

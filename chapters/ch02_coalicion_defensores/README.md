# Capítulo 2: Construir una coalición de defensores

> **Libro:** *How to Build a Coalition of Advocates*. Parte 1: Diseñar el camino hacia datos confiables.
> **Microproyecto:** Mapa de stakeholders y evaluación del sponsor.

**Estado:** ✅ hecho

## Objetivo

Identificar a los stakeholders de NovaMercado, mapear qué persiguen y cómo les ayudan los datos, elegir al sponsor ejecutivo con criterios explícitos y mantener viva la coalición con bucles de feedback y comunicación abierta.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| La confianza se construye relación a relación. Escuchar solo a los pares da una visión filtrada | Se registran sesiones en 5 direcciones (horizontal, arriba, abajo, transversal y hacia fuera) y se detectan los huecos | [stakeholders.py](stakeholders.py) |
| Stakeholders internos y externos con rol, salud de la relación, contribución y medidas de éxito | Registro validado (cada nivel debe corresponder a su tipo) | [stakeholders.py](stakeholders.py) |
| Mapa de stakeholders: objetivos → soluciones de datos → resultados de negocio | Plantilla del libro más el beneficiario final de la cadena de valor | [stakeholders.py](stakeholders.py) |
| Ir más allá de las *vanity metrics* (calidad, tiempo) hasta el impacto en el negocio | Cada resultado tiene un tipo, y se avisa si un grupo solo tiene métricas del dato | [stakeholders.py](stakeholders.py) |
| No todos los stakeholders pesan igual | Matriz de influencia e interés para priorizar (complemento propio, no está en el libro) | [run.py](run.py) |
| Características de un gran sponsor; el sponsor no es el CIO; al menos uno, idealmente dos | Puntuación ponderada; quedan excluidos el CIO y quien no reporta al CEO; se recomiendan dos | [sponsors.py](sponsors.py) |
| Caso de negocio para el dominio del sponsor, organizado por *tracks* | Se genera con la estructura del libro y se avisa si no es del dominio del sponsor recomendado | [sponsors.py](sponsors.py) |
| Bucles de feedback: señales de que el ritmo del comité falla (delegación, peticiones fuera de ciclo, silencio) | Detección automática a partir del registro de reuniones | [feedback.py](feedback.py) |
| Apoyo de toda la organización: mostrar lo hecho y explicar qué podrá hacer cada empleado | Cada comunicación exige un "qué podrás hacer" y un "por qué te importa" | [feedback.py](feedback.py) |

## Entregables (`outputs/`)

| Archivo | Contenido |
|---|---|
| `stakeholder_register.md` | Cobertura de la escucha, priorización por cuadrantes y registro interno y externo |
| `stakeholder_matrix.png` | Matriz de influencia e interés, con la salud de la relación indicada por color y forma |
| `stakeholder_map.md` | Mapa de stakeholders con avisos de *vanity metrics* y preguntas para mantenerlo |
| `sponsor_assessment.md` | Puntuación de sponsors, recomendación, dominio piloto y caso de negocio por tracks |
| `coalition_plan.md` | Socios clave, pulso del comité con sus señales y acciones, y plan de comunicación |

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch02_coalicion_defensores.run
uv run pytest chapters/ch02_coalicion_defensores
```

## Decisiones de modelado

- **Puntuación del sponsor** de 0 a 100, a partir de la media ponderada de los 5 criterios del libro. Pesan más las necesidades urgentes de datos (×2), porque el mejor sponsor es quien tiene un problema que los datos resuelven, y el impacto final y el respaldo del CEO (×1,5).
- **Reglas de exclusión** antes de puntuar: el CIO nunca es sponsor y el candidato debe reportar al CEO. Así, el Director de Compras (55 puntos) queda fuera aunque supere al Director Comercial (39), que sí es elegible.
- **Señales del comité**, con umbrales configurables en `coalition.yaml`: hay cambio de membresía si un miembro delega 2 de las últimas 3 reuniones, hay que verse más si llegan 4 o más peticiones fuera de ciclo, y hay silencio si se hace como mucho una pregunta y no hay ninguna petición.

## Conclusiones para NovaMercado

1. **La CMO es la sponsor principal (91/100) y el CFO el secundario (80/100).** El dominio piloto es *Cliente*, que concentra las líneas de mayor valor del capítulo 1: vista única de cliente, PII sin clasificar y duplicados.
2. **Falta escuchar hacia fuera.** La sesión con el proveedor del CRM aún está planificada; sin ella falta la perspectiva externa.
3. **Dos grupos tienen solo *vanity metrics*.** El Director Comercial (completitud de atributos) y el CISO (cobertura de controles) no tienen un resultado de negocio comprometido. Hay que traducirlas a margen y a riesgo evitado.
4. **El comité da dos señales.** El Director Comercial ha delegado en las dos últimas reuniones, así que toca una reunión 1:1. Las peticiones fuera de ciclo subieron a 5, así que conviene pasar a una cadencia bimestral o enviar una actualización intermedia.
5. **Los directores regionales son el único grupo con relación negativa.** Desconfían de las cifras de ventas, y la cifra única de ventas del CFO es la entrega que puede convertirlos en defensores.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada

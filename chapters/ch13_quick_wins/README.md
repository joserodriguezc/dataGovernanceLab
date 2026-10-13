# Capítulo 13: Quick wins con impacto

> **Libro:** *Delivering Quick Wins with Impact*. Parte 3: Generar confianza con entregas basadas en valor.
> **Microproyecto:** Backlog priorizado de quick wins.

**Estado:** ✅ hecho

## Objetivo

Convertir lo que se escuchó a los stakeholders en un backlog de quick wins priorizado. Cada problema común tiene su tamaño **medido en los datos**, una solución rápida y otra de largo plazo, su resultado de negocio (capítulo 5) y un lugar en un roadmap ajustado a la capacidad del equipo. Además, se activa la propiedad de los datos y la mentalidad de producto.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| Identificar las necesidades por grupo | 16 necesidades de 6 grupos, tal como se dijeron | [inputs/needs.yaml](inputs/needs.yaml) |
| Racionalizar la lista: el mismo problema dicho con otras palabras | Matriz problema × grupo; comparación con un emparejamiento automático por texto | [quickwins.py](quickwins.py) |
| Priorizar: impacto, cómo se mide, urgencia, corto frente a largo plazo y recursos | Puntuación explícita, tipo de problema y tamaño medido en el warehouse | [quickwins.py](quickwins.py) |
| Crear opciones (al menos tres) y usar lo que ya hay | Tres opciones por problema; los quick wins reutilizan los capítulos 6 a 10 | [inputs/needs.yaml](inputs/needs.yaml) |
| Modelos de financiación: CDAO, stakeholder o híbrido | Financiación propuesta para cada problema | [inputs/needs.yaml](inputs/needs.yaml) |
| Comunicar para conseguir apoyo (impacto × comunicación) | Diagnóstico de cada entrega en la matriz del libro | [quickwins.py](quickwins.py) |
| Políticas, estándares y procedimientos que generan interés | Plantillas de estándar y de procedimiento rellenas con un ejemplo | [templates/psp_templates.md.j2](templates/psp_templates.md.j2) |
| Propiedad de los datos: activar a los stewards | Registro de cada activo con su ejecutivo y sus stewards; ideas de la comunidad con reconocimiento | [ownership.py](ownership.py) |
| Mentalidad de producto: producto, servicio o activo | Clasificación con los criterios del libro y candidatos a retirar por falta de uso | [quickwins.py](quickwins.py) |
| Entrega continua: impacto y coste en bajo, medio y alto, y roadmap | Reparto por trimestres según la capacidad del equipo | [quickwins.py](quickwins.py) |

## Entregables (`outputs/`)

| Archivo | Contenido |
|---|---|
| `quick_wins.md` | Racionalización, priorización, corto y largo plazo, roadmap, producto/servicio/activo, comunicación e ideas |
| `impact_vs_cost.png` | Matriz de impacto y coste con la posición de cada problema |
| `data_ownership_register.csv` | Registro de propiedad: activo, dominio, ejecutivo, stewards y huecos |
| `psp_templates.md` | Plantillas de estándar, procedimiento y política |

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch11_operaciones_datos.pipeline   # para medir los problemas con los caps. 6-10
uv run python -m chapters.ch13_quick_wins.run
uv run pytest chapters/ch13_quick_wins
```

## Decisiones de modelado

- **Puntuación = 2 × impacto + urgencia − coste** (alto = 3, medio = 2, bajo = 1). El impacto pesa el doble porque el libro pone el valor para el negocio por delante. Es quick win si el impacto es medio o alto y el coste bajo.
- **El tamaño del problema se mide, no se estima.** Cada problema tiene una consulta sobre el warehouse: duplicados de cliente, ventas sin cliente identificado, datasets sin certificar, emails inválidos, etc. Si falta el capítulo que lo mide, aparece como "sin medir".
- **Cada problema está ligado a un resultado del capítulo 5.** Si no, la ejecución falla: es el criterio de aceptación del plan.
- **El roadmap reparte las soluciones rápidas** por orden de puntuación entre trimestres, sin pasar de la capacidad del equipo. Lo que no cabe queda en el backlog.

## Conclusiones para NovaMercado

1. **16 necesidades son 11 problemas comunes.** El cliente repetido lo mencionan Ventas, Marketing y Tiendas con palabras distintas. Un emparejamiento automático por texto solo habría encontrado 1 de los 6 pares del mismo problema: hace falta conocer el contenido, como advierte el libro.
2. **Los problemas con más prioridad son quick wins de verdad:** localizar los datos personales (4 tablas fuera de raw con PII) y ver el historial de compras (el 51 % de las ventas no tiene cliente identificado). Los dos se resuelven reutilizando lo que ya construyeron los capítulos 6 y 10.
3. **La cifra de ventas y el cliente único son estratégicos:** alto impacto, pero coste medio o alto. El quick win del primero (corregir los precios negativos) es lo que desbloquea su certificación.
4. **El registro de propiedad muestra dos dominios con huecos,** Producto y Proveedor. Nombrar a sus responsables es en sí un quick win de coste bajo.
5. **Dos soluciones nadie las usa** y se pueden retirar. Una entrega de alto impacto (validar el origen de la cifra de ventas) no se ha comunicado: el libro advierte que así no genera apoyo.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada
- [x] Paso añadido al recorrido del README raíz

# Capítulo 9: Arquitectura de datos

> **Libro:** *Data Architecture*. Parte 2: Las capacidades de gobierno de datos en profundidad.
> **Microproyecto:** Principios de arquitectura y linter de estándares.

**Estado:** ✅ hecho

## Objetivo

Documentar cómo fluyen hoy los datos de NovaMercado (as-is) y hacia dónde deben ir (to-be), con principios de diseño y estándares arquitectónicos. Los estándares se **hacen cumplir de forma automática**, tanto sobre el warehouse que ya existe como sobre cada cambio de SQL antes de incorporarlo (SDLC).

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Dónde |
|---|---|---|
| La simplicidad gana: fuentes, almacenamiento, integración, procesamiento y acceso | Inventario de almacenes y flujos; se mide cuántos desaparecen en el to-be | [inputs/architecture.yaml](inputs/architecture.yaml) |
| Modelado as-is y to-be: el "espagueti" actual y la arquitectura objetivo por capas | Diagramas Mermaid generados desde el YAML | [templates/](templates/) |
| Principios de diseño definidos antes de diseñar | 5 principios del libro más 2 propios (simplicidad y mínima PII) | [inputs/architecture.yaml](inputs/architecture.yaml) |
| Estándares arquitectónicos: metadatos, calidad, acceso, distribución y consumo | 10 estándares que se comprueban automáticamente | [inputs/standards.yaml](inputs/standards.yaml), [lint.py](lint.py) |
| No guardar datos sensibles en varios sitios | Se cuenta en cuántas tablas está cada categoría de PII (con la clasificación del capítulo 6) | [lint.py](lint.py) |
| Niveles de revisión según el tamaño del cambio | Autodeclaración con la revisión automática, revisión del arquitecto o del consejo | [inputs/architecture.yaml](inputs/architecture.yaml) |
| Integrar la arquitectura en el SDLC | Revisión automática de SQL, con código de salida para usarla como puerta | [review.py](review.py) |
| Consejo de arquitectura (negocio, datos y TI) | Composición, presidencia y cadencia | [inputs/architecture.yaml](inputs/architecture.yaml) |
| Transición por fases: primero lo rápido, después lo material | Roadmap en 3 fases (0-6, 6-24 y 24-60 meses) | [inputs/architecture.yaml](inputs/architecture.yaml) |
| Medidas de éxito: adopción, calidad, coste, accesibilidad, seguridad, escalabilidad | Calculadas con el linter y con los resultados de los capítulos 6 y 8 | [run.py](run.py) |

## Entregables

| Archivo | Contenido |
|---|---|
| `outputs/data_architecture.md` | As-is y to-be (Mermaid) con su comparación, principios, cumplimiento de cada estándar, revisión SDLC del SQL, programa, roadmap y medidas de éxito |

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch09_arquitectura_datos.run
uv run python -m chapters.ch09_arquitectura_datos.review chapters/ch09_arquitectura_datos/inputs/proposals/20_curated_customer_report.sql
uv run pytest chapters/ch09_arquitectura_datos
```

`review` revisa cualquier fichero SQL contra los estándares y termina con código 1 si incumple alguno.

## Decisiones de modelado

- **El linter trabaja sobre dos objetivos.** Sobre el *SQL* comprueba nomenclatura, capas permitidas, `SELECT *`, snake_case y PII en curated; sobre el *warehouse*, tipos, claves, documentación y localización de la PII. El SQL del warehouse pasa la revisión y la propuesta de ejemplo (`inputs/proposals/`) se rechaza.
- **La nomenclatura se revisa sobre el SQL tal como se escribió.** Al cualificar con sqlglot, los identificadores se normalizan a minúsculas y `lastSale` pasaba como válido. Se corrigió y hay un test.
- **La PII se detecta por el nombre de la columna** con la política del capítulo 6, incluidas las correcciones de los stewards (el email de proveedor es corporativo y no cuenta). La revisión no necesita leer datos, así que sirve antes de crear la tabla.
- **Los `SELECT *` se expanden con el esquema real** para detectar la PII que arrastran.
- **Los lugares de PII se cuentan por tabla.** Nombre y apellido en la misma tabla son un solo lugar.

## Conclusiones para NovaMercado

1. **El as-is es un espagueti pequeño pero real:** 9 almacenes y 17 flujos punto a punto, 5 de ellos manuales y 8 con datos personales. Retirando la base de datos de Marketing, el cubo de Finanzas y las hojas regionales, quedan 6 almacenes y 8 flujos.
2. **El warehouse cumple 8 de 10 estándares.** Los 10 importes se guardan como `DOUBLE` (coma flotante) en lugar de `DECIMAL`: para dinero es un riesgo de redondeo, y está en la fase 1 del roadmap.
3. **Los datos personales están en 4 tablas de staging.** El email está en 2, el teléfono en 3 y el nombre en 4. El golden record del capítulo 10 es la palanca para reducirlos a un solo lugar autorizado (principio P7).
4. **La propuesta de Marketing incumple 5 estándares:** nombre sin prefijo, `SELECT *`, lectura directa de raw, un alias en camelCase y PII en curated. La revisión del SDLC la rechazaría antes de llegar al warehouse.
5. **Solo hay 1 punto de provisión autorizado de 4** (los datasets curados certificados del capítulo 8). Es la medida que más directamente refleja el principio P3.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada
- [x] Paso añadido al recorrido del README raíz

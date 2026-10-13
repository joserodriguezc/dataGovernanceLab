# Capítulo 6: Gestión de metadatos

> **Libro:** *Metadata Management*. Parte 2: Las capacidades de gobierno de datos en profundidad.
> **Microproyecto:** Glosario de negocio y catálogo de datos.

**Estado:** ✅ hecho

## Objetivo

Responder a las preguntas básicas de cualquier programa de datos: qué datos tenemos, qué significan, quién responde de ellos, cómo se clasifican y dónde encontrarlos. Se publican un glosario y un catálogo **dentro del propio warehouse** de NovaMercado.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| Metadatos de negocio, técnicos y operativos | Negocio: glosario y anotaciones. Técnicos: columnas, tipos, filas y % de nulos extraídos de DuckDB | [catalog.py](catalog.py) |
| Glosario de negocio: término, definición, sinónimos, antónimos, ejemplos y notas | 15 términos con fuente autorizada, estado y columnas que los implementan | [inputs/glossary.yaml](inputs/glossary.yaml) |
| Usar términos únicos y específicos (no "ID", sino "Identificador de cliente") | Validación de términos duplicados y de columnas totalmente cualificadas | [glossary.py](glossary.py) |
| El caso del "cliente": hasta 18 meses para acordar una definición | "Cliente activo" queda **en revisión** con el conflicto entre Marketing y Ventas | [inputs/glossary.yaml](inputs/glossary.yaml) |
| Catálogo: nombre, descripción, ubicación, formato, linaje, calidad y etiquetas | Tablas anotadas con stewards por dominio (capítulo 3); calidad y linaje llegan en los capítulos 7 y 8 | [catalog.py](catalog.py) |
| Clasificar los datos según la política de clasificación | Reglas por nombre y contenido; las correcciones de los stewards prevalecen | [classify.py](classify.py) |
| Estándar de metadatos: medir la publicación y la adopción por dominio | 10 normas con cumplimiento por norma y por dominio | [standards.py](standards.py) |
| Métricas de madurez del catálogo | Activos catalogados, completos, con stewards, certificados y con linaje | [standards.py](standards.py) |
| Valor: tiempo de búsqueda liberado e informes sin idas y vueltas | Estimación con los supuestos de `catalog.yaml` | [catalog.py](catalog.py) |
| *Data marketplace*: un único sitio para encontrar datos | Esquema `meta` en el warehouse más un buscador desde la terminal | [marketplace.py](marketplace.py) |

## Entregables

En `outputs/`:

| Archivo | Contenido |
|---|---|
| `business_glossary.md` | Glosario por dominio con stewards, fuente autorizada y columnas |
| `data_catalog.md` | Activos y columnas: dominio, stewards, filas, % de nulos, término y clasificación |
| `pii_classification.md` y `.csv` | Clasificación de las 146 columnas por nivel y capa, PII directa y correcciones de los stewards |
| `metadata_standards.md` | Cumplimiento del estándar por norma y por dominio, madurez del catálogo, vínculos rotos y valor |

En el **warehouse**:

- Comentarios `COMMENT ON` en tablas y columnas.
- Esquema `meta` con las tablas `glossary`, `term_columns`, `catalog_tables` y `catalog_columns`.

## Cómo ejecutarlo

```bash
uv run dglab build   # warehouse de la Fase 0 (y otra vez después de cada rebuild)
uv run python -m chapters.ch06_gestion_metadatos.run
uv run python -m chapters.ch06_gestion_metadatos.marketplace "cifra de ventas"
uv run pytest chapters/ch06_gestion_metadatos
```

`dglab build` recrea el warehouse desde cero y borra los metadatos, así que después hay que volver a ejecutar este capítulo.

## Decisiones de modelado

- **Los metadatos viven en el warehouse.** Los comentarios los ve cualquier herramienta y el esquema `meta` es la base del marketplace. Así los capítulos 4 y 5 *miden* el avance: el indicador de tablas documentadas pasa del 0 % al 100 %.
- **Los stewards no se repiten.** Salen de los roles por dominio del capítulo 3, así que donde allí faltan stewards (producto y proveedor) aquí aparecen los incumplimientos.
- **Clasificación: el nombre manda sobre el contenido.** La primera versión aplicaba las reglas en orden y comprobaba nombre y contenido a la vez. Las fechas ISO (`2025-03-14`) coincidían con el patrón de teléfono y `birth_date` o `sale_date` salían como PII de teléfono. Ahora se busca primero una regla que coincida por nombre y solo después por contenido, y el teléfono exige de 9 a 12 dígitos. Un test cubre el caso.
- **Las correcciones de los stewards se aplican por columna.** En raw, el email de contacto de proveedor sigue como restringido porque solo se corrigió en staging: es un recordatorio de que hay que propagar las decisiones.
- **Alcance del estándar:** las capas staging y curated. Raw se cataloga y clasifica, pero no se le exige documentación de negocio.

## Conclusiones para NovaMercado

1. **Hay 23 columnas con PII directa** (nombres, emails, teléfonos y fechas de nacimiento), todas en raw y staging. Ninguna llega a curated: el modelo de ventas no expone datos personales.
2. **El estándar se cumple a medias donde faltan personas, no herramientas.** Producto no tiene steward de negocio y Proveedor no tiene ninguno, así que fallan MD-03, MD-04 y MD-09. Es la misma brecha que señalaron los capítulos 1, 3 y 4.
3. **Solo el 37 % de las columnas está ligado a un término del glosario (MD-06).** El glosario cubre los términos críticos y el resto llegará por demanda.
4. **"Cliente activo" sigue en revisión.** Hasta que el consejo de datos lo resuelva, Marketing y Ventas seguirán contando clientes distintos.
5. **El valor estimado es de US$ 516.000/año** (catálogo US$ 408.000 y glosario US$ 108.000), pendiente de validar con el negocio como pide el capítulo 1.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada

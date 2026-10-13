# Capítulo 10: Gestión de datos primarios (maestros)

> **Libro:** *Primary Data Management*. Parte 2: Las capacidades de gobierno de datos en profundidad.
> **Microproyecto:** Golden record de cliente.

**Estado:** ✅ hecho

El libro propone hablar de datos **primarios** en lugar de datos "maestros", y el laboratorio sigue esa propuesta. El esquema del hub se llama `pdm` (*Primary Data Management*).

## Objetivo

Unificar a los clientes que aparecen repetidos entre el CRM, el e-commerce y las tarjetas de tienda en un **golden record** fiable. Para cada atributo queda documentado de qué sistema sale (atribución de la fuente dorada), se enriquece con datos de referencia y se publica con un modelo de consumo que mantiene los datos personales en un solo lugar.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| Definiciones comunes: qué es un cliente | Definición aprobada por la ejecutiva del dominio, la misma del glosario del capítulo 6 | [inputs/pdm.yaml](inputs/pdm.yaml) |
| Deduplicación (*match and merge*): algoritmos, lógica difusa y revisión humana | Reglas deterministas (email, teléfono), coincidencia difusa con rapidfuzz (código postal + nombre) y cola de revisión; cierre transitivo con union-find | [matching.py](matching.py) |
| Medir la deduplicación | Precisión y recall por pares frente al solucionario de la Fase 0 | [matching.py](matching.py) |
| Lógica de confianza (*trust logic*) por atributo: fuente, antigüedad, completitud | Orden de fuentes por atributo, gana el registro más reciente y solo valores válidos | [survivorship.py](survivorship.py) |
| Atribución de la fuente dorada y un steward por atributo | Para cada valor se guarda su sistema y registro de origen | [survivorship.py](survivorship.py) |
| Datos de referencia (lentos, finitos, gestión central) | Provincias por prefijo de código postal (oficial) y regiones comerciales (propias) | [inputs/reference_data.yaml](inputs/reference_data.yaml) |
| Enriquecimiento y varias jerarquías sobre la misma base | Localización (CP → provincia → comunidad) y comercial (comunidad → región de ventas) | [reference.py](reference.py) |
| Integración bidireccional | `pdm.customer_xref`: cada registro de origen con su golden id, para devolverlo al sistema | [publish.py](publish.py) |
| Modelo de consumo estricto | Operación desde `pdm`; analítica desde `curated.dim_customer`, sin PII directa | [publish.py](publish.py) |
| Búsqueda de clientes (capacidad típica de un PDM) | CLI de búsqueda con golden record, orígenes y atribución | [lookup.py](lookup.py) |
| CRM frente a PDM; caso de negocio con valor | Comparativa y valor estimado en el informe | [templates/primary_data.md.j2](templates/primary_data.md.j2) |

## Entregables

En `outputs/`:

| Archivo | Contenido |
|---|---|
| `primary_data.md` | Deduplicación y su acierto, cola de revisión, lógica de confianza y atribución, calidad antes y después, referencia y jerarquías, vista única, modelo de consumo, CRM frente a PDM y valor |
| `deduplication.png` | Registros de cada sistema frente a clientes únicos |
| `review_queue.csv` | Pares dudosos para el steward de cliente |

En el **warehouse**:

- `pdm.customer_golden`, `pdm.customer_xref`, `pdm.customer_attribution`, `pdm.customer_review_queue` y `pdm.ref_province`.
- `curated.dim_customer`, documentada y con su linaje registrado en `meta.lineage_external`.

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch10_datos_primarios_mdm.run
uv run python -m chapters.ch10_datos_primarios_mdm.lookup "telmo anton"
uv run pytest chapters/ch10_datos_primarios_mdm
```

## Decisiones de modelado

- **Reglas en cascada, de la más segura a la más dudosa.** Primero email o teléfono idénticos; después mismo código postal con nombre parecido (`token_set_ratio` ≥ 90, que tolera que la tarjeta de tienda solo tenga un apellido); y a revisión humana cuando el nombre coincide pero el código postal no (¿se ha mudado?). Para no comparar todos con todos, solo se comparan registros con el mismo código postal o el mismo nombre y primer apellido (*blocking*).
- **No se pide revisar lo que ya está resuelto.** Si A=B y B=C ya están unidos, el par A–C no va a la cola. Un test detectó el caso.
- **Dentro de un mismo sistema gana el registro más reciente** (la "antigüedad del dato" del libro), y un valor inválido se salta: el código postal mal escrito en el e-commerce se toma de otra fuente.
- **El consentimiento es conservador:** sin registro en el CRM, no hay consentimiento.
- **La PII del cliente unificado vive en `pdm`, no en curated.** `curated.dim_customer` solo tiene localización, tramo de edad, segmento, canales y ventas. Un test lo comprueba con el linter del capítulo 9.
- **La ciudad declarada no se usa.** En los datos sintéticos no es coherente con el código postal; la localización sale del código postal y de los datos de referencia.
- **Integración con los capítulos anteriores:**
  - El indicador de duplicados de cliente (capítulos 4 y 5) mide el golden record cuando existe.
  - El catálogo del capítulo 6 documenta `dim_customer`.
  - El capítulo 7 incorpora el linaje que registra este proceso, que no es SQL.
  - El capítulo 9 trata `net_sales` como un importe.

## Conclusiones para NovaMercado

1. **Hay 3.752 registros pero solo 1.926 clientes:** el 49 % de los registros eran duplicados entre sistemas o dentro del CRM.
2. **La deduplicación acierta:** 100 % de precisión y 99,96 % de recall frente al solucionario. El único cliente que se escapa tiene el código postal mal escrito y se resuelve en la cola de revisión. La cola tiene 2 pares: uno es el mismo cliente y el otro son **dos personas distintas con el mismo nombre**. Por eso el libro insiste en la revisión humana.
3. **El golden record es mejor que cualquier sistema por separado:** el email válido pasa del 74 % de los registros al 95 % de los clientes, y 40 clientes recuperan un código postal válido de otra fuente.
4. **La vista única cambia el análisis.** El 71 % de los clientes está en más de un sistema, 415 compran en tienda y online, y el 49 % de las ventas netas ya se puede atribuir a un cliente identificado. Es la base del resultado O1 de la CMO (capítulo 5).
5. **El resultado de datos "Duplicados de cliente por debajo del 0,5 %" del capítulo 5 pasa a estar logrado** (0 %), y el nivel de madurez de datos maestros del capítulo 4 deja de estar acotado por la evidencia.
6. **El valor estimado es de US$ 110.756/año,** casi todo por la depuración manual que se elimina (línea L3 del capítulo 1). Los envíos duplicados evitados suman poco por el bajo coste de un email: el valor está en el tiempo y en la vista única, no en el envío.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada
- [x] Paso añadido al recorrido del README raíz

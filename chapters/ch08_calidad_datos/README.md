# Capítulo 8: Calidad de datos

> **Libro:** *Data Quality*. Parte 2: Las capacidades de gobierno de datos en profundidad.
> **Microproyecto:** Calidad de datos y certificación.

**Estado:** ✅ hecho

## Objetivo

Responder con evidencia a *¿puedo confiar en este dato?* Para ello se perfilan los datos, se ejecutan reglas por dimensión de calidad, se registran y priorizan las incidencias, se certifican los datasets que cumplen y se publica todo con transparencia. Como los datos son sintéticos, además se puede **medir si las reglas encuentran los defectos sembrados**.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| Dimensiones de calidad (exactitud, completitud, consistencia, actualidad, validez, integridad…) | Cada regla pertenece a una dimensión; scorecard por dimensión y por dominio | [rules.py](rules.py) |
| Perfilado: conocer los datos antes de escribir reglas | Nulos, cardinalidad, rangos y patrones de forma; detecta formatos mezclados | [profiling.py](profiling.py) |
| Validación y estandarización: valores permitidos, formatos y reglas de negocio | 17 reglas ejecutadas con pandera que devuelven los registros concretos que fallan | [rules.py](rules.py) |
| Severidad tipo Sev1/Sev2/Sev3 | Severidad por regla; la Sev1 bloquea la certificación | [inputs/dq_rules.yaml](inputs/dq_rules.yaml) |
| Gestión de incidencias y registro de disposiciones | Una incidencia por regla incumplida, con steward del dominio (capítulo 3) y disposiciones firmadas | [quality.py](quality.py) |
| Remediación: corregir lo más cerca posible del origen | Cada regla indica cómo se remedia: estandarizar, excluir, corregir en origen, enriquecer o aceptar | [inputs/dq_rules.yaml](inputs/dq_rules.yaml) |
| Datos certificados, apoyados en metadatos y linaje | Se certifica un dataset si él **y sus fuentes según el linaje** cumplen las reglas Sev1, y si está documentado y tiene steward | [quality.py](quality.py) |
| Transparencia: publicar los resultados aunque sean malos | Scorecard, incidencias y resultados en el warehouse; marca de certificado en el marketplace | [publish.py](publish.py) |
| Medir el valor en términos de negocio (el caso de los contactos de marketing) | Clientes aptos para marketing y coste de la corrección manual | [quality.py](quality.py) |

## Entregables

En `outputs/`:

| Archivo | Contenido |
|---|---|
| `dq_scorecard.md` | Scorecard por dimensión y dominio, resultado de cada regla, incidencias, disposiciones, certificación, detección frente al solucionario y valor |
| `dq_rules.png` | Cada regla frente a su umbral |
| `data_profile.md` | Perfil de cada tabla y columnas con formatos mezclados |
| `dq_issues.csv` | Los registros concretos que fallan cada regla (para remediarlos) |

En el **warehouse**:

- `meta.dq_results` y `meta.dq_issues`.
- La marca `certified` de `meta.catalog_tables`, que se ve en el marketplace del capítulo 6 (`--solo-certificados`).

## Cómo ejecutarlo

```bash
uv run dglab build
uv run python -m chapters.ch06_gestion_metadatos.run       # documentación y stewards
uv run python -m chapters.ch07_metadatos_tecnicos_linaje.run # linaje
uv run python -m chapters.ch08_calidad_datos.run
uv run pytest chapters/ch08_calidad_datos
```

Sin los capítulos 6 y 7, las reglas se ejecutan igual, pero no se certifica ningún dataset: falta la documentación y el linaje.

## Decisiones de modelado

- **pandera, una regla por esquema.** Cada regla es un esquema de una columna validado en modo `lazy` sobre la tabla indexada por su clave. Así se obtienen los registros que fallan, no solo un porcentaje, y se pueden cruzar con el solucionario y remediar uno a uno.
- **Las reglas se aplican en la capa donde el defecto es visible.** El formato de fecha mezclado se mide en raw (DQ-04), porque staging ya lo estandariza: así se ve que la estandarización funciona y que el origen sigue mal.
- **La actualidad mide el conjunto, no los registros.** DQ-16 compara el último dato de la cifra de ventas con la fecha de medición. No aparece en el gráfico para no distorsionar la escala.
- **Certificación por linaje.** `curated.fct_sales` cumple todas sus reglas, pero no se certifica porque su fuente `staging.stg_pos_sales` tiene precios negativos (DQ-08, Sev1). Sin el linaje del capítulo 7 este problema no se vería.
- **"Fuera del solucionario" no significa falso positivo.** La regla de código postal de envío (DQ-06) marca 352 pedidos más de los sembrados. Todos son de clientes cuyo código postal ya era inválido: el defecto se hereda del maestro de cliente. Se corrige en el cliente, no en cada pedido.
- **Patrones de perfilado por forma, no por longitud.** Las secuencias de dígitos y de letras se colapsan (`2025-03-12` → `9-9-9`). La primera versión las contaba carácter a carácter y marcaba como "mezclados" nombres e importes de distinta longitud.

## Conclusiones para NovaMercado

1. **Las reglas encuentran el 100 % de los 9 tipos de defecto sembrados** (de 4 a 240 registros cada uno), lo que demuestra que cubren lo que se buscaba.
2. **Solo 7 de 17 reglas cumplen su umbral.** Las peores dimensiones son actualidad (la cifra de ventas tiene 12 días de retraso), consistencia (20 % de fechas en otro formato) y completitud (93 %).
3. **Solo se certifica `curated.dim_store`.** La cifra de ventas no se certifica por los precios negativos en origen y por su falta de actualidad. Es la conversación que hay que tener con el CFO antes de presentarla como fuente oficial (capítulo 5, resultado O3).
4. **Los duplicados del CRM son Sev1:** 102 registros comparten teléfono. Es la entrada del capítulo 10 (golden record).
5. **El 67 % de los clientes del CRM es apto para marketing.** El resto se debe casi todo a la falta de consentimiento, no a la calidad del email: corregir emails solo suma 61 contactos (US$ 3.660/año). En cambio, corregir a mano todos los registros que fallan costaría 326 horas (US$ 14.659), así que conviene corregir en origen.
6. **La falta de teléfono en tarjetas de tienda se acepta** (disposición firmada por el responsable de tiendas): no toda regla incumplida merece remediarse.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada
- [x] Paso añadido al recorrido del README raíz

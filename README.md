# Data Governance Lab

*Data Governance Handbook* (Wendy S. Batchelder, Packt 2024) convertido en 17 microproyectos prácticos, uno por capítulo, sobre la empresa ficticia **NovaMercado**, un retail omnicanal con una filial financiera, NovaPay.

La idea es leer un capítulo del libro y después ejecutar y explorar su microproyecto: cada concepto del libro se convierte en algo que se puede ejecutar, medir y cambiar. El plan completo está en [PLAN.md](PLAN.md).

## Cómo funciona el repositorio

- **Un capítulo, una carpeta** en [chapters/](chapters/). Cada una tiene:
  - `README.md`: qué ideas del libro aplica, las decisiones tomadas y las conclusiones para NovaMercado. **Es lo primero que hay que leer.**
  - `inputs/`: los supuestos de NovaMercado en YAML. Se pueden editar para experimentar.
  - `run.py`: genera los entregables. Se ejecuta con `uv run python -m chapters.<carpeta>.run`.
  - `outputs/`: los entregables generados (informes Markdown, gráficos y CSV). No se versionan: se regeneran con `run.py`.
  - `tests/`: las reglas del capítulo, comprobadas con pytest.
- **Los capítulos se encadenan.** Cada uno reutiliza lo que dejaron los anteriores: el valor del capítulo 1, los stakeholders del 2, los roles del 3, los indicadores del 4, etc. Por eso conviene seguirlos en orden.
- **Hay dos tipos de capítulo.** Los de gestión (1-3) solo leen YAML. Desde el capítulo 4, los capítulos trabajan sobre un **warehouse DuckDB** con datos sintéticos de NovaMercado, que se genera en el paso 0.

## Requisitos

[uv](https://docs.astral.sh/uv/). uv instala Python 3.12 automáticamente.

## Recorrido paso a paso

| Paso | Capítulo del libro | Comando | Necesita |
|---:|---|---|---|
| 0 | Preparación | `uv sync` y `uv run dglab build` | — |
| 1 | What Is Data Governance? | `uv run python -m chapters.ch01_que_es_gobierno_datos.run` | — |
| 2 | How to Build a Coalition of Advocates | `uv run python -m chapters.ch02_coalicion_defensores.run` | — |
| 3 | Building a High-Performing Team | `uv run python -m chapters.ch03_equipo_alto_rendimiento.run` | Inputs del cap. 1 |
| 4 | Baseline Your Organization | `uv run python -m chapters.ch04_linea_base_madurez.run` | Warehouse e inputs del cap. 3 |
| 5 | Defining Success and Aligning on Outcomes | `uv run python -m chapters.ch05_exito_y_resultados.run` | Warehouse e inputs de los caps. 1 y 2 |
| 6 | Metadata Management | `uv run python -m chapters.ch06_gestion_metadatos.run` | Warehouse e inputs del cap. 3 |
| 7 | Technical Metadata and Data Lineage | `uv run python -m chapters.ch07_metadatos_tecnicos_linaje.run` | Warehouse; recomendable haber ejecutado el paso 6 |
| 8 | Data Quality | `uv run python -m chapters.ch08_calidad_datos.run` | Warehouse; para certificar, pasos 6 y 7 |
| 9 | Data Architecture | `uv run python -m chapters.ch09_arquitectura_datos.run` | Warehouse; para las medidas de éxito completas, pasos 6 y 8 |
| 10-17 | Próximamente | Ver el estado en [PLAN.md](PLAN.md) | |

"Necesita" indica de qué depende cada paso: el warehouse (paso 0) o los YAML de `inputs/` de capítulos anteriores, que ya están en el repositorio, así que no hace falta ejecutar antes esos capítulos. Aun así, el orden recomendado es el de la tabla, porque así se sigue el razonamiento del libro.

### Paso 0. Preparar el entorno y los datos

```bash
uv sync            # instala Python 3.12 y las dependencias
uv run dglab build # genera los datos sintéticos y construye el warehouse DuckDB
uv run pytest      # opcional: comprueba que todo funciona
```

- `dglab build` crea `data/raw/` (CSV por sistema de origen) y `data/warehouse/novamercado.duckdb`, con las capas raw, staging y curated. Tarda unos segundos y siempre genera los mismos datos (semilla fija).
- **Para entender los datos:** [docs/datos_sinteticos.md](docs/datos_sinteticos.md) explica los sistemas, las tablas y los defectos de calidad sembrados a propósito, que los capítulos irán descubriendo.
- **Ojo:** `dglab build` recrea el warehouse desde cero y **borra lo que hayan escrito los capítulos** (por ejemplo, los metadatos del capítulo 6). Después de un rebuild hay que volver a ejecutar esos capítulos.

### Paso 1. ¿Qué es el gobierno de datos?

```bash
uv run python -m chapters.ch01_que_es_gobierno_datos.run
```

- **Qué produce:** data equity (activos − pasivos de datos), caso de negocio con 3 opciones de timeline, charter, política de gobierno de 10 secciones y EDG Scorecard.
- **Qué mirar:** `outputs/business_case.md` y su gráfico, y `outputs/edg_scorecard.md`.
- **Qué probar:** en `inputs/business_case.yaml`, pon `include_unvetted_benefits: true` y vuelve a ejecutar. Verás cuánto sube el VAN si se cuentan los beneficios que el negocio aún no ha validado.
- [README del capítulo](chapters/ch01_que_es_gobierno_datos/README.md)

### Paso 2. Construir una coalición de defensores

```bash
uv run python -m chapters.ch02_coalicion_defensores.run
```

- **Qué produce:** registro y mapa de stakeholders, matriz de influencia e interés, evaluación de sponsors con un caso de negocio piloto y plan de coalición con las señales del comité.
- **Qué mirar:** `outputs/sponsor_assessment.md` y `outputs/stakeholder_matrix.png`.
- **Qué probar:** en `inputs/sponsors.yaml`, cambia `reports_to_ceo` del Director de Compras a `true`. Pasa a ser elegible, aunque no supera a la CMO ni al CFO.
- [README del capítulo](chapters/ch02_coalicion_defensores/README.md)

### Paso 3. Construir un equipo de alto rendimiento

```bash
uv run python -m chapters.ch03_equipo_alto_rendimiento.run
```

- **Qué produce:** modelo organizativo recomendado, organigrama y plan de contratación, RACI, cartas y calendario de los foros, inventario del portfolio y brechas de habilidades.
- **Qué mirar:** `outputs/org_model.md` y `outputs/team_design.md`, que contrasta el coste del equipo con el presupuesto del capítulo 1.
- **Qué probar:** en `inputs/org_context.yaml`, cambia `capabilities_consistent` a `true`. La recomendación pasa de centralizado a otro modelo.
- [README del capítulo](chapters/ch03_equipo_alto_rendimiento/README.md)

### Paso 4. Establecer la línea base de la organización

```bash
uv run python -m chapters.ch04_linea_base_madurez.run
```

- **Qué produce:** los 10 pasos de una evaluación de madurez. Incluye respuestas simuladas, detección del sesgo de autoevaluación, evidencia objetiva medida en el warehouse, un informe agregado para el comité y otro interno por área, y un plan de mejora.
- **Qué mirar:** `outputs/maturity_report.md` (agregado), `outputs/maturity_internal.md` (solo para la oficina de datos) y `outputs/improvement_plan.md`, cuyas líneas base salen del warehouse.
- **Qué probar:** en `inputs/assessment.yaml`, sube el `self_bias` de Ventas y vuelve a ejecutar. Verás cómo crece la diferencia entre la autoevaluación y el consenso del taller.
- [README del capítulo](chapters/ch04_linea_base_madurez/README.md)

### Paso 5. Definir el éxito y alinearse en resultados

```bash
uv run python -m chapters.ch05_exito_y_resultados.run
```

- **Qué produce:** marco de resultados (resultado de negocio → capacidades → entregables → resultados de datos), informe de progreso, roadmap y revisión trimestral (QBR) con cada stakeholder.
- **Qué mirar:** `outputs/progress_report.md`. Sus "resultados de datos" se **miden en el warehouse** en cada ejecución.
- **Qué probar:** ejecútalo antes y después del paso 6. Tras el paso 6, "Tablas curated documentadas al 100 %" pasa a estar logrado sin tocar nada de este capítulo.
- [README del capítulo](chapters/ch05_exito_y_resultados/README.md)

### Paso 6. Gestión de metadatos

```bash
uv run python -m chapters.ch06_gestion_metadatos.run
uv run python -m chapters.ch06_gestion_metadatos.marketplace "cifra de ventas"
```

- **Qué produce:** glosario de negocio, catálogo de datos, clasificación de PII y cumplimiento del estándar de metadatos. Además **escribe en el warehouse** comentarios en tablas y columnas y el esquema `meta`.
- **Qué mirar:** `outputs/metadata_standards.md` y `outputs/pii_classification.md`. Prueba también el buscador: encuentra "Venta neta" por su sinónimo "cifra de ventas".
- **Qué probar:** vuelve a ejecutar los pasos 4 y 5. El indicador de tablas documentadas pasa del 0 % al 100 %.
- **Recuerda:** después de cada `uv run dglab build` hay que volver a ejecutar este paso.
- [README del capítulo](chapters/ch06_gestion_metadatos/README.md)

### Paso 7. Metadatos técnicos y linaje de datos

```bash
uv run python -m chapters.ch07_metadatos_tecnicos_linaje.run
uv run python -m chapters.ch07_metadatos_tecnicos_linaje.impact raw.ecom_orders.status
uv run python -m chapters.ch07_metadatos_tecnicos_linaje.impact curated.agg_sales_daily_channel.revenue --origen
```

- **Qué produce:** el linaje a nivel de columna, extraído del SQL del warehouse, desde el sistema de origen hasta el KPI. Incluye el análisis de impacto, la validación de la narrativa de quien produce la venta neta y los hallazgos (qué fuentes llegan a curated y si llega PII). **Escribe en el warehouse** las tablas `meta.lineage_edges` y `meta.lineage_steps`.
- **Qué mirar:** `outputs/lineage_validation.md`, donde el responsable cree que la venta sale del ERP y no es así, y el diagrama de `outputs/data_lineage.md`.
- **Qué probar:** usa el comando `impact` con otras columnas. Después edita un SQL de [src/dglab/warehouse/sql/](src/dglab/warehouse/sql/) (por ejemplo, quita el filtro de cancelados en `11_curated_sales.sql`), ejecuta `uv run dglab build` y repite los pasos 6 y 7: el linaje y la validación cambian solos.
- **Recuerda:** como el paso 6, después de cada `uv run dglab build` hay que volver a ejecutarlo. Ejecútalo después del paso 6 para que el cruce con la PII funcione.
- [README del capítulo](chapters/ch07_metadatos_tecnicos_linaje/README.md)

### Paso 8. Calidad de datos

```bash
uv run python -m chapters.ch08_calidad_datos.run
uv run python -m chapters.ch06_gestion_metadatos.marketplace "tienda" --solo-certificados
```

- **Qué produce:** perfilado de las tablas, 17 reglas de calidad por dimensión (ejecutadas con pandera), registro de incidencias con severidad y steward, certificación de los datasets curados y comparación de lo detectado con los defectos sembrados. **Escribe en el warehouse** `meta.dq_results` y `meta.dq_issues`, y marca los datasets certificados en el catálogo.
- **Qué mirar:** `outputs/dq_scorecard.md`, sobre todo la certificación (¿por qué no se certifica la cifra de ventas?) y la tabla de detección. Después, `outputs/dq_issues.csv` con los registros concretos que fallan.
- **Qué probar:** en `inputs/dq_rules.yaml`, baja el `threshold` de DQ-08 a `0.99` y vuelve a ejecutar: `curated.fct_sales` pasa a certificarse. O regenera los datos con otra semilla (`uv run dglab generate --seed 7`, `uv run dglab load` y los pasos 6 y 7) y comprueba que las reglas siguen encontrando todos los defectos.
- **Recuerda:** ejecútalo después de los pasos 6 y 7, porque la certificación exige documentación, steward y linaje.
- [README del capítulo](chapters/ch08_calidad_datos/README.md)

### Paso 9. Arquitectura de datos

```bash
uv run python -m chapters.ch09_arquitectura_datos.run
uv run python -m chapters.ch09_arquitectura_datos.review chapters/ch09_arquitectura_datos/inputs/proposals/20_curated_customer_report.sql
```

- **Qué produce:** as-is y to-be de la arquitectura (diagramas Mermaid), principios de diseño, el cumplimiento de 10 estándares arquitectónicos sobre el warehouse, la revisión automática de cada SQL (puerta del SDLC), el programa de arquitectura, el roadmap por fases y las medidas de éxito.
- **Qué mirar:** `outputs/data_architecture.md`, sobre todo la comparación as-is/to-be y los incumplimientos (importes en coma flotante, PII repetida en varias tablas). Después ejecuta `review` con la propuesta de ejemplo, que se rechaza con 5 incumplimientos.
- **Qué probar:** corrige la propuesta en `inputs/proposals/` (renómbrala a `curated.dim_customer_sales`, lee de staging, quita el `SELECT *` y los datos personales) hasta que `review` la apruebe. También puedes cambiar un `CAST(... AS DOUBLE)` por `DECIMAL(18,2)` en el SQL del warehouse, reconstruirlo y ver cómo baja ARQ-06.
- [README del capítulo](chapters/ch09_arquitectura_datos/README.md)

### Ejecutar todo de una vez

```bash
uv run dglab build
uv run python -m chapters.ch01_que_es_gobierno_datos.run
uv run python -m chapters.ch02_coalicion_defensores.run
uv run python -m chapters.ch03_equipo_alto_rendimiento.run
uv run python -m chapters.ch04_linea_base_madurez.run
uv run python -m chapters.ch05_exito_y_resultados.run
uv run python -m chapters.ch06_gestion_metadatos.run
uv run python -m chapters.ch07_metadatos_tecnicos_linaje.run
uv run python -m chapters.ch08_calidad_datos.run
uv run python -m chapters.ch09_arquitectura_datos.run
```

Este orden refleja la línea base: los capítulos 4 y 5 se ejecutan antes de documentar el warehouse y de calcular el linaje. Para ver el avance, vuelve a ejecutar 4 y 5 al final.

## Comandos útiles

```bash
uv run pytest                            # todos los tests
uv run pytest chapters/ch04_linea_base_madurez  # los de un capítulo
uv run ruff check .                      # lint
uv run dglab --help                      # comandos del generador de datos (build, generate, load, reset)
```

## Estructura

```text
src/dglab/        paquete compartido: rutas, empresa ficticia, datos sintéticos, warehouse, reporting y gráficos
data/raw/         CSV sintéticos y solucionario (generados, no versionados)
data/warehouse/   base DuckDB de NovaMercado (generada, no versionada)
chapters/chNN_*/  un microproyecto por capítulo: README, inputs/, run.py, outputs/, tests/
docs/             referencia bibliográfica y documentación de los datos sintéticos
tests/            tests del paquete compartido
```

## Referencia y derechos

Proyecto de aprendizaje basado en *Data Governance Handbook* (Wendy S. Batchelder, Packt Publishing, 2024, ISBN 978-1-80324-072-5). El libro tiene copyright y no se distribuye aquí: el repositorio solo lo referencia (ver [docs/README.md](docs/README.md)). Todo el código y los datos sintéticos son originales.

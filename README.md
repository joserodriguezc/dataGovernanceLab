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
| 10 | Primary Data Management | `uv run python -m chapters.ch10_datos_primarios_mdm.run` | Warehouse |
| 11 | Data Operations | `uv run python -m chapters.ch11_operaciones_datos.run` | `data/raw` (reconstruye el warehouse y ejecuta los pasos 10, 6, 7 y 8) |
| 12 | Launch Powerfully | `uv run python -m chapters.ch12_lanzamiento.run` | Warehouse con los pasos 6 a 10 (o el pipeline del paso 11) |
| 13 | Delivering Quick Wins with Impact | `uv run python -m chapters.ch13_quick_wins.run` | Warehouse; para medir los problemas, pasos 6 a 10 |
| 14 | Data Automation | `uv run python -m chapters.ch14_automatizacion.run` | Warehouse con el paso 10 (o el pipeline del paso 11) |
| 15 | Adoption That Drives Business Success | `uv run python -m chapters.ch15_adopcion.run` | — (logs de uso simulados) |
| 16 | Delivering Trusted Results | `uv run python -m chapters.ch16_resultados_confiables.run` | Pipeline del paso 11 (warehouse completo y registro de operaciones) |
| 17 | Case Study – Financial Institution | `uv run python -m chapters.ch17_caso_estudio_novapay.run` | Ninguno: genera sus propios datos y su warehouse |

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

### Paso 10. Gestión de datos primarios (golden record de cliente)

```bash
uv run python -m chapters.ch10_datos_primarios_mdm.run
uv run python -m chapters.ch10_datos_primarios_mdm.lookup "telmo anton"
```

- **Qué produce:** el golden record de cliente. Deduplica los registros del CRM, el e-commerce y las tarjetas de tienda (reglas, coincidencia difusa y cola de revisión humana), aplica lógica de confianza por atributo con atribución de la fuente dorada, enriquece con datos de referencia (provincia, comunidad y región comercial) y calcula la vista única de ventas. **Escribe en el warehouse** el hub `pdm.*` y `curated.dim_customer`, sin datos personales directos.
- **Qué mirar:** `outputs/primary_data.md`, sobre todo la precisión y el recall frente al solucionario, la cola de revisión (uno de los dos pares son dos personas distintas con el mismo nombre) y la calidad antes y después. Prueba también el buscador `lookup` con un nombre, un email o un teléfono.
- **Qué probar:** en `inputs/pdm.yaml`, baja `auto_match_score` a 70 y comprueba cómo cae la precisión al unir personas distintas. O cambia el orden de fuentes de `email` para que el e-commerce vaya primero y mira cómo cambia la atribución.
- **Después:** vuelve a ejecutar los pasos 4 y 5. El resultado "Duplicados de cliente por debajo del 0,5 %" pasa a estar logrado. Ejecuta también los pasos 6 y 7 para que `dim_customer` quede con steward y linaje.
- [README del capítulo](chapters/ch10_datos_primarios_mdm/README.md)

### Paso 11. Operaciones de datos

```bash
uv run python -m chapters.ch11_operaciones_datos.run
uv run python -m chapters.ch11_operaciones_datos.run --sin-pipeline   # solo el informe
```

- **Qué produce:** ejecuta el **pipeline nocturno real**: reconstruye el warehouse y vuelve a pasar los capítulos 10, 6, 7 y 8 en orden de dependencias, con reintentos y un registro de auditoría en `data/warehouse/operations.duckdb`. Después genera el informe de operaciones: panel de valor (dólares, horas, riesgos y automatizaciones), SLAs, frescura y volumen, tickets por causa raíz y revisión posterior.
- **Qué mirar:** `outputs/data_operations.md` y la línea temporal `outputs/ops_timeline.png`. Ejecuta el paso dos veces y verás que la tabla de volumen compara con la ejecución anterior.
- **Qué probar:** en `inputs/operations.yaml`, sube el `failure_rate` del paso `pdm` y la `retry_success` a 0 y regenera el informe con `--sin-pipeline`: caen los SLAs y aparecen más tickets de fallos de proceso.
- [README del capítulo](chapters/ch11_operaciones_datos/README.md)

### Paso 12. Lanzar con fuerza

```bash
uv run python -m chapters.ch12_lanzamiento.run
```

- **Qué produce:** la evaluación de preparación para el lanzamiento en las cinco dimensiones del libro, calculada con la evidencia de los capítulos anteriores; el mensaje central (visión, as-is frente a to-be, audiencias); el **memo narrativo** para toda la empresa, revisado para que no tenga jerga; el plan de comunicación y feedback; y las victorias ya entregadas.
- **Qué mirar:** `outputs/narrative_memo.md` (léelo como si fueras del comité de dirección) y `outputs/launch_readiness.png`.
- **Qué probar:** escribe un término técnico ("golden record", "linaje", "PII") en un hito de `inputs/launch.yaml` y vuelve a ejecutar: la revisión del memo lo detecta. O pon `funding_approved: false` y mira cómo baja el liderazgo y cambia el enfoque recomendado.
- [README del capítulo](chapters/ch12_lanzamiento/README.md)

### Paso 13. Quick wins con impacto

```bash
uv run python -m chapters.ch13_quick_wins.run
```

- **Qué produce:** las necesidades de los stakeholders racionalizadas en problemas comunes y priorizadas (impacto, urgencia y coste) con su **tamaño medido en el warehouse**; para cada uno, tres opciones y la solución rápida frente a la de largo plazo; un roadmap por trimestres según la capacidad del equipo; la clasificación producto/servicio/activo; el registro de propiedad de los datos; y plantillas de estándar y procedimiento.
- **Qué mirar:** `outputs/quick_wins.md` (empieza por la matriz de problemas comunes y la comparación con el emparejamiento automático) y `outputs/impact_vs_cost.png`.
- **Qué probar:** sube `capacity_per_quarter` en `inputs/delivery.yaml` y mira cómo se adelanta el roadmap. O ejecútalo sin los capítulos 6 a 10 en el warehouse (`uv run dglab build` y directamente este paso): los tamaños aparecen como "sin medir".
- [README del capítulo](chapters/ch13_quick_wins/README.md)

### Paso 14. Automatización de datos

```bash
uv run python -m chapters.ch14_automatizacion.run
```

- **Qué produce:** los 6 pasos del libro aplicados al informe semanal de ventas por región que hoy se monta a mano: objetivos, proceso actual, problema, tres enfoques con su ROI, el **informe automatizado de verdad** (cuadra al céntimo con la cifra oficial), monitorización con alertas y la evaluación de dos proveedores externos de direcciones contra el código postal real de cada persona.
- **Qué mirar:** `outputs/automation.md`, sobre todo la tabla del paso 5 (antes frente a ahora) y la comparación de proveedores (el más barato devuelve muchos datos erróneos).
- **Qué probar:** en `inputs/automation.yaml`, baja `z_threshold` a 1 y verás cómo se disparan las alertas de volumen: demasiadas alertas acaban ignoradas. O cambia la `accuracy` de un proveedor y mira cómo cambia la recomendación.
- [README del capítulo](chapters/ch14_automatizacion/README.md)

### Paso 15. Adopción que impulsa el negocio

```bash
uv run python -m chapters.ch15_adopcion.run
```

- **Qué produce:** KPI de adopción de cuatro soluciones de datos a partir de logs de uso simulados (usuarios activos, adopción frente a usuarios objetivo, retención y departamentos), el coste de la baja adopción, el diagnóstico de por qué falla una adopción (la solución, la empresa o el líder) con su plan de recuperación, y la hoja de ruta de adopción tras la salida en vivo.
- **Qué mirar:** `outputs/adoption.md`, sobre todo el lanzamiento fallido de la plataforma de visualización (solo la usa el equipo de datos) y lo que cuesta al año.
- **Qué probar:** en `inputs/adoption.yaml`, mejora la encuesta de la plataforma de visualización y sube su `share` para simular el relanzamiento: cambian el diagnóstico y el coste.
- [README del capítulo](chapters/ch15_adopcion/README.md)

### Paso 16. Resultados confiables con resultados que importan

```bash
uv run python -m chapters.ch16_resultados_confiables.run
uv run python -m chapters.ch17_caso_estudio_novapay.run
```

- **Qué produce:** la revisión de capacidades del libro (gobierno, metadatos, calidad, arquitectura, operaciones y datos primarios, cada una con 5 etapas). El estado de cada etapa sale de la **evidencia** que han dejado los capítulos anteriores. Además: los compromisos del capítulo 5 medidos de nuevo (cumplido, en plazo, riesgo anticipado o retrasado), un mensaje estructurado para cada desvío y mensajes para cada audiencia. Todo en un **informe HTML** consolidado.
- **Qué mirar:** abre `outputs/capability_review.html` en el navegador.
- **Qué probar:** reconstruye solo el warehouse (`uv run dglab build`) y ejecuta este paso: las etapas de metadatos, calidad y datos primarios pasan a pendientes, porque el estado no se declara, se comprueba. Después ejecuta el pipeline del paso 11 y vuelve a ejecutarlo.
- [README del capítulo](chapters/ch16_resultados_confiables/README.md)

### Paso 17. Caso de estudio: NovaPay, entidad financiera regulada

```bash
uv run python -m chapters.ch17_caso_estudio_novapay.run
```

- **Qué produce:** el caso del libro de punta a punta sobre NovaPay, con su propio warehouse (`data/warehouse/novapay.duckdb`). El informe de liquidez se consolidaba a mano desde hojas de cálculo con partidas duplicadas, importes en texto, vacíos y signos cambiados. El paso reutiliza las herramientas de los capítulos anteriores: segregación de funciones con la RACI (3), reglas de calidad antes y después de remediar (8), linaje de la ratio (7), clasificación de datos personales ampliada con el IBAN (6), opciones de inversión con VAN (1) y revisión de jerga del mensaje al supervisor (12). Genera el caso completo, el resumen para el comité de dirección, el mensaje al supervisor y un gráfico de la ratio manual frente a la remediada y la real.
- **Qué mirar:** `outputs/case_study.md` y `outputs/liquidity_ratio.png`. La hoja a mano marca 25 días por debajo del mínimo regulatorio cuando en realidad fueron 6.
- **Qué probar:** en `inputs/novapay.yaml`, sube `defects.missing_amount` y mira cómo bajan los días certificados; o vuelve a juntar preparación y revisión en `raci_after` y verás reaparecer el fallo de segregación.
- [README del capítulo](chapters/ch17_caso_estudio_novapay/README.md)

### Ejecutar todo de una vez

Con un solo comando:

```bash
uv run dglab run-all                     # warehouse + capítulos 1 a 17 + repetir 4 y 5 para ver el avance
uv run dglab run-all --start 6 --no-build  # retomar desde un capítulo sobre el warehouse actual
```

Se detiene en el primer capítulo que falle y termina con una tabla de tiempos. Es lo mismo que ejecutar a mano:

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
uv run python -m chapters.ch10_datos_primarios_mdm.run
uv run python -m chapters.ch11_operaciones_datos.run
uv run python -m chapters.ch12_lanzamiento.run
uv run python -m chapters.ch13_quick_wins.run
uv run python -m chapters.ch14_automatizacion.run
uv run python -m chapters.ch15_adopcion.run
uv run python -m chapters.ch16_resultados_confiables.run
uv run python -m chapters.ch17_caso_estudio_novapay.run
```

Para dejar solo el warehouse completo (carga y capítulos 10, 6, 7 y 8) basta con el pipeline del paso 11: `uv run python -m chapters.ch11_operaciones_datos.pipeline`.

Este orden refleja la línea base: los capítulos 4 y 5 se ejecutan antes de documentar el warehouse y de calcular el linaje. Para ver el avance, vuelve a ejecutar 4 y 5 al final.

## Comandos útiles

```bash
uv run pytest                            # todos los tests
uv run pytest chapters/ch04_linea_base_madurez  # los de un capítulo
uv run ruff check .                      # lint
uv run dglab --help                      # comandos: build, generate, load, reset, run-all
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

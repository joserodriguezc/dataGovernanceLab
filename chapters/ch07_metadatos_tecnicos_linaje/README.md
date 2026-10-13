# Capítulo 7: Metadatos técnicos y linaje de datos

> **Libro:** *Technical Metadata and Data Lineage*. Parte 2: Las capacidades de gobierno de datos en profundidad.
> **Microproyecto:** Linaje de datos a nivel de columna.

**Estado:** ✅ hecho

## Objetivo

Reconstruir la cadena de suministro de datos de NovaMercado (del sistema de origen hasta el KPI del comité) a partir del SQL real del warehouse. Con ella se analiza el impacto de un cambio antes de hacerlo y se valida si quien produce la cifra de ventas sabe de dónde sale.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| Metadatos técnicos: esquema, diccionario y linaje | El esquema sale del warehouse; el linaje, del SQL de las transformaciones | [lineage.py](lineage.py) |
| Linaje: dónde están los datos, de dónde vienen y cómo se transformaron | Linaje a nivel de columna con sqlglot y tipo de transformación (directo, renombrado, conversión de tipo, calculado, agregado o constante) | [lineage.py](lineage.py) |
| Gestión del cambio: saber qué se ve afectado *antes* de un cambio | Análisis de impacto, con aviso si toca métricas críticas del comité | [analysis.py](analysis.py), [impact.py](impact.py) |
| Encontrar el origen de un problema en un informe | Árbol de "de dónde viene" para cualquier columna | [impact.py](impact.py) |
| Proteger los datos: dónde está la PII | Cruce del linaje con la clasificación del capítulo 6: ¿llega PII a curated? | [analysis.py](analysis.py) |
| Empezar por un informe o una métrica importante | Métricas críticas del comité con linaje hasta el origen | [inputs/lineage.yaml](inputs/lineage.yaml) |
| Buena práctica: validar el linaje en 7 pasos con quien produce el informe | Narrativa del Controller de ventas frente al linaje técnico | [analysis.py](analysis.py) |
| Optimizar el recorrido de los datos | Qué parte de cada fuente llega a la capa curated | [analysis.py](analysis.py) |
| Métricas de madurez y valor: ROI = (beneficios − costes) / costes | Métricas del libro y ROI con supuestos explícitos | [analysis.py](analysis.py) |

## Entregables

En `outputs/`:

| Archivo | Contenido |
|---|---|
| `data_lineage.md` | Cadena de suministro (Mermaid) por capas, sistemas de origen, linaje columna a columna de la venta neta y cada transformación con sus filtros |
| `lineage_validation.md` | Los 7 pasos de la validación: narrativa frente a linaje técnico y acciones |
| `technical_metadata.md` | Madurez, ejemplos de impacto, hallazgos (alcance de cada fuente, PII), valor y ROI |

En el **warehouse**: las tablas `meta.lineage_edges` (columna → columna) y `meta.lineage_steps` (tabla → tabla, con filtros).

## Cómo ejecutarlo

```bash
uv run dglab build                                   # si no está el warehouse
uv run python -m chapters.ch06_gestion_metadatos.run # recomendado: para el cruce con la PII
uv run python -m chapters.ch07_metadatos_tecnicos_linaje.run
uv run python -m chapters.ch07_metadatos_tecnicos_linaje.impact raw.ecom_orders.status
uv run python -m chapters.ch07_metadatos_tecnicos_linaje.impact curated.agg_sales_daily_channel.revenue --origen
uv run pytest chapters/ch07_metadatos_tecnicos_linaje
```

## Decisiones de modelado

- **El linaje sale del código, no de una documentación manual.** Se analizan los ficheros SQL de [src/dglab/warehouse/sql/](../../src/dglab/warehouse/sql/): si cambia una transformación, el linaje se actualiza en la siguiente ejecución.
- **Los filtros y las claves de unión también son dependencias.** La primera versión solo seguía las columnas proyectadas. Con ella, un cambio en `status` parecía no afectar a la venta neta, aunque el `WHERE status NOT IN ('cancelado', 'devuelto')` decide qué filas cuentan. Ahora las columnas del `WHERE` y del `ON` de los joins generan aristas de tipo *filtro* y *clave de unión*.
- **Las tablas raw se enlazan con su sistema de origen** por el prefijo del nombre (`crm_`, `ecom_`, `pos_`, `erp_`).
- **Validación por columnas de origen.** Lo que la narrativa cita se compara con las *raíces* del linaje: las columnas de raw de las que depende la cifra.

## Conclusiones para NovaMercado

1. **La venta neta no sale de donde cree su responsable.** El Controller de ventas dice "cantidad × precio de lista del ERP". El linaje muestra que en tienda se usa el importe ya calculado por el POS (`raw.pos_sales.amount`) y online, cantidad × precio del pedido. El ERP no interviene. Son 5 diferencias que hay que repasar con él: es exactamente el caso "fuente supuesta frente a fuente real" del libro.
2. **`status` es una columna crítica oculta.** Un cambio en `raw.ecom_orders.status` afecta a 6 columnas y a dos KPI del comité (venta neta y transacciones), aunque no aparece en ninguna fórmula.
3. **Los datos de cliente no llegan a curated.** CRM, e-commerce y tarjetas de fidelización se cargan y se transforman, pero el 0 % de sus columnas alimenta un dataset curado. El golden record del capítulo 10 cerrará este hueco. A cambio, ninguna PII llega hoy a curated.
4. **Todas las tablas curated y las 3 métricas críticas tienen linaje hasta el origen.** En el capítulo 5, el resultado "Linaje documentado" pasa a estar logrado.
5. **Las tablas raw no tienen el esquema documentado** (0 de 8). El capítulo 6 documentó staging y curated, pero no las fuentes.
6. **El ROI estimado es del 192 %** (US$ 175.500/año de beneficio frente a US$ 60.000 de coste), con supuestos que hay que acordar con el negocio.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada
- [x] Paso añadido al recorrido del README raíz

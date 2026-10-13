# Datos sintéticos de NovaMercado (Fase 0)

Base de datos compartida por los capítulos técnicos del laboratorio. Es **determinista**: con la misma semilla se generan siempre los mismos datos y los mismos defectos.

```bash
uv run dglab build              # generar CSV + construir el warehouse
uv run dglab generate --seed 7  # solo generar, con otra semilla
uv run dglab load               # solo (re)construir el warehouse desde data/raw
uv run dglab reset              # borrar todo lo generado
```

## Cómo se generan

1. Se crean **personas reales** (2.000 por defecto) con nombre, dos apellidos, email, móvil, fecha de nacimiento y código postal.
2. Cada persona se registra o no en cada sistema según su probabilidad de presencia (CRM 85 %, e-commerce 55 %, tiendas 45 %). Cada sistema guarda la persona a su manera:

| Sistema | Tabla raw | Cómo llega el cliente |
|---|---|---|
| CRM | `crm_customers` | Nombre y apellidos por separado, teléfono `+34 612 345 678` |
| E-commerce | `ecom_customers` | Nombre completo, a veces sin tildes; email a veces en mayúsculas; teléfono `612345678` |
| Tiendas (POS) | `pos_loyalty_cards` | Tarjeta de fidelización: `NOMBRE APELLIDO` en mayúsculas y un solo apellido; teléfono `612-345-678` |

3. Se generan el catálogo (`erp_products`), los proveedores (`erp_suppliers`), las tiendas (`erp_stores`) y las ventas: líneas de ticket en tienda (`pos_sales`) y líneas de pedido online (`ecom_orders`). La moneda es USD.

## Defectos sembrados

Las tasas se configuran en `dglab.synthetic.DefectRates`. Se afecta a un número exacto de registros (n × tasa).

| Defecto | Tasa | Lo usa el capítulo |
|---|---:|---|
| `crm_duplicates`: la misma persona dada de alta dos veces en el CRM, con una errata en el nombre | 3 % | 10 |
| `crm_null_email`: email obligatorio vacío | 5 % | 8 |
| `ecom_bad_date_format`: fecha de alta en `dd/mm/aaaa` en vez de ISO | 20 % | 8 |
| `ecom_invalid_postal`: código postal de cliente inválido | 4 % | 8 |
| `order_invalid_postal`: código postal de envío inválido | 3 % | 8, 14 |
| `pos_missing_phone`: tarjeta de fidelización sin teléfono | 15 % | 8, 10 |
| `pos_negative_price`: precio unitario negativo en el ticket | 0,5 % | 8 |
| `product_missing_category`: producto sin categoría | 5 % | 6, 8 |
| `supplier_missing_contact`: proveedor sin persona ni email de contacto | 10 % | 6, 13 |

Además, el mismo cliente repartido entre CRM, e-commerce y tiendas con variaciones es el reto de datos maestros del capítulo 10.

## Solucionario (`data/raw/_truth/`)

- `customer_links.csv`: qué registro de cada sistema corresponde a cada persona real (`person_id`, `system`, `source_id`).
- `defects.json`: los ids afectados por cada defecto sembrado.

**Solo se usa para evaluar** si las detecciones y el matching de los capítulos aciertan, nunca como entrada de una solución.

## Warehouse (`data/warehouse/novamercado.duckdb`)

| Capa | Contenido | Tablas |
|---|---|---|
| `raw` | Los CSV tal como llegan, todo como texto | Una por CSV |
| `staging` | Tipos correctos y normalizaciones técnicas (emails en minúsculas, teléfonos con 9 dígitos, las dos variantes de fecha). **No** corrige defectos de negocio | `stg_*` |
| `curated` | Modelo conformado | `dim_store`, `dim_product`, `fct_sales` (todos los canales), `agg_sales_daily_channel` (la cifra de ventas, sin cancelados ni devoluciones) |

Las transformaciones son los ficheros SQL numerados de [src/dglab/warehouse/sql/](../src/dglab/warehouse/sql/). El capítulo 7 los analiza para construir el linaje.

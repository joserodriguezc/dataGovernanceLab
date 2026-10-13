"""Generador de datos sintéticos de NovaMercado (Fase 0, pendiente de implementar).

Generará con semilla fija los datos de clientes, productos, proveedores, tiendas y pedidos
de cada sistema de origen, con defectos de calidad sembrados a propósito (duplicados, nulos
y formatos inconsistentes) para los capítulos 8 y 10, y los cargará en DuckDB en las capas
raw, staging y curated.
"""

DEFAULT_SEED = 42

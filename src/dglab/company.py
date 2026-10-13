"""Constantes de la empresa ficticia NovaMercado, el hilo conductor de todos los capítulos."""

COMPANY_NAME = "NovaMercado"
COMPANY_DESCRIPTION = "Retail omnicanal (tiendas físicas, e-commerce y app móvil)"
FINANCIAL_SUBSIDIARY = "NovaPay"  # filial financiera regulada (capítulo 17)

# Dominios de datos y su unidad de negocio responsable
DATA_DOMAINS: dict[str, str] = {
    "customer": "Marketing y CRM",
    "product": "Comercial",
    "supplier": "Compras",
    "sales": "Ventas",
    "store": "Operaciones",
    "finance": "Finanzas",
}

# Nombre en español de cada dominio, para los informes
DOMAIN_NAMES: dict[str, str] = {
    "customer": "Cliente",
    "product": "Producto",
    "supplier": "Proveedor",
    "sales": "Ventas",
    "store": "Tiendas",
    "finance": "Finanzas",
}

# Sistemas de origen simulados
SOURCE_SYSTEMS: dict[str, str] = {
    "pos": "Punto de venta de tiendas",
    "ecom": "Plataforma e-commerce",
    "crm": "CRM de clientes y fidelización",
    "erp": "ERP de compras, inventario y finanzas",
}

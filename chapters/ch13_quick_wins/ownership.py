"""Registro de propiedad de los datos: cada activo con su ejecutivo de dominio y stewards.

Une los roles por dominio del capítulo 3 con el catálogo del capítulo 6 (las tablas de cada
dominio). Si el catálogo no está en el warehouse, el registro queda a nivel de dominio.
"""

import duckdb
import pandas as pd

from chapters.ch03_equipo_alto_rendimiento.team import FunctionalRoles
from dglab.company import DOMAIN_NAMES


def ownership_register(con: duckdb.DuckDBPyConnection,
                       roles: list[FunctionalRoles]) -> pd.DataFrame:
    try:
        assets = con.execute("SELECT domain, table_fqn FROM meta.catalog_tables "
                             "WHERE domain IS NOT NULL ORDER BY domain, table_fqn").df()
    except duckdb.CatalogException:
        assets = pd.DataFrame(columns=["domain", "table_fqn"])
    rows = []
    for r in roles:
        tables = assets.loc[assets["domain"] == r.domain, "table_fqn"].tolist() or [None]
        for t in tables:
            rows.append({
                "dominio": DOMAIN_NAMES[r.domain], "activo": t,
                "ejecutivo": r.executive, "steward_negocio": ", ".join(r.business_stewards),
                "steward_tecnico": ", ".join(r.technical_stewards),
                "huecos": ", ".join(r.gaps),
            })
    return pd.DataFrame(rows)

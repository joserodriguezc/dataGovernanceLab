"""El proceso automatizado: informe semanal de ventas por región con monitorización.

Sustituye los pasos manuales: integra tienda y online, asigna la región (tiendas por su
región; online por el código postal de envío y los datos de referencia del capítulo 10),
aplica la regla oficial de cancelaciones y comprueba que cuadra con la cifra oficial.
Después lanza las alertas de monitorización (observabilidad de datos).
"""

import time
from dataclasses import dataclass

import duckdb
import pandas as pd

from dglab.reporting import fmt_pct

WEEKLY_SQL = """
WITH ref AS (
    SELECT province_code, sales_region FROM pdm.ref_province
), sales AS (
    SELECT date_trunc('week', s.sale_ts)::DATE AS week, st.region, s.amount
    FROM staging.stg_pos_sales s JOIN curated.dim_store st ON st.store_id = s.store_id
    UNION ALL
    SELECT date_trunc('week', o.order_ts)::DATE, coalesce(r.sales_region, 'Sin región'),
           o.amount
    FROM staging.stg_ecom_orders o
    LEFT JOIN ref r ON r.province_code = substr(o.shipping_postal_code, 1, 2)
                   AND regexp_full_match(o.shipping_postal_code, '\\d{5}')
    WHERE o.status NOT IN ('cancelado', 'devuelto')
)
SELECT week, region, round(sum(amount), 2) AS net_sales, count(*) AS lines
FROM sales GROUP BY week, region ORDER BY week, region
"""


@dataclass(frozen=True)
class Alert:
    week: object
    region: str
    kind: str
    message: str


def build_report(con: duckdb.DuckDBPyConnection) -> tuple[pd.DataFrame, float]:
    """Informe semanal por región y segundos que tarda en generarse."""
    start = time.perf_counter()
    df = con.execute(WEEKLY_SQL).df()
    df["week"] = pd.to_datetime(df["week"]).dt.date
    return df, time.perf_counter() - start


def reconcile(con: duckdb.DuckDBPyConnection, report: pd.DataFrame) -> float:
    """Diferencia entre el total del informe y la cifra oficial de ventas (debe ser 0)."""
    official = con.execute("SELECT sum(revenue) FROM curated.agg_sales_daily_channel"
                           ).fetchone()[0]
    return round(float(report["net_sales"].sum() - official), 2)


def complete_weeks(report: pd.DataFrame) -> pd.DataFrame:
    """Quita la primera y la última semana, que suelen estar incompletas."""
    weeks = sorted(report["week"].unique())
    return report[report["week"].isin(weeks[1:-1])]


def monitor(con: duckdb.DuckDBPyConnection, report: pd.DataFrame, window: int,
            z_threshold: float, max_unmapped: float, allow_negative: bool) -> list[Alert]:
    alerts = []
    report = complete_weeks(report)
    # 1. Caída de volumen anómala: por debajo de la media de las semanas anteriores menos
    #    z desviaciones típicas (un umbral fijo salta con la variación normal de las ventas)
    weekly = report[report["region"] != "Sin región"].pivot_table(
        index="week", columns="region", values="net_sales", aggfunc="sum").sort_index()
    past = weekly.rolling(window, min_periods=window)
    mean, std = past.mean().shift(1), past.std().shift(1)
    drops = (weekly < mean - z_threshold * std) & mean.notna()
    for week, row in drops.iterrows():
        for region, hit in row.items():
            if hit:
                alerts.append(Alert(week, region, "Caída de volumen anómala",
                                    f"{weekly.at[week, region]:,.0f} frente a una media de "
                                    f"{mean.at[week, region]:,.0f}".replace(",", ".")))
    # 2. Ventas online sin región asignable
    total = report.groupby("week")["net_sales"].sum()
    unmapped = report[report["region"] == "Sin región"].set_index("week")["net_sales"]
    share = (unmapped / total).fillna(0)
    for week, value in share.items():
        if value > max_unmapped:
            alerts.append(Alert(week, "Sin región", "Sin región asignable",
                                f"{fmt_pct(value, 1)} de la venta de la semana"))
    # 3. Líneas con importe negativo
    if not allow_negative:
        neg = con.execute("""
            SELECT date_trunc('week', sale_ts)::DATE AS week, count(*)
            FROM staging.stg_pos_sales WHERE amount < 0 GROUP BY 1 ORDER BY 1""").fetchall()
        for week, n in neg:
            alerts.append(Alert(week, "Tiendas", "Importes negativos",
                                f"{n} líneas de ticket con importe negativo"))
    return sorted(alerts, key=lambda a: (a.week, a.kind, a.region))

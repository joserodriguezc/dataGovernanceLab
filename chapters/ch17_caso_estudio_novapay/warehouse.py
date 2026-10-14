"""Warehouse DuckDB de NovaPay y el informe "a la manera de antes" (la hoja consolidada)."""

from pathlib import Path

import duckdb
import pandas as pd

from .data import NovaPayData

SQL = Path(__file__).parent / "sql" / "novapay.sql"


def build(db: Path, data: NovaPayData, units: dict[str, str]) -> None:
    db.parent.mkdir(parents=True, exist_ok=True)
    if db.exists():
        db.unlink()
    with duckdb.connect(str(db)) as con:
        for schema in ("raw", "staging", "curated"):
            con.execute(f"CREATE SCHEMA {schema}")
        frames = {
            "liquidity_submissions": data.submissions,
            "accounts": data.customers,
            "business_units": pd.DataFrame(
                [{"business_unit": u, "side": s} for u, s in units.items()]),
        }
        for name, df in frames.items():
            con.register("_f", df.astype("string") if name != "business_units" else df)
            con.execute(f"CREATE TABLE raw.{name} AS SELECT * FROM _f")
            con.unregister("_f")
        con.execute(SQL.read_text(encoding="utf-8"))


def manual_report(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Lo que hacía la preparadora: sumar las hojas tal como llegan.

    Los importes escritos como texto no suman (la hoja los trata como texto), los
    duplicados cuentan dos veces y los signos cambiados restan.
    """
    return con.execute("""
        SELECT CAST(s.report_date AS DATE) AS report_date,
               sum(CASE WHEN u.side = 'asset' THEN TRY_CAST(s.amount AS DOUBLE) ELSE 0 END)
                   AS liquid_assets,
               sum(CASE WHEN u.side = 'liability' THEN TRY_CAST(s.amount AS DOUBLE) ELSE 0 END)
                   AS short_term_liabilities
        FROM raw.liquidity_submissions s JOIN raw.business_units u USING (business_unit)
        GROUP BY 1 ORDER BY 1""").df().assign(
        liquidity_ratio=lambda d: d.liquid_assets / d.short_term_liabilities)


def true_report(truth: pd.DataFrame) -> pd.DataFrame:
    piv = truth.pivot_table(index="report_date", columns="side", values="amount", aggfunc="sum")
    return pd.DataFrame({"report_date": piv.index, "liquid_assets": piv["asset"].values,
                         "short_term_liabilities": piv["liability"].values,
                         "liquidity_ratio": (piv["asset"] / piv["liability"]).values})

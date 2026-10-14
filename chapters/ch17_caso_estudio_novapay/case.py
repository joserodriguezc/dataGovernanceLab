"""Análisis del caso NovaPay con las herramientas de los capítulos anteriores.

- Segregación de funciones con la RACI del capítulo 3.
- Calidad de datos con el motor de reglas del capítulo 8 (antes y después de remediar).
- Linaje del informe con el analizador de SQL del capítulo 7.
- Clasificación de datos personales con la política del capítulo 6.
- Opciones de inversión con el caso de negocio del capítulo 1.
- Revisión de jerga de los mensajes con la del capítulo 12.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import duckdb

from chapters.ch03_equipo_alto_rendimiento.raci import RaciInput
from chapters.ch06_gestion_metadatos.classify import ClassificationPolicy, classify
from chapters.ch07_metadatos_tecnicos_linaje.lineage import (
    column_graph,
    parse_sql,
    warehouse_schema,
)
from chapters.ch08_calidad_datos.rules import Rule, RuleResult, run_rule

AMOUNT_OK = "^-?[0-9]+(\\.[0-9]+)?$"

RAW_RULES = [
    Rule(id="NP-01", table="raw.liquidity_submissions", column="amount", type="not_null",
         dimension="completitud", severity=1, threshold=1.0, remediation="corregir_en_origen",
         description="Toda partida enviada tiene importe."),
    Rule(id="NP-02", table="raw.liquidity_submissions", column="amount", type="regex",
         pattern=AMOUNT_OK, dimension="consistencia", severity=1, threshold=1.0,
         remediation="estandarizar", description="El importe es un número, no un texto."),
    Rule(id="NP-03", table="raw.liquidity_submissions", column="amount", type="condition",
         condition="count(*) OVER (PARTITION BY report_date, business_unit, item) = 1",
         dimension="unicidad", severity=1, threshold=1.0, remediation="excluir",
         description="Cada partida se envía una sola vez al día."),
    Rule(id="NP-04", table="raw.liquidity_submissions", column="amount", type="condition",
         condition="NOT starts_with(coalesce(amount, ''), '-')", dimension="exactitud",
         severity=1, threshold=1.0, remediation="estandarizar",
         description="Los importes llegan en positivo (el signo lo da el lado del balance)."),
]
CURATED_RULES = [
    Rule(id="NP-05", table="staging.stg_liquidity_items", column="amount", type="not_null",
         dimension="completitud", severity=1, threshold=1.0, remediation="corregir_en_origen",
         description="Toda partida del informe tiene importe."),
    Rule(id="NP-06", table="staging.stg_liquidity_items", column="amount", type="positive",
         dimension="exactitud", severity=1, threshold=1.0, remediation="estandarizar",
         description="Los importes del informe son positivos."),
]
TABLE_DOCS = {
    "raw.liquidity_submissions": "Partidas del informe de liquidez tal como las envía cada "
                                 "unidad en su hoja de cálculo.",
    "staging.stg_liquidity_items": "Partidas interpretadas y sin duplicados: una por día, "
                                   "unidad y partida.",
    "curated.fct_liquidity_report": "Informe diario de liquidez: activos líquidos frente a "
                                    "obligaciones a corto plazo.",
    "staging.stg_accounts": "Cuentas de clientes del monedero y la tarjeta (datos personales).",
}


@dataclass(frozen=True)
class Segregation:
    ok: bool
    overlap: list[str]


def segregation(raci: RaciInput, prepare: str, review: str) -> Segregation:
    """Quien prepara el informe no puede ejecutar ni responder de su revisión."""
    acts = {a.name: a for a in raci.activities}
    preparers = set(acts[prepare].R)
    reviewers = set(acts[review].R) | {acts[review].A}
    overlap = sorted(raci.roles[r] for r in preparers & reviewers)
    return Segregation(not overlap, overlap)


def run_rules(con: duckdb.DuckDBPyConnection, rules: list[Rule], keys: dict[str, str],
              as_of: date) -> list[RuleResult]:
    return [run_rule(con, r, keys[r.table], as_of) for r in rules]


def lineage_roots(con: duckdb.DuckDBPyConnection, sql: Path, column: str) -> list[str]:
    import networkx as nx
    edges, _ = parse_sql(sql.read_text(encoding="utf-8"), sql.name, warehouse_schema(con))
    g = column_graph(edges)
    return sorted(n for n in nx.ancestors(g, column) if g.in_degree(n) == 0)


def document(con: duckdb.DuckDBPyConnection) -> int:
    for table, text in TABLE_DOCS.items():
        con.execute(f"COMMENT ON TABLE {table} IS '{text}'")
    return len(TABLE_DOCS)


def pii_columns(con: duckdb.DuckDBPyConnection, policy: ClassificationPolicy) -> list[tuple]:
    cols = con.execute("SELECT column_name FROM information_schema.columns WHERE "
                       "table_schema = 'staging' AND table_name = 'stg_accounts'").fetchall()
    out = []
    for (c,) in cols:
        values = [r[0] for r in con.execute(
            f'SELECT CAST("{c}" AS VARCHAR) FROM staging.stg_accounts LIMIT 100').fetchall()]
        cls = classify(f"staging.stg_accounts.{c}", c, values, policy)
        if cls.level in ("restricted", "confidential"):
            out.append((c, policy.level_name(cls.level), cls.category))
    return out


def certify_days(con: duckdb.DuckDBPyConnection, documented: bool, has_lineage: bool) -> tuple:
    """Indicador de confianza del caso: documentado, con linaje y con calidad en umbral."""
    total, complete = con.execute(
        "SELECT count(*), count(*) FILTER (WHERE complete) FROM curated.fct_liquidity_report"
    ).fetchone()
    certified = complete if documented and has_lineage else 0
    return certified, total

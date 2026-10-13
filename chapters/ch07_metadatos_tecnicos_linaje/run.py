"""Capítulo 7: metadatos técnicos y linaje de datos a nivel de columna.

Analiza el SQL de `src/dglab/warehouse/sql/` y publica el linaje en el warehouse
(`meta.lineage_edges`). Requiere `uv run dglab build`; conviene ejecutar antes el capítulo 6
para cruzar el linaje con la clasificación de PII.
Uso: uv run python -m chapters.ch07_metadatos_tecnicos_linaje.run
"""

from collections import defaultdict
from pathlib import Path

from rich.console import Console

from chapters.ch04_linea_base_madurez.evidence import indicators
from chapters.ch06_gestion_metadatos.glossary import Glossary
from dglab.config import load_yaml
from dglab.paths import WAREHOUSE_DB
from dglab.reporting import fmt_money, render_template, write_text
from dglab.warehouse import connect, sql_files

from .analysis import (
    LineageInput,
    impact,
    maturity_metrics,
    path_to,
    pii_reaching,
    reach_curated,
    validate,
)
from .lineage import build_lineage, column_graph, table_graph
from .publish import write_lineage

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CH06_GLOSSARY = CHAPTER_DIR.parent / "ch06_gestion_metadatos" / "inputs" / "glossary.yaml"
COMPANY = "NovaMercado"
IMPACT_EXAMPLES = ["raw.pos_sales.amount", "raw.ecom_orders.status", "raw.erp_products.category",
                   "raw.crm_customers.birth_date"]


def _has_table(con, schema: str, table: str) -> bool:
    return bool(con.execute("SELECT count(*) FROM information_schema.tables WHERE "
                            "table_schema = ? AND table_name = ?", [schema, table]).fetchone()[0])


def main(out_dir: Path | None = None, db_path: Path = WAREHOUSE_DB) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    if not db_path.exists():
        raise FileNotFoundError(f"No existe {db_path}: ejecuta antes `uv run dglab build`")
    console = Console()
    inp = LineageInput.model_validate(load_yaml(INPUTS / "lineage.yaml"))
    terms = Glossary.model_validate(load_yaml(CH06_GLOSSARY)).column_terms()

    with connect(db_path) as con:
        before = indicators(con)["lineage_coverage"]
        edges, steps = build_lineage(con, sql_files(), {k: s.name for k, s in
                                                         inp.source_systems.items()})
        meta_rows = write_lineage(con, edges, steps)
        after = indicators(con)["lineage_coverage"]
        raw_columns = [f"raw.{t}.{c}" for t, c in con.execute(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_schema = 'raw'").fetchall()]
        curated = [f"curated.{t}" for (t,) in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'curated'"
        ).fetchall()]
        documented = {f"{s}.{t}" for s, t in con.execute(
            "SELECT schema_name, table_name FROM duckdb_tables() WHERE comment IS NOT NULL "
            "AND comment <> ''").fetchall()}
        pii_known = _has_table(con, "meta", "catalog_columns")
        pii = [r[0] for r in con.execute(
            "SELECT table_fqn || '.' || column_name FROM meta.catalog_columns "
            "WHERE classification = 'restricted'").fetchall()] if pii_known else []

    g, tg = column_graph(edges), table_graph(edges)
    missing = [m.column for m in inp.critical_metrics if m.column not in g]
    if missing or inp.validation.business_element not in g:
        raise ValueError(f"columnas de métricas críticas que no están en el linaje: {missing}")

    # Vistas para los informes
    layer_of = {"sistema": "Sistemas de origen", "raw": "raw", "staging": "staging",
                "curated": "curated"}
    layers = [(label, sorted(n for n in tg if n.split(".")[0] == key))
              for key, label in layer_of.items()]
    raw_by_system: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        if e.kind == "carga":
            raw_by_system[e.source_table.split(".")[1]].append(e.target_table)
    columns_by_table: dict[str, dict[str, dict]] = defaultdict(dict)
    for e in edges:
        if e.target_column is None or e.kind == "carga":
            continue
        info = columns_by_table[e.target_table].setdefault(
            e.target_column, {"kinds": [], "expressions": [], "sources": []})
        for key, value in (("kinds", e.kind), ("expressions", e.expression),
                           ("sources", e.source if e.source_column else None)):
            if value and value not in info[key]:
                info[key].append(value)
    kpi = path_to(g, inp.validation.business_element)
    kpi_edges = sorted((s, t, d["kind"]) for s, t, d in kpi.edges(data=True))

    result = validate(g, steps, inp.validation)
    rows = []
    for c in sorted(set(result.actual_sources) | set(inp.validation.claimed_sources)):
        claimed, actual = c in inp.validation.claimed_sources, c in result.actual_sources
        reading = ("Confirmado" if claimed and actual else
                   "⚠️ La narrativa lo cita, pero no se usa" if claimed else
                   "⚠️ Se usa, pero la narrativa no lo menciona")
        rows.append({"column": c, "claimed": claimed, "actual": actual, "reading": reading})
    impacts = [impact(g, c, inp.critical_metrics) for c in IMPACT_EXAMPLES]
    reach = reach_curated(g, sorted(raw_columns))
    reaching = pii_reaching(g, pii)
    maturity = maturity_metrics(edges, g, inp.source_systems, inp.critical_metrics, documented,
                                curated)
    constants = [e for e in edges if e.kind == "constante"]

    outputs = {
        "lineage": write_text(out_dir / "data_lineage.md", render_template(
            TEMPLATES, "data_lineage.md.j2", company=COMPANY, layers=layers,
            table_edges=sorted(tg.edges()), systems=inp.source_systems,
            raw_by_system=raw_by_system, kpi_edges=kpi_edges, steps=steps,
            columns_by_table=columns_by_table)),
        "validation": write_text(out_dir / "lineage_validation.md", render_template(
            TEMPLATES, "lineage_validation.md.j2", v=inp.validation, r=result, rows=rows,
            term=terms.get(inp.validation.business_element))),
        "technical": write_text(out_dir / "technical_metadata.md", render_template(
            TEMPLATES, "technical_metadata.md.j2", company=COMPANY, maturity=maturity,
            impacts=impacts, reach=reach, pii_known=pii_known, pii_reaching=reaching,
            constants=constants, value=inp.value)),
    }

    console.rule("[bold]Capítulo 7: Metadatos técnicos y linaje")
    console.print(f"Linaje: {len(edges)} aristas, {g.number_of_nodes()} columnas, "
                  f"{len(steps)} transformaciones · meta: "
                  f"{', '.join(f'{k} {v}' for k, v in meta_rows.items())}")
    console.print(f"Tablas curated con linaje: {before:.0%} → [bold]{after:.0%}[/bold]")
    console.print(f"Venta neta: {len(result.actual_sources)} columnas de origen; "
                  f"[yellow]{result.gaps} diferencias[/yellow] con la narrativa del "
                  f"{inp.validation.producer}")
    for i in impacts:
        console.print(f"  • Si cambia {i.column}: {len(i.affected)} columnas afectadas"
                      + (f", críticas: {', '.join(i.critical)}" if i.critical else ""))
    dark = [r.table for r in reach if not r.reaching]
    console.print(f"Tablas raw que no llegan a curated: {', '.join(dark) or 'ninguna'}")
    console.print("PII que llega a curated: "
                  + (str(len(reaching)) if pii_known else "sin evaluar (falta el capítulo 6)"))
    console.print(f"ROI estimado: {inp.value.roi:.0%} "
                  f"({fmt_money(sum(inp.value.benefits.values()))}/año de beneficio)")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

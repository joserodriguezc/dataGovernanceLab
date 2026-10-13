"""Capítulo 6: glosario de negocio, catálogo de datos, clasificación de PII y estándares.

Escribe en el warehouse (comentarios y esquema `meta`), así que requiere `uv run dglab build`
y debe volver a ejecutarse cada vez que se reconstruya el warehouse.
Uso: uv run python -m chapters.ch06_gestion_metadatos.run
"""

from collections import Counter
from pathlib import Path

import pandas as pd
from rich.console import Console

from chapters.ch03_equipo_alto_rendimiento.team import TeamInput
from chapters.ch04_linea_base_madurez.evidence import indicators
from dglab.company import DOMAIN_NAMES
from dglab.config import load_yaml
from dglab.paths import WAREHOUSE_DB
from dglab.reporting import fmt_money, render_template, write_text
from dglab.warehouse import connect

from .catalog import FORMAT_LABELS, CatalogInput, extract, sample_values
from .classify import ClassificationPolicy, classify
from .glossary import STATUS_LABELS, Glossary, broken_mappings, stewards_by_domain
from .publish import write_comments, write_meta
from .standards import StandardsInput, evaluate, maturity_metrics

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CH03_TEAM = CHAPTER_DIR.parent / "ch03_equipo_alto_rendimiento" / "inputs" / "team.yaml"
COMPANY = "NovaMercado"
LAYERS = ("raw", "staging", "curated")
SCOPE_LABELS = {"table": "Tablas", "column": "Columnas", "term": "Términos"}


def main(out_dir: Path | None = None, db_path: Path = WAREHOUSE_DB) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    if not db_path.exists():
        raise FileNotFoundError(f"No existe {db_path}: ejecuta antes `uv run dglab build`")
    console = Console()

    glossary = Glossary.model_validate(load_yaml(INPUTS / "glossary.yaml"))
    catalog_in = CatalogInput.model_validate(load_yaml(INPUTS / "catalog.yaml"))
    policy = ClassificationPolicy.model_validate(load_yaml(INPUTS / "classification.yaml"))
    standards = StandardsInput.model_validate(load_yaml(INPUTS / "standards.yaml"))
    stewards = stewards_by_domain(TeamInput.model_validate(load_yaml(CH03_TEAM)).functional_roles)
    column_terms = glossary.column_terms()

    with connect(db_path) as con:
        before = indicators(con)["documented_tables"]
        tables = extract(con)
        unknown = set(catalog_in.tables) - {t.fqn for t in tables}
        for fqn in sorted(unknown):  # p. ej. curated.dim_customer antes del capítulo 10
            console.print(f"[yellow]El catálogo anota {fqn}, que aún no existe: se omite[/yellow]")
        for t in tables:
            t.annotation = catalog_in.tables.get(t.fqn)
            if t.domain and t.domain in stewards:
                t.business_stewards = stewards[t.domain].business
                t.technical_stewards = stewards[t.domain].technical
            for c in t.columns:
                c.term = column_terms.get(c.fqn)
                result = classify(c.fqn, c.name, sample_values(con, c, policy.sample_size),
                                  policy)
                c.level, c.category, c.method = result.level, result.category, result.method
        comments = write_comments(con, tables, glossary)
        meta_rows = write_meta(con, tables, glossary, stewards,
                               {k: v.name for k, v in policy.levels.items()})
        after = indicators(con)["documented_tables"]
        has_lineage = con.execute("SELECT count(*) FROM information_schema.tables WHERE "
                                  "table_schema = 'meta' AND table_name = 'lineage_edges'"
                                  ).fetchone()[0]
        lineage_tables = {r[0] for r in con.execute(
            "SELECT DISTINCT target_table FROM meta.lineage_edges").fetchall()} if has_lineage \
            else set()

    columns = [c for t in tables for c in t.columns]
    broken = broken_mappings(glossary, {c.fqn for c in columns})
    compliance = evaluate(standards.standards, tables, glossary, stewards)
    maturity = maturity_metrics(tables, compliance, lineage_tables)
    restricted = [c for c in columns if policy.is_restricted(c.level)]
    level_order = sorted(policy.levels, key=lambda k: -policy.levels[k].order)
    matrix = []
    for level in level_order:
        row = {layer: sum(c.level == level for t in tables if t.layer == layer
                          for c in t.columns) for layer in LAYERS}
        row["_total"] = sum(row.values())
        matrix.append((level, row))
    by_domain = [(d, [t for t in glossary.terms if t.domain == d])
                 for d in DOMAIN_NAMES if any(t.domain == d for t in glossary.terms)]
    domains = [d for d in DOMAIN_NAMES if any(t.domain == d for t in tables)]
    sensitive = {t.fqn: sum(policy.levels[c.level].order >= 2 for c in t.columns)
                 for t in tables}
    level_names = {k: v.name for k, v in policy.levels.items()}

    csv_path = out_dir / "pii_classification.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"column": c.fqn, "level": level_names[c.level], "category": c.category,
                   "method": c.method, "business_term": c.term} for c in columns]
                 ).to_csv(csv_path, index=False, encoding="utf-8")
    common = {"company": COMPANY, "domain_names": DOMAIN_NAMES}
    outputs = {
        "classification_csv": csv_path,
        "glossary": write_text(out_dir / "business_glossary.md", render_template(
            TEMPLATES, "business_glossary.md.j2", **common, terms=glossary.terms,
            status_counts=sorted(Counter(t.status for t in glossary.terms).items()),
            status_labels=STATUS_LABELS, by_domain=by_domain, stewards=stewards)),
        "catalog": write_text(out_dir / "data_catalog.md", render_template(
            TEMPLATES, "data_catalog.md.j2", **common, tables=tables,
            format_labels=FORMAT_LABELS, sensitive=sensitive, level_names=level_names)),
        "classification": write_text(out_dir / "pii_classification.md", render_template(
            TEMPLATES, "pii_classification.md.j2", **common, sample_size=policy.sample_size,
            layers=LAYERS, matrix=matrix, level_names=level_names, restricted=restricted,
            overrides=policy.overrides)),
        "standards": write_text(out_dir / "metadata_standards.md", render_template(
            TEMPLATES, "metadata_standards.md.j2", **common, pub=standards.publication,
            compliance=compliance, scope_labels=SCOPE_LABELS, domains=domains,
            maturity=maturity, broken=broken, v=catalog_in.value)),
    }

    console.rule("[bold]Capítulo 6: Gestión de metadatos")
    console.print(f"Glosario: {len(glossary.terms)} términos · catálogo: {len(tables)} tablas, "
                  f"{len(columns)} columnas · {len(restricted)} columnas restringidas (PII)")
    console.print(f"Warehouse: {comments} comentarios y esquema meta "
                  f"({', '.join(f'{k} {v}' for k, v in meta_rows.items())})")
    console.print(f"Tablas curated documentadas: {before:.0%} → [bold]{after:.0%}[/bold]")
    for c in compliance:
        if c.rate < 1:
            console.print(f"[yellow]{c.standard.id}[/yellow] {c.standard.text} "
                          f"{c.passed}/{c.total}")
    for term, col in broken:
        console.print(f"[red]Vínculo roto:[/red] {term} → {col}")
    console.print(f"Valor estimado: "
                  f"{fmt_money(catalog_in.value.catalog_value + catalog_in.value.glossary_value)}"
                  "/año")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

"""Capítulo 9: arquitectura de datos (as-is, to-be, principios, estándares y revisión SDLC).

Requiere `uv run dglab build`. Si se han ejecutado los capítulos 6-8, las medidas de éxito
incluyen documentación, certificación e incidencias de calidad.
Uso: uv run python -m chapters.ch09_arquitectura_datos.run
"""

from collections import Counter, defaultdict
from pathlib import Path

from pydantic import BaseModel, Field
from rich.console import Console

from dglab.config import load_yaml
from dglab.paths import ROOT, WAREHOUSE_DB
from dglab.reporting import fmt_pct, render_template, write_text
from dglab.warehouse import connect, sql_files

from .lint import lint_files
from .review import make_linter

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
COMPANY = "NovaMercado"
MANUAL_WORDS = ("manual", "copia", "email")


class Store(BaseModel):
    id: str
    name: str
    kind: str


class Flow(BaseModel):
    from_: str = Field(alias="from")
    to: str
    how: str
    pii: bool

    @property
    def manual(self) -> bool:
        return any(w in self.how.lower() for w in MANUAL_WORDS)


class AsIs(BaseModel):
    stores: list[Store]
    flows: list[Flow]


class Layer(BaseModel):
    name: str
    components: list[str]


class ToBe(BaseModel):
    layers: list[Layer]
    retired: list[str]


class Principle(BaseModel):
    id: str
    text: str


class Architecture(BaseModel):
    as_is: AsIs
    to_be: ToBe
    principles: list[Principle]
    program: dict
    roadmap: list[dict]


def _scalar(con, sql: str):
    try:
        return con.execute(sql).fetchone()[0]
    except Exception:  # la tabla meta aún no existe: el capítulo no se ha ejecutado
        return None


def main(out_dir: Path | None = None, db_path: Path = WAREHOUSE_DB) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    if not db_path.exists():
        raise FileNotFoundError(f"No existe {db_path}: ejecuta antes `uv run dglab build`")
    console = Console()
    arch = Architecture.model_validate(load_yaml(INPUTS / "architecture.yaml"))
    stores = {s.id for s in arch.as_is.stores}
    bad = [f"{f.from_}->{f.to}" for f in arch.as_is.flows if {f.from_, f.to} - stores]
    if bad or set(arch.to_be.retired) - stores:
        raise ValueError(f"flujos o retiradas con almacenes desconocidos: {bad}")
    linter = make_linter()

    proposals = sorted((INPUTS / "proposals").glob("*.sql"))
    with connect(db_path, read_only=True) as con:
        findings = linter.lint_warehouse(con)
        reviews = lint_files(linter, con, [*sql_files(), *proposals])
        documented = _scalar(con, "SELECT avg(CASE WHEN comment <> '' THEN 1 ELSE 0 END) "
                                  "FROM duckdb_tables() WHERE schema_name = 'curated'")
        certified = _scalar(con, "SELECT count(*) FILTER (WHERE certified) || ' de ' || "
                                 "count(*) FROM meta.catalog_tables WHERE layer = 'curated'")
        dq_issues = _scalar(con, "SELECT count(*) FROM meta.dq_issues WHERE status = 'abierta'")

    by_standard: dict[str, list] = defaultdict(list)
    for f in findings:
        by_standard[f.standard].append(f)
    counts = Counter(f.standard for f in findings)
    retired = set(arch.to_be.retired)
    kept = [f for f in arch.as_is.flows if not {f.from_, f.to} & retired]
    sql_reviews = [(Path(k).relative_to(ROOT).as_posix(), v) for k, v in reviews.items()]
    compliant = sum(1 for s in linter.std.standards if not counts.get(s.id))
    pii_tables = sorted(set().union(*linter.pii_places.values()))
    measures = [
        ("Estándares que cumple el warehouse",
         f"{compliant} de {len(linter.std.standards)}"),
        ("Seguridad y cumplimiento: tablas con datos personales fuera de raw",
         f"{len(pii_tables)} ({', '.join(pii_tables)})" if pii_tables else "0"),
        ("Simplificación: almacenes de datos", f"{len(stores)} hoy → {len(stores - retired)}"),
        ("Simplificación: flujos punto a punto", f"{len(arch.as_is.flows)} hoy → {len(kept)}"),
        ("Accesibilidad: puntos de provisión autorizados (curated certificados, capítulo 8)",
         certified or "sin medir (ejecuta el capítulo 8)"),
        ("Metadatos: tablas curated documentadas (capítulo 6)",
         fmt_pct(documented) if documented is not None else "sin medir"),
        ("Calidad: incidencias abiertas (capítulo 8)",
         str(dq_issues) if dq_issues is not None else "sin medir (ejecuta el capítulo 8)"),
        ("Programa: principios definidos y to-be en borrador",
         f"{len(arch.principles)} principios · to-be de {len(arch.to_be.layers)} capas"),
    ]

    outputs = {"architecture": write_text(out_dir / "data_architecture.md", render_template(
        TEMPLATES, "data_architecture.md.j2", company=COMPANY, as_is=arch.as_is,
        to_be=arch.to_be, retired=sorted(retired),
        retired_names=[s.name for s in arch.as_is.stores if s.id in retired],
        pii_flows=sum(f.pii for f in arch.as_is.flows),
        manual_flows=sum(f.manual for f in arch.as_is.flows),
        to_be_stores=len(stores - retired), to_be_flows=len(kept),
        to_be_manual=sum(f.manual for f in kept), to_be_pii=sum(f.pii for f in kept),
        principles=arch.principles, standards=linter.std.standards, counts=counts,
        by_standard=by_standard, sql_reviews=sql_reviews, program=arch.program,
        roadmap=arch.roadmap, measures=measures))}

    console.rule("[bold]Capítulo 9: Arquitectura de datos")
    console.print(f"As-is: {len(stores)} almacenes y {len(arch.as_is.flows)} flujos "
                  f"({sum(f.manual for f in arch.as_is.flows)} manuales) → to-be: "
                  f"{len(stores - retired)} almacenes y {len(kept)} flujos")
    console.print(f"Warehouse: cumple {compliant} de {len(linter.std.standards)} estándares")
    for sid, n in sorted(counts.items()):
        console.print(f"  [yellow]{sid}[/yellow]: {n} incumplimientos")
    for file, fs in sql_reviews:
        mark = "[green]✓[/green]" if not fs else f"[red]✗ {len(fs)}[/red]"
        console.print(f"Revisión SQL {mark} {file}")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

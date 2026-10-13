"""Revisión de arquitectura de un cambio SQL antes de incorporarlo (puerta del SDLC).

Uso:
    uv run python -m chapters.ch09_arquitectura_datos.review \
        chapters/ch09_arquitectura_datos/inputs/proposals/20_curated_customer_report.sql

Devuelve código de salida 1 si el cambio incumple algún estándar, así que puede usarse
como comprobación automática antes de aceptar un cambio.
"""

from pathlib import Path

import typer
from rich.console import Console

from chapters.ch06_gestion_metadatos.classify import ClassificationPolicy
from dglab.config import load_yaml
from dglab.paths import WAREHOUSE_DB
from dglab.warehouse import connect

from .lint import Linter, StandardsInput, lint_files

CHAPTER_DIR = Path(__file__).parent
CH06_POLICY = CHAPTER_DIR.parent / "ch06_gestion_metadatos" / "inputs" / "classification.yaml"
app = typer.Typer(add_completion=False)


def make_linter() -> Linter:
    std = StandardsInput.model_validate(load_yaml(CHAPTER_DIR / "inputs" / "standards.yaml"))
    return Linter(std, ClassificationPolicy.model_validate(load_yaml(CH06_POLICY)))


@app.command()
def main(files: list[Path] = typer.Argument(..., help="Ficheros SQL a revisar."),
         db: Path = typer.Option(WAREHOUSE_DB, help="Warehouse con el esquema actual.")) -> None:
    console = Console()
    linter = make_linter()
    texts = {s.id: s.text for s in linter.std.standards}
    with connect(db, read_only=True) as con:
        results = lint_files(linter, con, files)
    failed = False
    for file, findings in results.items():
        if not findings:
            console.print(f"[green]✓ {file}: cumple los estándares[/green]")
            continue
        failed = True
        console.print(f"[red]✗ {file}: {len(findings)} incumplimientos[/red]")
        for f in findings:
            console.print(f"  [bold]{f.standard}[/bold] {texts[f.standard]}\n    → {f.message}")
    raise typer.Exit(1 if failed else 0)


if __name__ == "__main__":
    app()

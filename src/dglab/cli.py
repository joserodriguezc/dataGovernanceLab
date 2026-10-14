"""CLI del laboratorio: generar los datos sintéticos y construir el warehouse.

Uso:
    uv run dglab build          # generar + cargar
    uv run dglab generate --seed 7 --persons 500
    uv run dglab load
    uv run dglab reset
    uv run dglab run-all        # warehouse + capítulos 1 a 17 en orden
    uv run dglab run-all --start 6 --no-build
"""

import importlib
import sys
import time

import typer
from rich.console import Console
from rich.table import Table

from dglab.paths import RAW_DIR, ROOT, WAREHOUSE_DB
from dglab.synthetic import DEFAULT_SEED, Scale, SyntheticConfig, generate, write_dataset
from dglab.warehouse import build_warehouse

app = typer.Typer(help="Data Governance Lab: datos sintéticos de NovaMercado.",
                  no_args_is_help=True)
console = Console()


@app.command("generate")
def generate_cmd(seed: int = typer.Option(DEFAULT_SEED, help="Semilla del generador."),
                 persons: int = typer.Option(Scale.persons, help="Clientes reales.")) -> None:
    """Genera los CSV raw y el solucionario en data/raw."""
    ds = generate(SyntheticConfig(seed=seed, scale=Scale(persons=persons)))
    write_dataset(ds)
    table = Table("Tabla raw", "Filas", title=f"Datos generados (semilla {seed})")
    for name, df in ds.tables.items():
        table.add_row(name, f"{len(df):,}")
    console.print(table)
    defects = Table("Defecto sembrado", "Registros", title="Solucionario")
    for name, ids in ds.defects.items():
        defects.add_row(name, str(len(ids)))
    console.print(defects)


@app.command("load")
def load_cmd() -> None:
    """Carga data/raw en DuckDB y ejecuta las transformaciones staging y curated."""
    counts = build_warehouse()
    table = Table("Tabla", "Filas", title=f"Warehouse: {WAREHOUSE_DB.name}")
    for name, n in counts.items():
        table.add_row(name, f"{n:,}")
    console.print(table)


@app.command("build")
def build_cmd(seed: int = typer.Option(DEFAULT_SEED, help="Semilla del generador.")) -> None:
    """Genera los datos y construye el warehouse en un paso."""
    generate_cmd(seed=seed, persons=Scale.persons)
    load_cmd()


@app.command("reset")
def reset_cmd() -> None:
    """Borra los CSV generados, el solucionario y el warehouse."""
    removed = [p for p in [*RAW_DIR.glob("*.csv"), *RAW_DIR.glob("_truth/*"), WAREHOUSE_DB]
               if p.exists()]
    for p in removed:
        p.unlink()
    console.print(f"Borrados {len(removed)} ficheros.")


def chapter_modules() -> list[tuple[int, str]]:
    """(número, módulo run) de cada capítulo, en orden."""
    return [(int(p.parent.name[2:4]), f"chapters.{p.parent.name}.run")
            for p in sorted((ROOT / "chapters").glob("ch[0-9][0-9]_*/run.py"))]


@app.command("run-all")
def run_all_cmd(
    start: int = typer.Option(1, help="Primer capítulo que se ejecuta."),
    build: bool = typer.Option(True, help="Generar los datos y construir el warehouse antes."),
    progress: bool = typer.Option(
        True, help="Repetir los capítulos 4 y 5 al final para ver el avance frente a la "
                   "línea base."),
) -> None:
    """Ejecuta el recorrido completo del README: warehouse y capítulos en orden."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    if build:
        build_cmd(seed=DEFAULT_SEED)
    modules = [(n, m) for n, m in chapter_modules() if n >= start]
    if progress and start <= 5:
        modules += [(n, m) for n, m in chapter_modules() if n in (4, 5)]
    summary = Table("Capítulo", "Segundos", "Entregables", title="Recorrido completo")
    for n, module in modules:
        t0 = time.perf_counter()
        try:
            outputs = importlib.import_module(module).main()
        except Exception as exc:
            console.print(summary)
            console.print(f"[red]✗ Falla el capítulo {n} ({module}): {exc}[/red]")
            raise typer.Exit(1) from exc
        summary.add_row(str(n), f"{time.perf_counter() - t0:.1f}", str(len(outputs or {})))
    console.print(summary)


if __name__ == "__main__":
    app()

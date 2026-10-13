"""CLI del laboratorio: generar los datos sintéticos y construir el warehouse.

Uso:
    uv run dglab build          # generar + cargar
    uv run dglab generate --seed 7 --persons 500
    uv run dglab load
    uv run dglab reset
"""

import typer
from rich.console import Console
from rich.table import Table

from dglab.paths import RAW_DIR, WAREHOUSE_DB
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


if __name__ == "__main__":
    app()

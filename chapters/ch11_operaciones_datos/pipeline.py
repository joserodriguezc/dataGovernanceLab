"""Orquestador del pipeline nocturno con registro de ejecuciones y de auditoría.

Ejecuta los capítulos que mantienen el warehouse (carga, golden record, metadatos, linaje y
calidad) en orden de dependencias. Si un paso falla, se reintenta una vez; si vuelve a
fallar, los pasos que dependen de él se omiten. Cada paso queda registrado (quién, cuándo,
cuánto tardó y cómo terminó) en una base de operaciones aparte del warehouse, para que el
historial sobreviva a cada reconstrucción.

Uso: uv run python -m chapters.ch11_operaciones_datos.pipeline
"""

import getpass
import uuid
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import duckdb
import typer
from rich.console import Console

from dglab.paths import OPS_DB, RAW_DIR, WAREHOUSE_DB
from dglab.warehouse import build_warehouse, connect

from .config import OpsConfig, Step

CHAPTERS = Path(__file__).parent.parent
StepFn = Callable[[Path, Path, Path | None], object]


def _chapter(module: str, raw_arg: bool) -> StepFn:
    def run(db: Path, raw: Path, out: Path | None) -> object:
        mod = __import__(f"chapters.{module}.run", fromlist=["main"])
        kwargs = {"db_path": db} | ({"raw_dir": raw} if raw_arg else {})
        if out is not None:
            kwargs["out_dir"] = out / module
        return mod.main(**kwargs)
    return run


STEP_FUNCTIONS: dict[str, StepFn] = {
    "load": lambda db, raw, out: build_warehouse(db, raw),
    "pdm": _chapter("ch10_datos_primarios_mdm", raw_arg=True),
    "metadata": _chapter("ch06_gestion_metadatos", raw_arg=False),
    "lineage": _chapter("ch07_metadatos_tecnicos_linaje", raw_arg=False),
    "quality": _chapter("ch08_calidad_datos", raw_arg=True),
}


def ops_connect(path: Path = OPS_DB) -> duckdb.DuckDBPyConnection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    con.execute("""CREATE TABLE IF NOT EXISTS runs (
        run_id VARCHAR, step VARCHAR, attempt INTEGER, started_at TIMESTAMP,
        finished_at TIMESTAMP, seconds DOUBLE, status VARCHAR, error VARCHAR,
        executed_by VARCHAR)""")
    con.execute("""CREATE TABLE IF NOT EXISTS row_counts (
        run_id VARCHAR, measured_at TIMESTAMP, table_fqn VARCHAR, row_count BIGINT)""")
    return con


def run_pipeline(steps: list[Step], db: Path = WAREHOUSE_DB, raw: Path = RAW_DIR,
                 ops_db: Path = OPS_DB, out: Path | None = None,
                 functions: dict[str, StepFn] | None = None,
                 console: Console | None = None) -> tuple[str, dict[str, str]]:
    """Ejecuta el pipeline y devuelve (run_id, estado de cada paso)."""
    functions = functions or STEP_FUNCTIONS
    console = console or Console(quiet=True)
    run_id = f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
    user = getpass.getuser()
    status: dict[str, str] = {}
    with ops_connect(ops_db) as ops:
        for step in steps:
            if any(status.get(d) != "ok" for d in step.depends_on):
                status[step.id] = "omitido"
                ops.execute("INSERT INTO runs VALUES (?, ?, 0, ?, ?, 0, 'omitido', ?, ?)",
                            [run_id, step.id, datetime.now(), datetime.now(),
                             "depende de un paso que no terminó", user])
                console.print(f"[yellow]⏭ {step.name}: omitido[/yellow]")
                continue
            for attempt in (1, 2):
                started = datetime.now()
                error = None
                try:
                    functions[step.id](db, raw, out)
                    result = "ok"
                except Exception as exc:  # noqa: BLE001 - se registra cualquier fallo
                    result, error = "fallido", f"{type(exc).__name__}: {exc}"[:500]
                finished = datetime.now()
                ops.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                            [run_id, step.id, attempt, started, finished,
                             (finished - started).total_seconds(), result, error, user])
                if result == "ok":
                    break
            status[step.id] = result
            mark = "[green]✓[/green]" if result == "ok" else "[red]✗[/red]"
            console.print(f"{mark} {step.name} ({(finished - started).total_seconds():.1f} s)")
        if status.get("load") == "ok" and db.exists():  # observabilidad de volumen
            with connect(db, read_only=True) as con:
                tables = [r[0] for r in con.execute(
                    "SELECT schema_name || '.' || table_name FROM duckdb_tables() "
                    "WHERE schema_name = 'curated' ORDER BY 1").fetchall()]
                counts = [(t, con.execute(f"SELECT count(*) FROM {t}").fetchone()[0])
                          for t in tables]
            ops.executemany("INSERT INTO row_counts VALUES (?, ?, ?, ?)",
                            [[run_id, datetime.now(), t, n] for t, n in counts])
    return run_id, status


app = typer.Typer(add_completion=False)


@app.command()
def main() -> None:
    """Ejecuta el pipeline nocturno completo sobre el warehouse."""
    from dglab.config import load_yaml

    cfg = OpsConfig.model_validate(load_yaml(Path(__file__).parent / "inputs" /
                                             "operations.yaml"))
    console = Console()
    console.rule("[bold]Pipeline nocturno de NovaMercado")
    run_id, status = run_pipeline(cfg.pipeline, console=console)
    console.print(f"Ejecución {run_id}: " + ", ".join(f"{k} {v}" for k, v in status.items()))
    raise typer.Exit(0 if all(v == "ok" for v in status.values()) else 1)


if __name__ == "__main__":
    app()

"""Búsqueda de un cliente en el hub de datos primarios (golden record, orígenes y atribución).

Uso:
    uv run python -m chapters.ch10_datos_primarios_mdm.lookup "telmo anton"
    uv run python -m chapters.ch10_datos_primarios_mdm.lookup 778606430
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from dglab.paths import WAREHOUSE_DB
from dglab.warehouse import connect

from .parties import name_key

app = typer.Typer(add_completion=False)


@app.command()
def main(text: str = typer.Argument(..., help="Nombre, email, teléfono o golden id."),
         db: Path = typer.Option(WAREHOUSE_DB, help="Ruta del warehouse.")) -> None:
    console = Console()
    key = name_key(text)
    with connect(db, read_only=True) as con:
        rows = con.execute("""
            SELECT * FROM pdm.customer_golden
            WHERE golden_id = ? OR email = lower(?) OR phone = ?
               OR strip_accents(lower(first_name || ' ' || last_name)) LIKE ?
            ORDER BY golden_id LIMIT 5""", [text, text, text, f"%{key}%"]).df()
        if rows.empty:
            console.print(f"[yellow]No hay clientes que coincidan con «{text}».[/yellow]")
            raise typer.Exit(1)
        for _, g in rows.iterrows():
            t = Table("Atributo", "Valor", "Fuente dorada",
                      title=f"{g.golden_id} · {g.first_name} {g.last_name}")
            for attr, src, sid in con.execute(
                    "SELECT attribute, source, source_id FROM pdm.customer_attribution "
                    "WHERE golden_id = ? ORDER BY rowid", [g.golden_id]).fetchall():
                t.add_row(attr, str(g[attr]), f"{src} {sid or ''}".strip())
            console.print(t)
            refs = con.execute("SELECT source || ' ' || source_id FROM pdm.customer_xref "
                               "WHERE golden_id = ? ORDER BY 1", [g.golden_id]).fetchall()
            console.print("Registros de origen: " + ", ".join(r[0] for r in refs) + "\n")


if __name__ == "__main__":
    app()

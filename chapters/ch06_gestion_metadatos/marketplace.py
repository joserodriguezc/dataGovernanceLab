"""Marketplace de datos: búsqueda en el glosario y el catálogo publicados en el warehouse.

Uso:
    uv run python -m chapters.ch06_gestion_metadatos.marketplace "cliente"
    uv run python -m chapters.ch06_gestion_metadatos.marketplace "ventas" --solo-certificados
"""

from pathlib import Path

import duckdb
import typer
from rich.console import Console
from rich.table import Table

from dglab.company import DOMAIN_NAMES
from dglab.paths import WAREHOUSE_DB
from dglab.warehouse import connect

from .glossary import STATUS_LABELS

app = typer.Typer(add_completion=False)


def search(con: duckdb.DuckDBPyConnection, text: str,
           certified_only: bool = False) -> dict[str, list[tuple]]:
    """Busca en términos, sinónimos, definiciones, tablas, etiquetas y columnas."""
    like = f"%{text.lower()}%"
    terms = con.execute("""
        SELECT term, status, definition, business_steward, authorized_source
        FROM meta.glossary
        WHERE lower(term) LIKE ? OR lower(synonyms) LIKE ? OR lower(definition) LIKE ?
        ORDER BY (lower(term) LIKE ?) DESC, term""", [like, like, like, like]).fetchall()
    tables = con.execute(f"""
        SELECT table_fqn, domain, description, business_steward, certified
        FROM meta.catalog_tables
        WHERE layer <> 'raw' {"AND certified" if certified_only else ""}
          AND (lower(table_fqn) LIKE ? OR lower(description) LIKE ? OR lower(tags) LIKE ?)
        ORDER BY table_fqn""", [like, like, like]).fetchall()
    columns = con.execute("""
        SELECT table_fqn || '.' || column_name, business_term, classification_label
        FROM meta.catalog_columns
        WHERE table_fqn NOT LIKE 'raw.%'
          AND (lower(column_name) LIKE ? OR lower(business_term) LIKE ?)
        ORDER BY 1""", [like, like]).fetchall()
    return {"terms": terms, "tables": tables, "columns": columns}


@app.command()
def main(text: str = typer.Argument(..., help="Texto a buscar."),
         solo_certificados: bool = typer.Option(False, help="Solo activos certificados."),
         db: Path = typer.Option(WAREHOUSE_DB, help="Ruta del warehouse.")) -> None:
    console = Console()
    with connect(db, read_only=True) as con:
        found = search(con, text, solo_certificados)

    def short(text: str | None, n: int = 90) -> str:
        return "—" if not text else text if len(text) <= n else text[: n - 1] + "…"

    def show(table: Table, rows: list[tuple]) -> None:
        if rows:
            for row in rows:
                table.add_row(*row)
            console.print(table)
        else:
            console.print(f"[dim]{table.title}: sin resultados.[/dim]")

    show(Table("Término", "Estado", "Definición", "Steward", "Fuente autorizada",
               title=f"Glosario: «{text}»"),
         [(term, STATUS_LABELS[status], short(definition), steward or "—", source or "—")
          for term, status, definition, steward, source in found["terms"]])
    show(Table("Tabla", "Dominio", "Descripción", "Steward", "Certificada", title="Catálogo"),
         [(fqn, DOMAIN_NAMES.get(domain, "—"), short(desc, 70), steward or "—",
           "✅" if cert else "No") for fqn, domain, desc, steward, cert in found["tables"]])
    show(Table("Columna", "Término", "Clasificación", title="Columnas"),
         [tuple(str(v or "—") for v in row) for row in found["columns"][:25]])


if __name__ == "__main__":
    app()

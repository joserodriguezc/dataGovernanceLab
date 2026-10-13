"""Análisis de impacto y origen desde la terminal, sobre el linaje publicado en el warehouse.

Uso:
    uv run python -m chapters.ch07_metadatos_tecnicos_linaje.impact raw.pos_sales.unit_price
    uv run python -m chapters.ch07_metadatos_tecnicos_linaje.impact \
        curated.agg_sales_daily_channel.revenue --origen
"""

from pathlib import Path

import networkx as nx
import typer
from rich.console import Console
from rich.tree import Tree

from dglab.paths import WAREHOUSE_DB
from dglab.warehouse import connect

app = typer.Typer(add_completion=False)


def load_graph(db: Path) -> nx.DiGraph:
    g = nx.DiGraph()
    with connect(db, read_only=True) as con:
        rows = con.execute("""
            SELECT source_table || '.' || source_column, target_table || '.' || target_column,
                   kind, expression
            FROM meta.lineage_edges
            WHERE source_column IS NOT NULL AND target_column IS NOT NULL""").fetchall()
    for source, target, kind, expression in rows:
        g.add_edge(source, target, kind=kind, expression=expression)
    return g


def _tree(g: nx.DiGraph, node: str, label: Tree, upward: bool, seen: set[str]) -> None:
    neighbours = g.predecessors(node) if upward else g.successors(node)
    for n in sorted(neighbours):
        edge = g.edges[n, node] if upward else g.edges[node, n]
        branch = label.add(f"[bold]{n}[/bold]  [dim]{edge['kind']}: {edge['expression']}[/dim]")
        if n not in seen:
            seen.add(n)
            _tree(g, n, branch, upward, seen)


@app.command()
def main(column: str = typer.Argument(..., help="Columna esquema.tabla.columna."),
         origen: bool = typer.Option(False, "--origen", help="Mostrar de dónde viene."),
         db: Path = typer.Option(WAREHOUSE_DB, help="Ruta del warehouse.")) -> None:
    console = Console()
    g = load_graph(db)
    if column not in g:
        console.print(f"[red]{column} no aparece en el linaje.[/red] "
                      "¿Has ejecutado el capítulo 7 después del último `dglab build`?")
        raise typer.Exit(1)
    title = "De dónde viene" if origen else "Qué se ve afectado si cambia"
    tree = Tree(f"[bold]{column}[/bold] · {title}")
    _tree(g, column, tree, origen, set())
    console.print(tree)
    related = nx.ancestors(g, column) if origen else nx.descendants(g, column)
    tables = sorted({n.rsplit(".", 1)[0] for n in related})
    console.print(f"{len(related)} columnas en {len(tables)} tablas: {', '.join(tables) or '—'}")


if __name__ == "__main__":
    app()

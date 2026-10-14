"""Capítulo 16: resultados confiables (revisión de capacidades y comunicación de resultados).

Lee todo lo que han dejado los capítulos anteriores. Para el resultado completo, ejecuta
antes el pipeline del capítulo 11 (warehouse con los capítulos 6, 7, 8 y 10, y registro
de operaciones).
Uso: uv run python -m chapters.ch16_resultados_confiables.run
"""

import base64
from datetime import date
from pathlib import Path

from matplotlib.colors import ListedColormap
from pydantic import BaseModel
from rich.console import Console

from chapters.ch04_linea_base_madurez.evidence import indicators
from chapters.ch05_exito_y_resultados.framework import OutcomeFramework
from chapters.ch12_lanzamiento.messaging import review_memo
from dglab import viz
from dglab.config import load_yaml
from dglab.paths import OPS_DB, ROOT, WAREHOUSE_DB
from dglab.reporting import render_template, write_text
from dglab.warehouse import connect

from .evidence import CHECKS, Context
from .results import STATUS_CLASS, Variance, commitments, status_counts
from .results import STATUS_LABELS as C_LABELS

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
COMPANY = "NovaMercado"
STAGES = ["define", "document", "analyze", "optimize", "sustain"]
STAGE_LABELS = {"define": "Definir", "document": "Documentar", "analyze": "Analizar",
                "optimize": "Optimizar", "sustain": "Sostener y probar"}
STATUS_LABELS = {"done": "✓ Entregado", "partial": "~ Parcial", "missing": "✗ Pendiente"}
STATUS_VALUE = {"missing": 0, "partial": 1, "done": 2}


class Stage(BaseModel):
    deliverable: str
    check: str
    impact: str


class Capability(BaseModel):
    id: str
    name: str
    stages: dict[str, Stage]


class Audience(BaseModel):
    id: str
    name: str
    focus: str


class ReviewInput(BaseModel):
    as_of: date
    capabilities: list[Capability]
    variances: dict[str, Variance]
    audiences: list[Audience]


def plot_matrix(caps: list[dict], path: Path) -> Path:
    grid = [[STATUS_VALUE[s["status"]] for s in c["stages"]] for c in caps]
    cmap = ListedColormap([viz.STATUS["critical"], viz.STATUS["warning"], viz.STATUS["good"]])
    fig, ax = viz.new_figure(9, 0.55 * len(caps) + 1.6)
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.imshow(grid, cmap=cmap, vmin=-0.5, vmax=2.5, aspect="auto")
    marks = {0: "✗", 1: "~", 2: "✓"}
    for i, row in enumerate(grid):
        for j, v in enumerate(row):
            ax.text(j, i, marks[v], ha="center", va="center", fontsize=13,
                    color=viz.TEXT_PRIMARY, fontweight="bold")
    ax.set_xticks(range(len(STAGES)), [STAGE_LABELS[s] for s in STAGES], fontsize=9)
    ax.set_yticks(range(len(caps)), [c["name"] for c in caps], fontsize=9)
    ax.set_xticks([x - 0.5 for x in range(1, len(STAGES))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(caps))], minor=True)
    ax.grid(which="minor", color=viz.SURFACE, linewidth=3)
    ax.tick_params(which="minor", length=0)
    viz.set_titles(ax, "Revisión de capacidades por etapa",
                   "✓ entregado · ~ parcial · ✗ pendiente (según la evidencia)")
    return viz.save_figure(fig, path)


def audience_messages(inp: ReviewInput, items, caps, counts: dict[str, int]) -> list[dict]:
    weak = [(c["name"], STAGE_LABELS[s["key"]], s["deliverable"]) for c in caps
            for s in c["stages"] if s["status"] != "done"]
    variances = [c for c in items if c.needs_message]
    lines = {
        "executives": [
            f"Hemos cumplido {counts['met']} de {len(items)} compromisos de datos. "
            f"En plazo: {counts['on_track']}. Con desvío, causa, plan y fecha: "
            f"{counts['at_risk'] + counts['late']}.",
            "La vista única de cliente ya está en uso y elimina la depuración manual de "
            "clientes repetidos.",
            "La cifra de ventas todavía no es oficial: los precios mal registrados en tienda "
            "lo impiden y su corrección vence en abril.",
        ],
        "managers": [f"{c.name}: {c.variance.plan if c.variance else 'causa raíz pendiente'} "
                     f"({c.variance.owner if c.variance else 'sin responsable'})"
                     for c in variances],
        "stewards": [f"{name} · {stage}: {deliverable}" for name, stage, deliverable in weak[:6]],
    }
    return [{"name": a.name, "focus": a.focus, "lines": lines.get(a.id, [])}
            for a in inp.audiences]


def main(out_dir: Path | None = None, db_path: Path = WAREHOUSE_DB,
         ops_db: Path = OPS_DB) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    if not db_path.exists():
        raise FileNotFoundError(f"No existe {db_path}: ejecuta antes el pipeline del capítulo 11")
    console = Console()
    inp = ReviewInput.model_validate(load_yaml(INPUTS / "review.yaml"))
    fw = OutcomeFramework.model_validate(load_yaml(
        ROOT / "chapters" / "ch05_exito_y_resultados" / "inputs" / "outcomes.yaml"))
    unknown = {st.check for c in inp.capabilities for st in c.stages.values()} - set(CHECKS)
    if unknown:
        raise ValueError(f"comprobaciones sin implementar: {sorted(unknown)}")

    with connect(db_path, read_only=True) as con:
        ctx = Context(con, ops_db)
        caps = [{"name": c.name, "stages": [
            dict(key=k, deliverable=st.deliverable, impact=st.impact,
                 **dict(zip(("status", "evidence"), CHECKS[st.check](ctx), strict=True)))
            for k, st in ((k, c.stages[k]) for k in STAGES)]} for c in inp.capabilities]
        items = commitments(fw, indicators(con), inp.variances)

    counts = status_counts(items)
    msgs = audience_messages(inp, items, caps, counts)
    exec_review = review_memo(" ".join(msgs[0]["lines"]), 500)
    chart = plot_matrix(caps, out_dir / "capability_matrix.png")
    stage_total = sum(len(c["stages"]) for c in caps)
    stage_done = sum(s["status"] == "done" for c in caps for s in c["stages"])
    outputs = {
        "chart": chart,
        "report": write_text(out_dir / "capability_review.html", render_template(
            TEMPLATES, "capability_review.html.j2", company=COMPANY, as_of=inp.as_of,
            caps=caps, stage_labels=STAGE_LABELS, status_labels=STATUS_LABELS, items=items,
            counts=counts, c_labels=C_LABELS, c_class=STATUS_CLASS, stage_done=stage_done,
            stage_total=stage_total, audience_msgs=msgs, exec_review=exec_review,
            chart_b64=base64.b64encode(chart.read_bytes()).decode())),
    }

    console.rule("[bold]Capítulo 16: Resultados confiables")
    console.print(f"Etapas entregadas: {stage_done} de {stage_total}")
    for c in caps:
        marks = " ".join({"done": "✓", "partial": "~", "missing": "✗"}[s["status"]]
                         for s in c["stages"])
        console.print(f"  {marks}  {c['name']}")
    console.print("Compromisos: " + ", ".join(f"{C_LABELS[k]} {v}" for k, v in counts.items()))
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

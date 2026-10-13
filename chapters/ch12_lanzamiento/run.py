"""Capítulo 12: lanzar con fuerza (preparación, mensaje, memo narrativo y plan).

Reutiliza los capítulos 1 a 10: la preparación se calcula con su evidencia y el memo
anuncia las victorias ya entregadas que se miden en el warehouse.
Uso: uv run python -m chapters.ch12_lanzamiento.run
"""

from datetime import date
from pathlib import Path

from pydantic import BaseModel
from rich.console import Console

from chapters.ch01_que_es_gobierno_datos.charter import ProgramInput
from chapters.ch01_que_es_gobierno_datos.equity import DataEquityInput, evaluate_equity
from chapters.ch02_coalicion_defensores.sponsors import SponsorInput, assess_sponsors, recommend
from chapters.ch02_coalicion_defensores.stakeholders import StakeholderInput
from chapters.ch05_exito_y_resultados.framework import OutcomeFramework
from dglab import viz
from dglab.config import load_yaml
from dglab.paths import ROOT, WAREHOUSE_DB
from dglab.reporting import render_template, write_text
from dglab.warehouse import connect

from .messaging import memo_context, review_memo
from .readiness import Dimension, assess, launch_approach, maturity_score

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CHAPTERS = ROOT / "chapters"
CHART_NAME = "launch_readiness.png"
COMPANY = "NovaMercado"


class Leadership(BaseModel):
    funding_approved: bool
    csuite_supporters: list[str]


class LaunchInput(BaseModel):
    launch_date: date
    memo_max_words: int
    leadership: Leadership
    as_is_to_be: list[dict[str, str]]
    audiences: list[dict[str, str]]
    communication: list[dict[str, str]]
    feedback: list[dict[str, str]]
    milestones: list[dict[str, str]]


def plot_readiness(dims: list[Dimension], path: Path) -> Path:
    """Las cinco escalas del capítulo, con la posición actual de cada dimensión."""
    fig, ax = viz.new_figure(9, 0.75 * len(dims) + 1.2)
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ys = range(len(dims))[::-1]
    for y, d in zip(ys, dims, strict=True):
        ax.plot([1, 5], [y, y], color=viz.BASELINE, linewidth=2, zorder=1)
        for tick in (2, 3, 4):
            ax.plot([tick, tick], [y - 0.08, y + 0.08], color=viz.BASELINE, linewidth=1)
        ax.scatter([d.score], [y], marker="*", s=320, color=viz.SERIES[0],
                   edgecolors=viz.SURFACE, linewidths=1.5, zorder=3)
        ax.annotate(f"{d.score:.1f}".replace(".", ","), (d.score, y), xytext=(0, 9),
                    textcoords="offset points", ha="center", fontsize=8,
                    color=viz.TEXT_SECONDARY)
        ax.text(0.9, y, d.left, ha="right", va="center", fontsize=8, color=viz.TEXT_SECONDARY)
        ax.text(5.1, y, d.right, ha="left", va="center", fontsize=8, color=viz.TEXT_SECONDARY)
    ax.set_xlim(-0.6, 6.6)
    ax.set_ylim(-0.6, len(dims) - 0.4)
    ax.set_xticks([])
    ax.set_yticks([])
    viz.set_titles(ax, f"Preparación de {COMPANY} para el lanzamiento",
                   "Cada estrella es la posición actual (1-5) según la evidencia acumulada")
    return viz.save_figure(fig, path)


def main(out_dir: Path | None = None, db_path: Path = WAREHOUSE_DB) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    if not db_path.exists():
        raise FileNotFoundError(f"No existe {db_path}: ejecuta antes `uv run dglab build`")
    console = Console()
    inp = LaunchInput.model_validate(load_yaml(INPUTS / "launch.yaml"))
    program = ProgramInput.model_validate(load_yaml(
        CHAPTERS / "ch01_que_es_gobierno_datos" / "inputs" / "program.yaml"))
    groups = {g.id: g.name for g in StakeholderInput.model_validate(load_yaml(
        CHAPTERS / "ch02_coalicion_defensores" / "inputs" / "stakeholders.yaml")).groups}
    sponsors = recommend(assess_sponsors(SponsorInput.model_validate(load_yaml(
        CHAPTERS / "ch02_coalicion_defensores" / "inputs" / "sponsors.yaml"))))
    equity_lines = {ln.id: ln for ln in evaluate_equity(DataEquityInput.model_validate(load_yaml(
        CHAPTERS / "ch01_que_es_gobierno_datos" / "inputs" / "data_equity.yaml"))).lines}
    outcomes = OutcomeFramework.model_validate(load_yaml(
        CHAPTERS / "ch05_exito_y_resultados" / "inputs" / "outcomes.yaml"))
    outcome_value = {o.id: sum(equity_lines[i].benefit for i in o.equity_lines)
                     for o in outcomes.outcomes}

    with connect(db_path, read_only=True) as con:
        dims = assess(con, inp.leadership.funding_approved, inp.leadership.csuite_supporters)
        context = memo_context(con, maturity_score())

    memo = render_template(TEMPLATES, "narrative_memo.md.j2", company=COMPANY,
                           launch_date=inp.launch_date, outcome_value=outcome_value,
                           milestones=inp.milestones,
                           supporters=inp.leadership.csuite_supporters,
                           sponsor=groups[sponsors[0].candidate.stakeholder] if sponsors
                           else "Falta un", **context)
    review = review_memo(memo, inp.memo_max_words)
    approach = launch_approach(dims)
    outputs = {
        "chart": plot_readiness(dims, out_dir / CHART_NAME),
        "memo": write_text(out_dir / "narrative_memo.md", memo),
        "plan": write_text(out_dir / "launch_plan.md", render_template(
            TEMPLATES, "launch_plan.md.j2", company=COMPANY, dims=dims, approach=approach,
            chart_name=CHART_NAME, vision=program.vision.statement,
            mission=program.program_mission.statement, as_is_to_be=inp.as_is_to_be,
            audiences=inp.audiences, review=review, communication=inp.communication,
            feedback=inp.feedback, milestones=inp.milestones, wins=context["wins"])),
    }

    console.rule("[bold]Capítulo 12: Lanzar con fuerza")
    for d in dims:
        console.print(f"  • {d.right}: {d.score:.1f}/5 ({'; '.join(d.evidence)})")
    for a in approach:
        console.print(f"[yellow]Enfoque:[/yellow] {a}")
    console.print(f"Memo: {review.words} palabras, jerga: "
                  f"{review.jargon or 'ninguna'} · {len(context['wins'])} victorias ya entregadas")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

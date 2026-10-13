"""Capítulo 4: línea base de madurez de gestión de datos (los 10 pasos).

Requiere el warehouse de la Fase 0: `uv run dglab build`.
Uso: uv run python -m chapters.ch04_linea_base_madurez.run
"""

from datetime import timedelta
from pathlib import Path

from rich.console import Console

from chapters.ch03_equipo_alto_rendimiento.team import TeamInput
from dglab import viz
from dglab.company import DOMAIN_NAMES
from dglab.config import load_yaml
from dglab.dates import add_months
from dglab.paths import WAREHOUSE_DB
from dglab.reporting import render_template, write_text
from dglab.warehouse import connect

from .analysis import (
    company_score,
    dimension_scores,
    group_themes,
    self_assessment_bias,
    unit_scores,
    unsupported_scores,
)
from .evidence import dq_checks, evidence_caps, indicators
from .model import DATA_OFFICE, AssessmentInput, MaturityModel
from .survey import participants, simulate_responses

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CH03_INPUTS = CHAPTER_DIR.parent / "ch03_equipo_alto_rendimiento" / "inputs"
CHART_NAME = "maturity_by_dimension.png"
COMPANY = "NovaMercado"
UNIT_NAMES = {**DOMAIN_NAMES, DATA_OFFICE: "Oficina de datos"}
SCOPE_LABELS = {"enterprise": "toda la empresa", "pilot": "piloto con un dominio",
                "rolling": "por oleadas de dominios"}


def plot_maturity(scores: dict[str, float], target: int, caps: dict[str, int],
                  names: dict[str, str], max_level: int, path: Path) -> Path:
    """Puntos: nivel actual y objetivo por dimensión; marca el máximo que respalda la evidencia."""
    order = sorted(scores, key=scores.get)
    fig, ax = viz.new_figure(9, 5)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=viz.GRIDLINE, linewidth=0.8)
    ys = range(len(order))
    for y, dim in zip(ys, order, strict=True):
        ax.plot([scores[dim], target], [y, y], color=viz.BASELINE, linewidth=2, zorder=1)
    ax.scatter([target] * len(order), ys, s=80, facecolors=viz.SURFACE,
               edgecolors=viz.TEXT_MUTED, linewidths=2, zorder=2,
               label=f"Objetivo (nivel {target})")
    capped = [(y, caps[d]) for y, d in zip(ys, order, strict=True) if d in caps]
    if capped:
        ax.scatter([c for _, c in capped], [y for y, _ in capped], marker="|", s=260,
                   color=viz.STATUS["critical"], linewidths=2, zorder=2,
                   label="Máximo que respalda la evidencia")
    ax.scatter([scores[d] for d in order], ys, s=80, color=viz.SERIES[0],
               edgecolors=viz.SURFACE, linewidths=2, zorder=3, label="Línea base")
    for y, dim in zip(ys, order, strict=True):
        ax.annotate(f"{scores[dim]:.1f}".replace(".", ","), (scores[dim], y), xytext=(0, 10),
                    textcoords="offset points", ha="center", fontsize=8,
                    color=viz.TEXT_SECONDARY)
    ax.set_yticks(list(ys), [names[d] for d in order])
    ax.set_xlim(0.8, max_level + 0.2)
    ax.set_xticks(range(1, max_level + 1))
    ax.set_xlabel("Nivel de madurez", color=viz.TEXT_SECONDARY)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.45, -0.13), ncol=3,
              labelcolor=viz.TEXT_SECONDARY)
    viz.set_titles(ax, f"Madurez de gestión de datos de {COMPANY} por dimensión",
                   "Media de los talleres de todas las unidades")
    return viz.save_figure(fig, path)


def main(out_dir: Path | None = None, db_path: Path = WAREHOUSE_DB) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    if not db_path.exists():
        raise FileNotFoundError(f"No existe {db_path}: ejecuta antes `uv run dglab build`")
    console = Console()

    model = MaturityModel.model_validate(load_yaml(INPUTS / "maturity_model.yaml"))
    inp = AssessmentInput.model_validate(load_yaml(INPUTS / "assessment.yaml"))
    inp.check_against(model)
    team = TeamInput.model_validate(load_yaml(CH03_INPUTS / "team.yaml"))
    dim_names = {d.id: d.name for d in model.dimensions}

    def level_name(score: float) -> str:
        return model.levels[max(model.min_level, min(model.max_level, int(score)))].name

    # [#2] y [#4] Participantes y respuestas
    people = participants(inp, team.functional_roles)
    responses = simulate_responses(inp, model, people)

    # [#5] Análisis
    scores = dimension_scores(responses)
    with connect(db_path, read_only=True) as con:
        ind = indicators(con)
        checks = dq_checks(con)
    caps = evidence_caps(ind)
    flags = unsupported_scores(scores, caps)
    biases = self_assessment_bias(responses, inp.bias_threshold)
    themes = group_themes(inp.findings)
    matrix = unit_scores(responses)
    matrix["_mean"] = matrix.mean(axis=1)

    # Calendario
    phases, start = [], inp.start_date
    for p in inp.phases:
        phases.append((p, start))
        start += timedelta(weeks=p.weeks or 0)
    next_assessment = add_months(inp.start_date, inp.reassessment.frequency_months)
    covered = {p.theme for p in inp.plan}
    uncovered = [t.name for t in themes if t.priority == 1 and t.name not in covered]

    ordered = sorted(scores.items(), key=lambda kv: kv[1])
    cap_by_dim = {c.dimension: c for c in caps}
    common = {"company": COMPANY, "year": inp.assessment_year, "dim_names": dim_names}
    outputs = {
        "responses": out_dir / "responses.csv",
        "chart": plot_maturity(dict(scores), inp.target_level,
                               {c.dimension: c.max_level for c in caps}, dim_names,
                               model.max_level, out_dir / CHART_NAME),
        "plan": write_text(out_dir / "assessment_plan.md", render_template(
            TEMPLATES, "assessment_plan.md.j2", company=COMPANY, inp=inp, model=model,
            people=people, phases=phases, unit_names=UNIT_NAMES, domain_names=DOMAIN_NAMES,
            scope_labels=SCOPE_LABELS)),
        "report": write_text(out_dir / "maturity_report.md", render_template(
            TEMPLATES, "maturity_report.md.j2", **common, company_score=company_score(responses),
            max_level=model.max_level, target=inp.target_level, levels=model.levels,
            level_name=level_name, scores=ordered, caps=cap_by_dim,
            flagged={f.cap.dimension for f in flags}, flags=flags, themes=themes,
            plan=inp.plan, chart_name=CHART_NAME)),
        "internal": write_text(out_dir / "maturity_internal.md", render_template(
            TEMPLATES, "maturity_internal.md.j2", **common, communication=inp.communication,
            dims=[d.id for d in model.dimensions],
            dim_short={d.id: d.short for d in model.dimensions},
            matrix=[(u, matrix.loc[u]) for u in inp.scope.units], unit_names=UNIT_NAMES,
            biases=biases, threshold=inp.bias_threshold,
            participation=[(u, sum(p.unit == u for p in people),
                            int((responses.unit == u).sum())) for u in inp.scope.units])),
        "improvement": write_text(out_dir / "improvement_plan.md", render_template(
            TEMPLATES, "improvement_plan.md.j2", **common, plan=inp.plan,
            total_funding=sum(p.funding_usd for p in inp.plan), uncovered=uncovered,
            indicators=ind, dq_checks=checks, next_assessment=next_assessment,
            reassessment=inp.reassessment, success=inp.success_measures)),
    }
    responses.to_csv(outputs["responses"], index=False, encoding="utf-8")

    console.rule("[bold]Capítulo 4: Línea base de madurez")
    console.print(f"Madurez de la empresa: [bold]{company_score(responses):.2f}[/bold] sobre "
                  f"{model.max_level} ({len(people)} participantes, {len(responses)} respuestas)")
    for dim, score in ordered:
        console.print(f"  • {dim_names[dim]}: {score:.2f}")
    for p in people:
        if p.fallback:
            console.print(f"[yellow]Sin stewards en {UNIT_NAMES[p.unit]}:[/yellow] "
                          f"se entrevista a {p.name}")
    for b in biases:
        console.print(f"[yellow]Sesgo:[/yellow] {UNIT_NAMES[b.unit]} {b.direction} "
                      f"({b.gap:+.2f})")
    for f in flags:
        console.print(f"[yellow]Sin respaldo de la evidencia:[/yellow] "
                      f"{dim_names[f.cap.dimension]} {f.score:.2f} > {f.cap.max_level}")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

"""Capítulo 3: modelo organizativo, equipo, RACI y ritmo del negocio de datos.

Uso: uv run python -m chapters.ch03_equipo_alto_rendimiento.run
"""

from collections import defaultdict
from pathlib import Path

from matplotlib.colors import BoundaryNorm, ListedColormap
from rich.console import Console

from chapters.ch01_que_es_gobierno_datos.business_case import BusinessCaseInput
from chapters.ch01_que_es_gobierno_datos.scorecard import ScorecardInput
from dglab import viz
from dglab.company import DOMAIN_NAMES
from dglab.config import load_yaml
from dglab.reporting import fmt_money, render_template, write_text

from .org_model import (
    MODEL_LABELS,
    RESPONSIBILITIES,
    RESPONSIBILITY_MATRIX,
    OrgContext,
    recommend_model,
)
from .raci import RaciInput, idle_roles, raci_table, write_csv
from .rhythm import ForumsInput, build_calendar, forum_issues, portfolio_without_outcome
from .team import (
    FUNCTION_LABELS,
    MAX_LEVEL,
    STATUS_LABELS,
    Skills,
    TeamInput,
    hiring_order_issues,
    org_chart_mermaid,
    skill_gaps,
    team_cost,
)

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CH01_INPUTS = CHAPTER_DIR.parent / "ch01_que_es_gobierno_datos" / "inputs"
CHART_NAME = "skills_heatmap.png"
COMPANY = "NovaMercado"

FACT_LABELS = {
    "has_data_capabilities": "Existen requisitos o capacidades de datos",
    "capabilities_consistent": "Las capacidades se implementan de forma consistente",
    "major_trust_issues": "Hay problemas graves de calidad, uso o confianza",
    "broad_support": "Hay apoyo general a la iniciativa de datos",
    "strong_bu_leaders": "Hay líderes de datos fuertes en las áreas",
    "central_office_strong": "La oficina del CDO es sólida y está bien financiada",
}
AI_STATUS = {"open": "🔴 Abierta", "in_progress": "🟡 En curso", "answered": "🟢 Respondida"}
LEVEL_LABELS = {"c_suite": "comité de dirección", "c_minus_1_2": "1-2 niveles por debajo",
                "team": "equipo del CDAO", "mixed": "mixto"}
TYPE_LABELS = {"program": "Programa", "project": "Proyecto", "bau": "Recurrente"}
RAG_LABELS = {"green": "🟢 En plazo", "yellow": "🟡 En riesgo", "red": "🔴 Bloqueado"}
MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre"]


def plot_skills(skills: Skills, path: Path) -> Path:
    """Mapa de calor del nivel de cada persona en cada habilidad (rampa secuencial)."""
    names = [m.name for m in skills.members]
    cols = list(skills.required)
    grid = [[m.levels[s] for s in cols] for m in skills.members]
    cmap = ListedColormap(viz.SEQUENTIAL_BLUE)
    norm = BoundaryNorm([x - 0.5 for x in range(MAX_LEVEL + 2)], cmap.N)
    fig, ax = viz.new_figure(11, 4.8)
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.imshow(grid, cmap=cmap, norm=norm, aspect="auto")
    for i, row in enumerate(grid):
        for j, value in enumerate(row):
            ink = viz.TEXT_PRIMARY if value <= 1 else viz.SURFACE
            ax.text(j, i, str(value), ha="center", va="center", fontsize=10, color=ink)
    ax.set_xticks(range(len(cols)),
                  [f"{c} (obj. {skills.required[c]})" for c in cols], fontsize=8,
                  rotation=30, ha="right", rotation_mode="anchor")
    ax.set_yticks(range(len(names)), names, fontsize=9)
    ax.set_xticks([x - 0.5 for x in range(1, len(cols))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(names))], minor=True)
    ax.grid(which="minor", color=viz.SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0)
    viz.set_titles(ax, "Nivel de habilidades del equipo de datos (0-4)",
                   "Más oscuro = más nivel · entre paréntesis, el nivel objetivo")
    return viz.save_figure(fig, path)


def main(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    console = Console()

    ctx = OrgContext.model_validate(load_yaml(INPUTS / "org_context.yaml"))
    team = TeamInput.model_validate(load_yaml(INPUTS / "team.yaml"))
    raci = RaciInput.model_validate(load_yaml(INPUTS / "raci.yaml"))
    forums = ForumsInput.model_validate(load_yaml(INPUTS / "forums.yaml"))
    ch1_scorecard = ScorecardInput.model_validate(load_yaml(CH01_INPUTS / "scorecard.yaml"))
    ch1_case = BusinessCaseInput.model_validate(load_yaml(CH01_INPUTS / "business_case.yaml"))

    # Modelo organizativo
    rec = recommend_model(ctx.org_facts)

    # Equipo
    cost = team_cost(team.roles)
    option = next(o for o in ch1_case.options if o.id == ch1_case.recommended_option)
    annual_budget = option.build_cost_usd / option.duration_months * 12
    hiring_issues = hiring_order_issues(team.roles)
    ch1_execs = {d.id: d.executive for d in ch1_scorecard.domains}
    exec_diffs = [
        f"{DOMAIN_NAMES[f.domain]}: el capítulo 1 tiene "
        f"«{ch1_execs.get(f.domain) or 'sin ejecutivo'}» y aquí se propone «{f.executive}»."
        for f in team.functional_roles if ch1_execs.get(f.domain) != f.executive
    ]
    gaps = skill_gaps(team.skills)

    # Ritmo
    names = {f.id: f.name for f in forums.forums}
    by_month: dict[tuple[int, int], dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for d, f in build_calendar(forums):
        by_month[(d.year, d.month)][f.id].append(d.strftime("%d"))
    months = [(f"{MONTHS[m - 1].capitalize()} {y}", dict(v)) for (y, m), v in sorted(
        by_month.items())]
    no_outcome = portfolio_without_outcome(forums.portfolio)

    outputs = {
        "chart": plot_skills(team.skills, out_dir / CHART_NAME),
        "org_model": write_text(out_dir / "org_model.md", render_template(
            TEMPLATES, "org_model.md.j2", company=COMPANY, ctx=ctx, rec=rec,
            model_labels=MODEL_LABELS, responsibilities=RESPONSIBILITIES,
            matrix=RESPONSIBILITY_MATRIX, ai_status=AI_STATUS,
            facts=[(FACT_LABELS[k], v) for k, v in ctx.org_facts.model_dump().items()])),
        "team": write_text(out_dir / "team_design.md", render_template(
            TEMPLATES, "team_design.md.j2", company=COMPANY,
            org_chart=org_chart_mermaid(team.roles), roles=team.roles,
            function_labels=FUNCTION_LABELS, status_labels=STATUS_LABELS, cost=cost,
            annual_budget=annual_budget, budget_option=option.name.lower(),
            hiring_issues=hiring_issues, functional=team.functional_roles,
            domain_names=DOMAIN_NAMES, exec_diffs=exec_diffs, gaps=gaps,
            chart_name=CHART_NAME, talent=team.talent_plan)),
        "raci_csv": write_csv(raci, out_dir / "raci.csv"),
        "raci": write_text(out_dir / "raci.md", render_template(
            TEMPLATES, "raci.md.j2", company=COMPANY, roles=raci.roles,
            rows=raci_table(raci), idle=idle_roles(raci))),
        "rhythm": write_text(out_dir / "governance_rhythm.md", render_template(
            TEMPLATES, "governance_rhythm.md.j2", company=COMPANY, forums=forums.forums,
            issues=forum_issues(forums), names=names, level_labels=LEVEL_LABELS,
            calendar_label=f"{forums.calendar.start.year}", months=months,
            portfolio=forums.portfolio, type_labels=TYPE_LABELS, status_labels=RAG_LABELS,
            no_outcome=no_outcome)),
    }

    console.rule("[bold]Capítulo 3: Construir un equipo de alto rendimiento")
    target = f" → {MODEL_LABELS[rec.target]}" if rec.target != rec.model else ""
    console.print(f"Modelo: [bold]{MODEL_LABELS[rec.model]}[/bold] ({rec.horizon}){target}")
    new_cost = cost["open"] + cost["planned"]
    console.print(f"Posiciones nuevas: {fmt_money(new_cost)}/año frente a un presupuesto de "
                  f"{fmt_money(annual_budget)}/año (capítulo 1)")
    for issue in hiring_issues + exec_diffs:
        console.print(f"[yellow]Aviso:[/yellow] {issue}")
    for f in team.functional_roles:
        if f.gaps:
            console.print(f"[yellow]{DOMAIN_NAMES[f.domain]} sin:[/yellow] {', '.join(f.gaps)}")
    for g in gaps:
        if g.action != "Cubierta":
            console.print(f"[yellow]Habilidad:[/yellow] {g.skill}: {g.action.lower()}")
    for i in no_outcome:
        console.print(f"[yellow]Portfolio sin resultado para el stakeholder:[/yellow] {i.name}")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

"""Capítulo 1: charter, data equity, caso de negocio, política y EDG Scorecard.

Uso: uv run python -m chapters.ch01_que_es_gobierno_datos.run
"""

from pathlib import Path

from rich.console import Console

from dglab import viz
from dglab.company import DOMAIN_NAMES
from dglab.config import load_yaml
from dglab.reporting import fmt_eur, render_template, write_text

from .business_case import BusinessCaseInput, OptionResult, evaluate_business_case
from .charter import ProgramInput, assess_launch, lint_vision
from .equity import DataEquityInput, evaluate_equity
from .policy import POLICY_SECTIONS, PolicyInput
from .scorecard import ScorecardInput, corporate_scorecard, domain_scorecard

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CHART_NAME = "business_case_cashflow.png"


def plot_cashflow(results: list[OptionResult], recommended: str, path: Path) -> Path:
    """Flujo de caja neto acumulado de cada opción, con su mes de payback marcado."""
    fig, ax = viz.new_figure()
    ax.axhline(0, color=viz.BASELINE, linewidth=1)
    for color, r in zip(viz.SERIES, results, strict=False):
        months = range(1, len(r.cumulative) + 1)
        values = [v / 1e6 for v in r.cumulative]
        width = 2.5 if r.option.id == recommended else 2
        ax.plot(months, values, color=color, linewidth=width, label=r.option.name)
        if r.payback_month:
            ax.scatter([r.payback_month], [values[r.payback_month - 1]], s=64, color=color,
                       edgecolors=viz.SURFACE, linewidths=2, zorder=3)
        ax.annotate(r.option.name, (months[-1], values[-1]), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=9,
                    color=viz.TEXT_SECONDARY)
    ax.set_xlabel("Mes", color=viz.TEXT_SECONDARY)
    ax.set_ylabel("Millones de €", color=viz.TEXT_SECONDARY)
    ax.legend(frameon=False, loc="upper left", labelcolor=viz.TEXT_SECONDARY)
    viz.set_titles(ax, "Flujo de caja neto acumulado por opción",
                   "Beneficios validados por el negocio · el punto marca el mes de payback")
    return viz.save_figure(fig, path)


def main(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    console = Console()

    program = ProgramInput.model_validate(load_yaml(INPUTS / "program.yaml"))
    equity_in = DataEquityInput.model_validate(load_yaml(INPUTS / "data_equity.yaml"))
    bc = BusinessCaseInput.model_validate(load_yaml(INPUTS / "business_case.yaml"))
    policy = PolicyInput.model_validate(load_yaml(INPUTS / "policy.yaml"))
    sc = ScorecardInput.model_validate(load_yaml(INPUTS / "scorecard.yaml"))

    # Data equity y caso de negocio
    equity = evaluate_equity(equity_in)
    annual_benefit = equity.annual_benefit(vetted_only=not bc.include_unvetted_benefits)
    results = evaluate_business_case(bc, annual_benefit)
    recommended = next(r for r in results if r.option.id == bc.recommended_option)
    top_lines = sorted(equity.lines, key=lambda ln: ln.benefit, reverse=True)[:5]

    # Charter
    vision_issues = lint_vision(program.vision.statement)
    launch = assess_launch(program.launch)

    # Scorecard
    corporate = corporate_scorecard(sc)
    domains = [
        {"name": DOMAIN_NAMES[d.id], "executive": d.executive, "stewards": d.stewards,
         "metrics": domain_scorecard(sc, d)}
        for d in sc.domains
    ]

    outputs = {
        "charter": write_text(out_dir / "charter.md", render_template(
            TEMPLATES, "charter.md.j2", company=program.company, vision=program.vision,
            vision_issues=vision_issues, cdao_mission=program.cdao_mission,
            cdao_principles=program.cdao_principles,
            program_mission=program.program_mission.statement, launch=launch,
            drivers=program.launch.drivers, warning_signs=program.launch.warning_signs,
            glossary=program.glossary)),
        "data_equity": write_text(out_dir / "data_equity.md", render_template(
            TEMPLATES, "data_equity.md.j2", company=program.company, s=equity,
            hourly_rate=equity_in.hourly_rate_eur, domain_names=DOMAIN_NAMES)),
        "chart": plot_cashflow(results, bc.recommended_option, out_dir / CHART_NAME),
        "business_case": write_text(out_dir / "business_case.md", render_template(
            TEMPLATES, "business_case.md.j2", bc=bc, results=results, rec=recommended,
            annual_benefit=annual_benefit, top_lines=top_lines, chart_name=CHART_NAME)),
        "policy": write_text(out_dir / "data_governance_policy.md", render_template(
            TEMPLATES, "policy.md.j2", p=policy, sections=POLICY_SECTIONS,
            glossary=program.glossary)),
        "scorecard": write_text(out_dir / "edg_scorecard.md", render_template(
            TEMPLATES, "edg_scorecard.md.j2", company=program.company, as_of=sc.as_of,
            at_risk_days=sc.at_risk_days, corporate=corporate, updates=sc.updates,
            domains=domains)),
    }

    console.rule("[bold]Capítulo 1: ¿Qué es el gobierno de datos?")
    console.print(f"Data equity actual: {fmt_eur(equity.equity('current'))} → "
                  f"objetivo: {fmt_eur(equity.equity('target'))}")
    console.print(f"Beneficio anual usado en el caso de negocio: {fmt_eur(annual_benefit)}")
    for r in results:
        payback = f"mes {r.payback_month}" if r.payback_month else "fuera del horizonte"
        console.print(f"  • {r.option.name}: VAN {fmt_eur(r.npv)}, payback {payback}")
    console.print(f"Lanzamiento: [bold]{launch.verdict.upper()}[/bold]. {launch.rationale}")
    if vision_issues:
        console.print("[yellow]Visión a revisar:[/yellow] " + " ".join(vision_issues))
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

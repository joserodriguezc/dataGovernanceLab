"""Capítulo 2: stakeholders, sponsor ejecutivo y plan de coalición.

Uso: uv run python -m chapters.ch02_coalicion_defensores.run
"""

from collections import defaultdict
from pathlib import Path

from rich.console import Console

from dglab import viz
from dglab.company import DOMAIN_NAMES
from dglab.config import load_yaml
from dglab.reporting import render_template, write_text

from .feedback import CoalitionInput, detect_signals
from .sponsors import CRITERIA, SponsorInput, assess_sponsors, pilot_mismatch, recommend
from .stakeholders import (
    DIRECTION_LABELS,
    HEALTH_LABELS,
    HIGH,
    LEVEL_LABELS,
    StakeholderGroup,
    StakeholderInput,
    listening_coverage,
    listening_gaps,
    vanity_groups,
)

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CHART_NAME = "stakeholder_matrix.png"
COMPANY = "NovaMercado"

# Salud de la relación: color de estado + forma, para no depender solo del color.
HEALTH_STYLE = {
    "positive": (viz.STATUS["good"], "o", "Relación positiva"),
    "neutral": (viz.TEXT_MUTED, "s", "Relación neutral"),
    "negative": (viz.STATUS["critical"], "^", "Relación negativa"),
}
ATTENDANCE_LABELS = {"present": "✅", "delegated": "↘️ delegó", "absent": "❌"}
SIGNAL_LABELS = {
    "membership_shift": "Cambio de membresía",
    "off_cycle": "Peticiones fuera de ciclo",
    "silence": "Silencio",
}


def _spread(groups: list[StakeholderGroup]) -> dict[str, tuple[float, float]]:
    """Separa los puntos que comparten celda para que no se tapen."""
    cells: dict[tuple[int, int], list[str]] = defaultdict(list)
    for g in groups:
        cells[(g.interest, g.influence)].append(g.id)
    offsets = [(0, 0), (0, -0.28), (0, 0.28), (0, -0.56), (0, 0.56)]
    positions = {}
    for (x, y), ids in cells.items():
        for i, gid in enumerate(ids):
            dx, dy = offsets[i % len(offsets)]
            positions[gid] = (x + dx, y + dy)
    return positions


def plot_matrix(groups: list[StakeholderGroup], path: Path) -> Path:
    fig, ax = viz.new_figure(10, 7.5)
    ax.grid(False)
    ax.axvline(HIGH + 0.5, color=viz.BASELINE, linewidth=1)
    ax.axhline(HIGH + 0.5, color=viz.BASELINE, linewidth=1)
    for x, y, label in [(1, 5.75, "Mantener satisfecho"), (4, 5.75, "Gestionar de cerca"),
                        (1, 0.35, "Monitorizar"), (4, 0.35, "Mantener informado")]:
        ax.text(x, y, label, fontsize=9, color=viz.TEXT_MUTED, ha="left", va="center")
    positions = _spread(groups)
    for health, (color, marker, label) in HEALTH_STYLE.items():
        members = [g for g in groups if g.health == health]
        if not members:
            continue
        xs, ys = zip(*(positions[g.id] for g in members), strict=True)
        ax.scatter(xs, ys, s=70, color=color, marker=marker, edgecolors=viz.SURFACE,
                   linewidths=2, zorder=3, label=label)
        for g, x, y in zip(members, xs, ys, strict=True):
            ax.annotate(g.short, (x, y), xytext=(8, 0), textcoords="offset points",
                        va="center", fontsize=8, color=viz.TEXT_SECONDARY, zorder=4,
                        bbox={"facecolor": viz.SURFACE, "edgecolor": "none", "pad": 0.5})
    ax.set_xlim(0.5, 6.2)
    ax.set_ylim(0.1, 6)
    ax.set_xticks(range(1, 6))
    ax.set_yticks(range(1, 6))
    ax.set_xlabel("Interés en el programa (1-5)", color=viz.TEXT_SECONDARY)
    ax.set_ylabel("Influencia (1-5)", color=viz.TEXT_SECONDARY)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3,
              labelcolor=viz.TEXT_SECONDARY)
    viz.set_titles(ax, f"Stakeholders de {COMPANY}: influencia e interés",
                   "Color y forma indican la salud de la relación")
    return viz.save_figure(fig, path)


def main(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    console = Console()

    sh = StakeholderInput.model_validate(load_yaml(INPUTS / "stakeholders.yaml"))
    sp = SponsorInput.model_validate(load_yaml(INPUTS / "sponsors.yaml"))
    co = CoalitionInput.model_validate(load_yaml(INPUTS / "coalition.yaml"))

    names = {g.id: g.name for g in sh.groups}
    unknown = [c.stakeholder for c in sp.candidates if c.stakeholder not in names]
    if unknown:
        raise ValueError(f"candidatos a sponsor que no están en el registro: {unknown}")

    # Stakeholders
    coverage = listening_coverage(sh.listening_sessions)
    gaps = [DIRECTION_LABELS[d] for d in listening_gaps(sh.listening_sessions)]
    quadrants: dict[str, list[str]] = {q: [] for q in (
        "Gestionar de cerca", "Mantener satisfecho", "Mantener informado", "Monitorizar")}
    for g in sorted(sh.groups, key=lambda g: (-g.influence, -g.interest)):
        quadrants[g.quadrant].append(g.name)
    mapped = [g for g in sh.groups if g.map]
    vanity = vanity_groups(sh.groups)

    # Sponsors
    assessments = assess_sponsors(sp)
    recommended = recommend(assessments)
    mismatch = pilot_mismatch(sp.pilot_business_case, recommended)

    # Coalición
    signals = detect_signals(co)
    partners = [g for g in sh.groups if g.partnership]

    common = {"company": COMPANY, "purpose": sh.purpose}
    outputs = {
        "chart": plot_matrix(sh.groups, out_dir / CHART_NAME),
        "register": write_text(out_dir / "stakeholder_register.md", render_template(
            TEMPLATES, "stakeholder_register.md.j2", **common, coverage=coverage, gaps=gaps,
            direction_labels=DIRECTION_LABELS, quadrants=quadrants, chart_name=CHART_NAME,
            internal=[g for g in sh.groups if g.kind == "internal"],
            external=[g for g in sh.groups if g.kind == "external"],
            level_labels=LEVEL_LABELS, health_labels=HEALTH_LABELS)),
        "map": write_text(out_dir / "stakeholder_map.md", render_template(
            TEMPLATES, "stakeholder_map.md.j2", **common, groups=mapped, vanity=vanity)),
        "sponsors": write_text(out_dir / "sponsor_assessment.md", render_template(
            TEMPLATES, "sponsor_assessment.md.j2", criteria=CRITERIA, weights=sp.weights,
            assessments=assessments, recommended=recommended, mismatch=mismatch,
            case=sp.pilot_business_case, names=names, domain_names=DOMAIN_NAMES)),
        "coalition": write_text(out_dir / "coalition_plan.md", render_template(
            TEMPLATES, "coalition_plan.md.j2", company=COMPANY, partners=partners,
            committee=co.committee, meetings=co.meetings, signals=signals,
            attendance_labels=ATTENDANCE_LABELS, signal_labels=SIGNAL_LABELS,
            forum=co.open_forum, channels=co.channels, communications=co.communications)),
    }

    console.rule("[bold]Capítulo 2: Construir una coalición de defensores")
    console.print(f"Stakeholders: {len(sh.groups)} grupos, {len(mapped)} en el mapa.")
    if gaps:
        console.print(f"[yellow]Huecos de escucha:[/yellow] {', '.join(gaps)}")
    for g in vanity:
        console.print(f"[yellow]Solo vanity metrics:[/yellow] {g.name}")
    for i, a in enumerate(recommended):
        role = "principal" if i == 0 else "secundario"
        console.print(f"Sponsor {role}: [bold]{names[a.candidate.stakeholder]}[/bold] "
                      f"({a.score:.0f}/100)")
    if mismatch:
        console.print(f"[yellow]{mismatch}[/yellow]")
    for s in signals:
        console.print(f"[yellow]Señal del comité:[/yellow] {s.message}")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

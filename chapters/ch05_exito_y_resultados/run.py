"""Capítulo 5: definir el éxito y alinear resultados (los 8 pasos).

Usa la data equity del capítulo 1, los stakeholders del capítulo 2 y los indicadores del
warehouse del capítulo 4 (requiere `uv run dglab build`).
Uso: uv run python -m chapters.ch05_exito_y_resultados.run
"""

from datetime import timedelta
from pathlib import Path

import matplotlib.dates as mdates
from matplotlib.patches import Patch
from matplotlib.transforms import blended_transform_factory
from rich.console import Console

from chapters.ch01_que_es_gobierno_datos.equity import (
    DataEquityInput,
    EquityLine,
    evaluate_equity,
)
from chapters.ch02_coalicion_defensores.stakeholders import StakeholderInput
from chapters.ch04_linea_base_madurez.evidence import indicators
from dglab import viz
from dglab.config import load_yaml
from dglab.dates import add_months
from dglab.paths import WAREHOUSE_DB
from dglab.reporting import fmt_money, fmt_num, fmt_pct, render_template, write_text
from dglab.warehouse import connect

from .framework import BARRIER_LABELS, OutcomeFramework, warnings
from .progress import (
    STATUS_LABELS,
    completed_by,
    data_outcomes,
    due_in,
    expected_progress,
    outcome_status,
)

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CHAPTERS = CHAPTER_DIR.parent
CHART_NAME = "roadmap.png"
COMPANY = "NovaMercado"


def fmt_metric(value: float | None, unit: str) -> str:
    if value is None:
        return "—"
    return {"usd": fmt_money, "pct": fmt_pct}.get(unit, lambda v: fmt_num(v) + (
        " h" if unit == "hours" else ""))(value)


def variance_text(fw: OutcomeFramework, o) -> str:
    overdue = [d for d in o.deliverables if d.overdue(fw.as_of)]
    if overdue:
        return "Entregables vencidos: " + "; ".join(
            f"{d.id} ({d.done} de {d.total}, vencía el {d.due:%d/%m/%Y})" for d in overdue) + "."
    behind = [d for d in o.deliverables
              if d.done < expected_progress(d, fw.as_of) * d.total - 0.5]
    return "Por detrás del ritmo previsto: " + ", ".join(d.id for d in behind) + "."


def plot_roadmap(fw: OutcomeFramework, names: dict[str, str], path: Path) -> Path:
    """Paso 5: entregables en el tiempo, coloreados por resultado, con la fecha de corte."""
    rows = [(o, c, d) for o in fw.outcomes for c in o.capabilities for d in c.deliverables]
    colors = {o.id: viz.SERIES[i] for i, o in enumerate(fw.outcomes)}
    fig, ax = viz.new_figure(11, 0.42 * len(rows) + 1.8)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=viz.GRIDLINE, linewidth=0.8)
    for y, (o, _, d) in enumerate(rows):
        start, end = mdates.date2num(d.start), mdates.date2num(d.due)
        ax.barh(y, end - start, left=start, height=0.6, color=colors[o.id],
                edgecolor=viz.SURFACE, linewidth=2)
        status = "✓" if d.complete else ("vencido" if d.overdue(fw.as_of) else "")
        ax.annotate(f"{d.done}/{d.total} {status}".strip(), (end, y), xytext=(5, 0),
                    textcoords="offset points", va="center", fontsize=8,
                    color=viz.TEXT_SECONDARY, zorder=4,
                    bbox={"facecolor": viz.SURFACE, "edgecolor": "none", "pad": 0.5})
    cut = mdates.date2num(fw.as_of)
    ax.axvline(cut, color=viz.TEXT_PRIMARY, linewidth=1, linestyle="--")
    ax.text(cut, 0.99, f" Corte {fw.as_of:%d/%m/%Y}", ha="left", va="top", fontsize=8,
            color=viz.TEXT_PRIMARY, transform=blended_transform_factory(ax.transData,
                                                                        ax.transAxes))
    labels = [f"{d.id}. {d.name[:48]}{'…' if len(d.name) > 48 else ''}" for _, _, d in rows]
    ax.set_yticks(range(len(rows)), labels, fontsize=8)
    ax.invert_yaxis()
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))
    handles = [Patch(color=colors[o.id], label=f"{o.id} · {names[o.stakeholder]}")
               for o in fw.outcomes]
    ax.legend(handles=handles, frameon=False, loc="upper center", bbox_to_anchor=(0.4, -0.06),
              ncol=len(handles), labelcolor=viz.TEXT_SECONDARY, fontsize=8)
    viz.set_titles(ax, "Roadmap de entregables por resultado de negocio",
                   "Hitos completados sobre el total al final de cada barra")
    return viz.save_figure(fig, path)


def main(out_dir: Path | None = None, db_path: Path = WAREHOUSE_DB) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    if not db_path.exists():
        raise FileNotFoundError(f"No existe {db_path}: ejecuta antes `uv run dglab build`")
    console = Console()

    fw = OutcomeFramework.model_validate(load_yaml(INPUTS / "outcomes.yaml"))
    sh = StakeholderInput.model_validate(
        load_yaml(CHAPTERS / "ch02_coalicion_defensores" / "inputs" / "stakeholders.yaml"))
    equity = evaluate_equity(DataEquityInput.model_validate(
        load_yaml(CHAPTERS / "ch01_que_es_gobierno_datos" / "inputs" / "data_equity.yaml")))

    # Referencias a los capítulos 1 y 2
    lines = {ln.id: ln for ln in equity.lines}
    names = {g.id: g.name for g in sh.groups}
    for o in fw.outcomes:
        if o.stakeholder not in names:
            raise ValueError(f"{o.id}: stakeholder desconocido en el capítulo 2: {o.stakeholder}")
        missing = set(o.equity_lines) - set(lines)
        if missing:
            raise ValueError(f"{o.id}: líneas de data equity inexistentes: {sorted(missing)}")
    equity_by: dict[str, list[EquityLine]] = {
        o.id: [lines[i] for i in o.equity_lines] for o in fw.outcomes}
    value = {oid: sum(ln.benefit for ln in lns) for oid, lns in equity_by.items()}
    warns = warnings(fw) + [
        f"{o.id}: usa la línea {ln.id}, que el negocio aún no ha validado en el capítulo 1."
        for o in fw.outcomes for ln in equity_by[o.id] if not ln.vetted]

    # Seguimiento con los indicadores del warehouse
    with connect(db_path, read_only=True) as con:
        ind = indicators(con)
    summary = []
    for o in fw.outcomes:
        status = outcome_status(o, fw.as_of)
        summary.append({"o": o, "status": status, "data_outcomes": data_outcomes(o, fw, ind),
                        "variance": "" if status == "green" else variance_text(fw, o)})

    # Medidas de valor por stakeholder (QBR)
    horizon = add_months(fw.qbr.quarter_end, 3)
    by_stakeholder = []
    for sid in dict.fromkeys(o.stakeholder for o in fw.outcomes):
        outs = [o for o in fw.outcomes if o.stakeholder == sid]
        by_stakeholder.append({
            "group": sh.by_id(sid), "outcomes": outs,
            "capabilities": [c.name for o in outs for c in o.capabilities],
            "value": sum(value[o.id] for o in outs),
            "actual": [f"{o.business_metric.name}: "
                       f"{fmt_metric(o.business_metric.actual, o.business_metric.unit)}"
                       for o in outs],
            "completed": [d for o in outs for d in completed_by(o, fw.as_of)],
            "next": [d for o in outs for d in due_in(o, fw.as_of + timedelta(days=1), horizon)],
        })

    common = {"company": COMPANY, "names": names, "fmt": fmt_metric}
    outputs = {
        "roadmap": plot_roadmap(fw, {g.id: g.short for g in sh.groups}, out_dir / CHART_NAME),
        "framework": write_text(out_dir / "outcome_framework.md", render_template(
            TEMPLATES, "outcome_framework.md.j2", **common, outcomes=fw.outcomes,
            equity=equity_by, value=value)),
        "progress": write_text(out_dir / "progress_report.md", render_template(
            TEMPLATES, "progress_report.md.j2", **common, as_of=fw.as_of, summary=summary,
            status_labels=STATUS_LABELS, barrier_labels=BARRIER_LABELS, warnings=warns,
            barriers=sorted(fw.barriers, key=lambda b: -b.severity))),
        "value_map": write_text(out_dir / "value_map.md", render_template(
            TEMPLATES, "value_map.md.j2", **common, stakeholders=by_stakeholder, qbr=fw.qbr,
            value=value)),
    }

    console.rule("[bold]Capítulo 5: Definir el éxito y alinear resultados")
    for row in summary:
        o = row["o"]
        console.print(f"{o.id} ({names[o.stakeholder]}): {STATUS_LABELS[row['status']]}, "
                      f"hitos {o.milestone_progress:.0%}, valor {fmt_money(value[o.id])}/año")
        for s in row["data_outcomes"]:
            if s.measured is not None:
                mark = "✓" if s.achieved else "·"
                console.print(f"   {mark} {s.name}: medido {s.measured:.1%}")
    for w in warns:
        console.print(f"[yellow]Aviso:[/yellow] {w}")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

"""Capítulo 14: automatización de datos (los 6 pasos y enriquecimiento de terceros).

Necesita el warehouse con los datos de referencia del capítulo 10 (`pdm.ref_province`):
ejecuta antes el pipeline del capítulo 11 o el capítulo 10.
Uso: uv run python -m chapters.ch14_automatizacion.run
"""

from itertools import groupby
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel
from rich.console import Console

from dglab import viz
from dglab.config import load_yaml
from dglab.paths import RAW_DIR, WAREHOUSE_DB
from dglab.reporting import fmt_money, fmt_pct, render_template, write_text
from dglab.synthetic import read_truth
from dglab.warehouse import connect

from .automation import build_report, monitor, reconcile
from .enrichment import (
    Vendor,
    evaluate_vendor,
    invalid_orders_with_truth,
    pick_vendor,
    simulate_vendor,
)
from .roi import Approach, ApproachRoi, CurrentProcess, approach_roi

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CHART_NAME = "roi_by_approach.png"
COMPANY = "NovaMercado"


class Monitoring(BaseModel):
    window_weeks: int
    z_threshold: float
    max_unmapped_share: float
    allow_negative_lines: bool


class AutomationInput(BaseModel):
    goals: dict[str, str]
    current_process: CurrentProcess
    problem_statement: str
    cost_per_hour: float
    approaches: dict[str, Approach]
    chosen: str
    horizon_years: int
    monitoring: Monitoring
    vendors: list[Vendor]
    vendor_seed: int
    revenue_per_fixed_order: float


def plot_roi(rois: list[ApproachRoi], chosen: str, path: Path) -> Path:
    fig, ax = viz.new_figure(8, 3.6)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=viz.GRIDLINE, linewidth=0.8)
    labels = [r.approach.name.split(":")[0] for r in rois]
    colors = [viz.SERIES[1] if r.key == chosen else viz.SERIES[0] for r in rois]
    bars = ax.barh(labels, [r.net_benefit for r in rois], color=colors, height=0.55,
                   edgecolor=viz.SURFACE, linewidth=2)
    for bar, r in zip(bars, rois, strict=True):
        ax.annotate(f"{fmt_money(r.net_benefit)} · ROI {fmt_pct(r.roi)}",
                    (bar.get_width(), bar.get_y() + bar.get_height() / 2), xytext=(4, 0),
                    textcoords="offset points", va="center", fontsize=8,
                    color=viz.TEXT_SECONDARY)
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(lambda v, _: fmt_money(v))
    ax.set_xlim(0, max(r.net_benefit for r in rois) * 1.45)
    viz.set_titles(ax, "Beneficio neto a 3 años por enfoque",
                   "Enfoque elegido en naranja")
    return viz.save_figure(fig, path)


def main(out_dir: Path | None = None, db_path: Path = WAREHOUSE_DB,
         raw_dir: Path = RAW_DIR) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    if not db_path.exists():
        raise FileNotFoundError(f"No existe {db_path}: ejecuta antes `uv run dglab build`")
    console = Console()
    inp = AutomationInput.model_validate(load_yaml(INPUTS / "automation.yaml"))
    links, _ = read_truth(raw_dir)

    with connect(db_path, read_only=True) as con:
        has_ref = con.execute("SELECT count(*) FROM information_schema.tables WHERE "
                              "table_schema = 'pdm' AND table_name = 'ref_province'"
                              ).fetchone()[0]
        if not has_ref:
            raise RuntimeError("Faltan los datos de referencia del capítulo 10: ejecuta "
                               "`uv run python -m chapters.ch11_operaciones_datos.pipeline`")
        report, seconds = build_report(con)
        diff = reconcile(con, report)
        m = inp.monitoring
        alerts = monitor(con, report, m.window_weeks, m.z_threshold, m.max_unmapped_share,
                         m.allow_negative_lines)
        orders = invalid_orders_with_truth(con, links)

    rois = [approach_roi(k, a, inp.current_process, inp.cost_per_hour, inp.horizon_years)
            for k, a in inp.approaches.items()]
    chosen = next(r for r in rois if r.key == inp.chosen)
    rng = np.random.default_rng(inp.vendor_seed)
    vendors = [evaluate_vendor(orders, simulate_vendor(orders, v, rng), v) for v in inp.vendors]
    best = pick_vendor(vendors)
    unmapped = (report.loc[report["region"] == "Sin región", "net_sales"].sum()
                / report["net_sales"].sum())

    out_dir.mkdir(parents=True, exist_ok=True)
    report.to_csv(out_dir / "weekly_regional_sales.csv", index=False, encoding="utf-8")
    alerts_csv = out_dir / "alerts.csv"
    pd.DataFrame([a.__dict__ for a in alerts]).to_csv(alerts_csv, index=False,
                                                      encoding="utf-8")
    by_kind = sorted(alerts, key=lambda a: a.kind)
    outputs = {
        "weekly": out_dir / "weekly_regional_sales.csv",
        "alerts": alerts_csv,
        "chart": plot_roi(rois, inp.chosen, out_dir / CHART_NAME),
        "report": write_text(out_dir / "automation.md", render_template(
            TEMPLATES, "automation.md.j2", company=COMPANY, goals=inp.goals,
            process=inp.current_process, problem=inp.problem_statement, rois=rois,
            chosen=inp.chosen, chosen_roi=chosen, horizon=inp.horizon_years,
            cost_per_hour=inp.cost_per_hour, chart_name=CHART_NAME,
            manual_minutes=sum(s.minutes for s in inp.current_process.steps),
            seconds=seconds, weeks=report["week"].nunique(), diff=diff, unmapped=unmapped,
            alerts=alerts,
            alert_groups=[(k, list(g)) for k, g in groupby(by_kind, key=lambda a: a.kind)],
            invalid=len(orders), vendors=vendors, best=best,
            revenue_per_fix=inp.revenue_per_fixed_order)),
    }

    console.rule("[bold]Capítulo 14: Automatización de datos")
    console.print(f"Proceso manual: {inp.current_process.hours_per_year:,.0f} h/año → "
                  f"informe automático en {seconds:.2f} s para {report['week'].nunique()} "
                  f"semanas · diferencia con la cifra oficial: {fmt_money(diff, 2)}")
    for r in rois:
        console.print(f"  • {r.approach.name}: ahorro {fmt_money(r.annual_saving)}/año, "
                      f"ROI {r.roi:.0%}")
    console.print(f"Alertas: {len(alerts)} · sin región asignable: {unmapped:.2%}")
    for v in vendors:
        console.print(f"  • {v.vendor.name}: {v.correct}/{v.queried} correctos, {v.wrong} "
                      f"erróneos, {fmt_money(v.cost_per_correct, 2)} por corrección")
    console.print(f"Proveedor recomendado: [bold]{best.vendor.name}[/bold]")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

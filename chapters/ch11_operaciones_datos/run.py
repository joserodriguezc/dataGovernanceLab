"""Capítulo 11: operaciones de datos (pipeline orquestado, SLAs, tickets y valor).

Por defecto ejecuta antes el pipeline nocturno completo (carga del warehouse y capítulos 10,
6, 7 y 8) y registra la ejecución. Con `--sin-pipeline` solo genera el informe.
Uso: uv run python -m chapters.ch11_operaciones_datos.run [--sin-pipeline]
"""

import sys
from datetime import datetime
from pathlib import Path

import matplotlib.dates as mdates
import numpy as np
from rich.console import Console

from dglab import viz
from dglab.config import load_yaml
from dglab.paths import OPS_DB, RAW_DIR, ROOT, WAREHOUSE_DB
from dglab.reporting import fmt_money, fmt_num, render_template, write_text
from dglab.warehouse import connect

from .analysis import (
    hotspots,
    last_runs,
    root_causes,
    row_count_changes,
    sla_summary,
    value_stream,
)
from .config import OpsConfig
from .history import simulate_nights, simulate_tickets
from .pipeline import ops_connect, run_pipeline

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
COMPANY = "NovaMercado"
STATUS_LABELS = {"ok": "✅ Correcto", "fallido": "❌ Fallido", "omitido": "⏭ Omitido"}
PROPOSALS = {
    "Bugs": "Pruebas automáticas en el SDLC (revisión del capítulo 9) antes de desplegar",
    "Calidad de datos": "Regla de calidad en origen (capítulo 8) en lugar de corregir después",
    "Fallos de proceso": "Alerta temprana y reintento automático del paso",
    "Petición de datos ad hoc": "Publicar el dataset en el marketplace (capítulo 6)",
}


def plot_timeline(cfg: OpsConfig, nights, path: Path) -> Path:
    per_night = nights.groupby("night").agg(end=("finished_at", "max"),
                                            ok=("status", lambda s: (s == "ok").all()))
    hours = [(e - datetime.combine(n, datetime.min.time())).total_seconds() / 3600
             for n, e in zip(per_night.index, per_night["end"], strict=True)]
    deadline = cfg.delivery.ready_by.hour + cfg.delivery.ready_by.minute / 60
    days = [mdates.date2num(d) for d in per_night.index]
    fig, ax = viz.new_figure(10, 4)
    ax.plot(days, hours, color=viz.SERIES[0], linewidth=1.5, label="Hora de fin")
    failed = [(d, h) for d, h, ok in zip(days, hours, per_night["ok"], strict=True) if not ok]
    if failed:
        ax.scatter(*zip(*failed, strict=True), color=viz.STATUS["critical"], marker="X", s=60,
                   zorder=3, edgecolors=viz.SURFACE, linewidths=1.5, label="Noche con fallo")
    ax.axhline(deadline, color=viz.TEXT_MUTED, linestyle="--", linewidth=1)
    ax.annotate(f"SLA {cfg.delivery.ready_by:%H:%M}", (days[-1], deadline), xytext=(0, 4),
                textcoords="offset points", fontsize=8, ha="right", color=viz.TEXT_SECONDARY)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.yaxis.set_major_formatter(lambda v, _: f"{int(v):02d}:{int(round(v % 1 * 60)):02d}")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2,
              labelcolor=viz.TEXT_SECONDARY, fontsize=8)
    viz.set_titles(ax, "Hora de fin del pipeline nocturno",
                   f"Últimas {len(days)} noches (historial simulado)")
    return viz.save_figure(fig, path)


def plot_causes(causes, path: Path) -> Path:
    data = causes.sort_values("tickets")
    fig, ax = viz.new_figure(8, 3.2)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=viz.GRIDLINE, linewidth=0.8)
    total = data["tickets"].sum()
    bars = ax.barh(data.index, data["tickets"], color=viz.SERIES[0], height=0.6,
                   edgecolor=viz.SURFACE, linewidth=2)
    for bar, n in zip(bars, data["tickets"], strict=True):
        ax.annotate(f"{n} ({n / total:.0%})", (bar.get_width(), bar.get_y() + 0.3),
                    xytext=(4, 0), textcoords="offset points", va="center", fontsize=8,
                    color=viz.TEXT_SECONDARY)
    ax.set_xlabel("Tickets", color=viz.TEXT_SECONDARY)
    viz.set_titles(ax, "Causas raíz de los tickets de operaciones de datos")
    return viz.save_figure(fig, path)


def main(out_dir: Path | None = None, db_path: Path = WAREHOUSE_DB, raw_dir: Path = RAW_DIR,
         ops_db: Path = OPS_DB, run: bool = True) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    console = Console()
    cfg = OpsConfig.model_validate(load_yaml(INPUTS / "operations.yaml"))
    if run:
        console.rule("[bold]Pipeline nocturno")
        run_pipeline(cfg.pipeline, db_path, raw_dir, ops_db, console=console,
                     out=None if out_dir == CHAPTER_DIR / "outputs" else out_dir / "pipeline")
    if not db_path.exists():
        raise FileNotFoundError(f"No existe {db_path}: ejecuta antes `uv run dglab build`")

    rng = np.random.default_rng(cfg.history.seed)
    nights = simulate_nights(cfg, rng)
    tickets = simulate_tickets(cfg, nights, rng)
    sla = sla_summary(cfg, nights)
    causes = root_causes(tickets)
    with ops_connect(ops_db) as ops:
        last, total_runs = last_runs(ops)
        changes = row_count_changes(ops, cfg.row_count_tolerance) if total_runs else None
        run_id = ops.execute("SELECT max(run_id) FROM runs").fetchone()[0]
    with connect(db_path, read_only=True) as con:
        latest_sale = con.execute("SELECT max(sale_date) FROM curated.fct_sales").fetchone()[0]
    last_by_step = {r.step: {"status": r.status, "attempts": r.attempts, "seconds": r.seconds,
                             "executed_by": r.executed_by,
                             "label": f"{STATUS_LABELS[r.status]} · {fmt_num(r.seconds, 1)} s"}
                    for r in last.itertuples()}
    value = value_stream(cfg)
    try:
        ops_label = ops_db.relative_to(ROOT).as_posix()
    except ValueError:
        ops_label = ops_db.name

    outputs = {
        "timeline": plot_timeline(cfg, nights, out_dir / "ops_timeline.png"),
        "causes": plot_causes(causes, out_dir / "ops_root_causes.png"),
    }
    tickets_csv = out_dir / "tickets.csv"
    tickets.to_csv(tickets_csv, index=False, encoding="utf-8")
    outputs["tickets"] = tickets_csv
    outputs["report"] = write_text(out_dir / "data_operations.md", render_template(
        TEMPLATES, "data_operations.md.j2", company=COMPANY, as_of=cfg.as_of, value=value,
        automations=cfg.automations, cost_per_hour=cfg.cost_per_hour, run_id=run_id or "—",
        total_runs=total_runs, ops_db=ops_label, steps=cfg.pipeline, last=last_by_step,
        status_labels=STATUS_LABELS, latest_sale=latest_sale,
        freshness=(cfg.as_of - latest_sale).days, delivery=cfg.delivery,
        row_changes=list(changes.itertuples()) if changes is not None else None,
        tolerance=cfg.row_count_tolerance, sla=sla, timeline_chart="ops_timeline.png",
        tickets=tickets, ticket_hours=tickets["hours"].sum(),
        open_tickets=int((tickets["status"] == "abierto").sum()),
        mttr=tickets["days_to_resolve"].mean(), causes_chart="ops_root_causes.png",
        causes=list(causes.iterrows()), hotspots=list(hotspots(tickets).itertuples()),
        proposals=PROPOSALS, partnership=cfg.partnership, visibility=cfg.visibility))

    console.rule("[bold]Capítulo 11: Operaciones de datos")
    console.print(f"Última ejecución {run_id}: " + ", ".join(
        f"{k} {v['status']}" for k, v in last_by_step.items()) + f" · {total_runs} registradas")
    console.print(f"Historial: {sla.success_rate:.1%} noches sin fallos, {sla.on_time_rate:.1%} "
                  f"a tiempo (objetivo {cfg.delivery.success_target:.0%})")
    console.print(f"Tickets: {len(tickets)} · causa principal: {causes.index[0]} "
                  f"({int(causes.iloc[0].tickets)})")
    console.print(f"Valor: {fmt_money(value.dollars)} · {value.hours:,.0f} h · {value.risks} "
                  f"riesgos · {value.automations} automatizaciones")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main(run="--sin-pipeline" not in sys.argv)

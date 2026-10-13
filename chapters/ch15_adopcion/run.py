"""Capítulo 15: adopción que impulsa el negocio.

No necesita el warehouse: trabaja con logs de uso simulados y la encuesta de usuarios.
Uso: uv run python -m chapters.ch15_adopcion.run
"""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel
from rich.console import Console

from dglab import viz
from dglab.config import load_yaml
from dglab.reporting import fmt_money, render_template, write_text

from .diagnosis import ACTIONS, adoption_cost, diagnose
from .usage import Solution, adoption_by_department, monthly_active, retention, simulate_usage

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CHART_NAME = "monthly_active_users.png"
COMPANY = "NovaMercado"


class Targets(BaseModel):
    adoption_rate: float
    retention: float
    weak_score: float


class RoadmapItem(BaseModel):
    solution: str
    group: str
    go_live: date
    hypercare_weeks: int
    users: int


class AdoptionInput(BaseModel):
    as_of: date
    months: int
    seed: int
    cost_per_hour: float
    departments: dict[str, int]
    solutions: list[Solution]
    survey: dict[str, dict[str, float]]
    targets: Targets
    roadmap: list[RoadmapItem]


def plot_mau(mau: pd.DataFrame, names: dict[str, str], path: Path) -> Path:
    fig, ax = viz.new_figure(9, 4.2)
    for color, col in zip(viz.SERIES, mau.columns, strict=False):
        ax.plot(mau.index, mau[col], color=color, linewidth=2, marker="o", markersize=5,
                label=names[col])
        ax.annotate(f"{mau[col].iloc[-1]:.0f}", (len(mau) - 1, mau[col].iloc[-1]),
                    xytext=(6, 0), textcoords="offset points", va="center", fontsize=8,
                    color=viz.TEXT_SECONDARY)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Usuarios activos", color=viz.TEXT_SECONDARY)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2,
              labelcolor=viz.TEXT_SECONDARY, fontsize=8)
    viz.set_titles(ax, "Usuarios activos al mes por solución",
                   "Logs de uso simulados desde la salida en vivo")
    return viz.save_figure(fig, path)


def main(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    console = Console()
    inp = AdoptionInput.model_validate(load_yaml(INPUTS / "adoption.yaml"))
    ids = {s.id for s in inp.solutions}
    unknown = (set(inp.survey) ^ ids) | {r.solution for r in inp.roadmap} - ids
    if unknown:
        raise ValueError(f"soluciones desconocidas o sin encuesta: {sorted(unknown)}")
    for s in inp.solutions:
        over = [d for d, n in s.target.items() if n > inp.departments.get(d, 0)]
        if over:
            raise ValueError(f"{s.id}: más usuarios objetivo que plantilla en {over}")

    usage = simulate_usage(inp.solutions, inp.as_of, inp.months,
                           np.random.default_rng(inp.seed))
    mau = monthly_active(usage, inp.solutions)
    last = mau.index.max()
    names = {s.id: s.name for s in inp.solutions}
    kpis = []
    for s in inp.solutions:
        active = int(mau.at[last, s.id]) if s.id in mau else 0
        rate = active / s.target_users
        ret = retention(usage, s.id)
        by_dept = adoption_by_department(usage, s, last)
        kpis.append({
            "s": s, "active": active, "rate": rate, "retention": ret, "by_dept": by_dept,
            "depts_used": sum(v > 0 for v in by_dept.values()),
            "ok": rate >= inp.targets.adoption_rate and ret >= inp.targets.retention,
            "cost": adoption_cost(s, rate, inp.cost_per_hour),
            "diagnosis": diagnose(inp.survey[s.id], inp.targets.weak_score),
        })
    old_way = {s.id: s.old_way.hours_per_user_month for s in inp.solutions}
    roadmap = [r.model_dump() | {"hours": r.users * old_way[r.solution] * 12,
                                 "value": r.users * old_way[r.solution] * 12 * inp.cost_per_hour}
               for r in sorted(inp.roadmap, key=lambda r: r.go_live)]

    out_dir.mkdir(parents=True, exist_ok=True)
    usage_csv = out_dir / "usage_log.csv"
    usage.to_csv(usage_csv, index=False, encoding="utf-8")
    outputs = {
        "usage": usage_csv,
        "chart": plot_mau(mau, names, out_dir / CHART_NAME),
        "report": write_text(out_dir / "adoption.md", render_template(
            TEMPLATES, "adoption.md.j2", company=COMPANY, as_of=inp.as_of, kpis=kpis,
            targets=inp.targets, chart_name=CHART_NAME,
            departments=list(inp.departments), actions=ACTIONS,
            total_cost=sum(k["cost"].total for k in kpis), roadmap=roadmap, names=names,
            cost_per_hour=inp.cost_per_hour)),
    }

    console.rule("[bold]Capítulo 15: Adopción")
    for k in kpis:
        mark = "[green]✓[/green]" if k["ok"] else "[red]✗[/red]"
        console.print(f"{mark} {k['s'].name}: adopción {k['rate']:.0%}, retención "
                      f"{k['retention']:.0%}, coste de la baja adopción "
                      f"{fmt_money(k['cost'].total)}/año")
        for d in k["diagnosis"]:
            console.print(f"    causa: {d.label} ({', '.join(w[1] for w in d.weak)})")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

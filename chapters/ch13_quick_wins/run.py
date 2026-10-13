"""Capítulo 13: quick wins con impacto.

Mide el tamaño de cada problema en el warehouse (mejor con los capítulos 6, 8 y 10 ya
ejecutados, o el pipeline del capítulo 11).
Uso: uv run python -m chapters.ch13_quick_wins.run
"""

from collections import defaultdict
from pathlib import Path

from rich.console import Console

from chapters.ch03_equipo_alto_rendimiento.team import TeamInput
from chapters.ch05_exito_y_resultados.framework import OutcomeFramework
from dglab import viz
from dglab.config import load_yaml
from dglab.paths import ROOT, WAREHOUSE_DB
from dglab.reporting import fmt_num, fmt_pct, render_template, write_text
from dglab.warehouse import connect

from .ownership import ownership_register
from .quickwins import (
    FUNDING_LABELS,
    LEVEL,
    LEVEL_LABELS,
    DeliveryInput,
    NeedsInput,
    fuzzy_rationalization,
    issue_matrix,
    measure,
    plan,
)

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CHAPTERS = ROOT / "chapters"
CHART_NAME = "impact_vs_cost.png"
COMPANY = "NovaMercado"

STANDARD = {
    "title": "Datos de contacto de cliente", "owner": "Responsable de CRM (steward de cliente)",
    "purpose": "Que cada cliente sea localizable por el canal que ha autorizado.",
    "scope": "Altas y modificaciones de clientes en el CRM, el e-commerce y las tarjetas de "
             "tienda.",
    "requirements": ["Email obligatorio y con formato válido en el CRM",
                     "Teléfono móvil de 9 dígitos sin prefijo ni separadores",
                     "Código postal de 5 dígitos validado contra los datos de referencia",
                     "Consentimiento de marketing registrado de forma expresa"],
    "measure": "Reglas DQ-01, DQ-02, DQ-05 y DQ-07 del capítulo 8, publicadas en el scorecard.",
}
PROCEDURE = {
    "title": "Solicitar un nuevo conjunto de datos", "owner": "Líder de gobierno y estrategia",
    "steps": [("Solicitante", "Busca primero en el marketplace: puede que ya exista certificado"),
              ("Solicitante", "Si no existe, describe la pregunta de negocio que quiere responder"),
              ("Steward de negocio", "Valida la necesidad y la fuente autorizada"),
              ("Ingeniería de datos", "Construye el conjunto de datos siguiendo los estándares"),
              ("Steward técnico", "Pasa la revisión de arquitectura y las reglas de calidad"),
              ("Oficina de datos", "Lo publica en el marketplace y avisa al solicitante")],
    "sla": "10 días laborables",
}


def plot_matrix(ranked, path: Path) -> Path:
    """Impacto frente a coste; cada punto lleva el número del problema en la priorización."""
    fig, ax = viz.new_figure(7, 5)
    ax.grid(False)
    cells: dict[tuple[int, int], list[int]] = defaultdict(list)
    for rank, (_, issue, _) in enumerate(ranked, start=1):
        cells[(LEVEL[issue.cost], LEVEL[issue.impact])].append(rank)
    ax.fill_between([0.5, 1.5], 1.5, 3.5, color=viz.SEQUENTIAL_BLUE[0], alpha=0.6, zorder=0)
    ax.text(0.55, 3.45, "Quick wins", fontsize=9, color=viz.TEXT_SECONDARY, va="top")
    for (x, y), ranks in cells.items():
        offsets = [(i - (len(ranks) - 1) / 2) * 0.16 for i in range(len(ranks))]
        for rank, dx in zip(ranks, offsets, strict=True):
            ax.scatter([x + dx], [y], s=260, color=viz.SERIES[0], edgecolors=viz.SURFACE,
                       linewidths=1.5, zorder=3)
            ax.text(x + dx, y, str(rank), ha="center", va="center", fontsize=8,
                    color=viz.SURFACE, zorder=4)
    ax.set_xlim(0.5, 3.5)
    ax.set_ylim(0.5, 3.5)
    ax.set_xticks([1, 2, 3], ["Coste bajo", "Coste medio", "Coste alto"])
    ax.set_yticks([1, 2, 3], ["Impacto bajo", "Impacto medio", "Impacto alto"])
    ax.axhline(1.5, color=viz.GRIDLINE, linewidth=1)
    ax.axvline(1.5, color=viz.GRIDLINE, linewidth=1)
    viz.set_titles(ax, "Problemas comunes: impacto frente a coste",
                   "El número es la posición en la priorización (tabla del informe)")
    return viz.save_figure(fig, path)


def main(out_dir: Path | None = None, db_path: Path = WAREHOUSE_DB) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    if not db_path.exists():
        raise FileNotFoundError(f"No existe {db_path}: ejecuta antes `uv run dglab build`")
    console = Console()
    needs = NeedsInput.model_validate(load_yaml(INPUTS / "needs.yaml"))
    delivery = DeliveryInput.model_validate(load_yaml(INPUTS / "delivery.yaml"))
    outcomes = {o.id for o in OutcomeFramework.model_validate(load_yaml(
        CHAPTERS / "ch05_exito_y_resultados" / "inputs" / "outcomes.yaml")).outcomes}
    orphans = [k for k, i in needs.issues.items() if i.outcome not in outcomes]
    if orphans:
        raise ValueError(f"problemas sin un resultado del capítulo 5: {orphans}")
    unknown_ideas = [i.idea for i in delivery.ideas if i.issue not in needs.issues]
    if unknown_ideas:
        raise ValueError(f"ideas asignadas a problemas inexistentes: {unknown_ideas}")
    roles = TeamInput.model_validate(load_yaml(
        CHAPTERS / "ch03_equipo_alto_rendimiento" / "inputs" / "team.yaml")).functional_roles

    with connect(db_path, read_only=True) as con:
        sizes = {k: measure(con, i) for k, i in needs.issues.items()}
        register = ownership_register(con, roles)

    def size_label(key: str) -> str:
        value, unit = sizes[key], needs.issues[key].size_unit
        if value is None:
            return "sin medir" if unit else "no medible en el warehouse"
        return fmt_pct(value, 1) if unit == "pct" else fmt_num(value)

    ranked = [(k, i, size_label(k)) for k, i in
              sorted(needs.issues.items(), key=lambda kv: (-kv[1].score, kv[0]))]
    matrix = issue_matrix(needs.needs)
    groups = list(dict.fromkeys(n.group for n in needs.needs))
    roadmap = plan(needs.issues, delivery.quarters, delivery.capacity_per_quarter)
    titles = {k: i.title for k, i in needs.issues.items()}
    fuzzy = fuzzy_rationalization(needs.needs)

    out_dir.mkdir(parents=True, exist_ok=True)
    register_csv = out_dir / "data_ownership_register.csv"
    register.to_csv(register_csv, index=False, encoding="utf-8")
    outputs = {
        "chart": plot_matrix(ranked, out_dir / CHART_NAME),
        "ownership": register_csv,
        "report": write_text(out_dir / "quick_wins.md", render_template(
            TEMPLATES, "quick_wins.md.j2", company=COMPANY, needs=needs.needs, groups=groups,
            matrix=matrix, matrix_sorted=sorted(matrix.items(), key=lambda kv: -len(kv[1])),
            issues=needs.issues, fuzzy=fuzzy, chart_name=CHART_NAME, ranked=ranked,
            levels=LEVEL_LABELS, funding=FUNDING_LABELS, roadmap=roadmap,
            capacity=delivery.capacity_per_quarter, titles=titles,
            solutions=delivery.solutions, communication=delivery.communication,
            ideas=delivery.ideas)),
        "psp": write_text(out_dir / "psp_templates.md", render_template(
            TEMPLATES, "psp_templates.md.j2", standard=STANDARD, procedure=PROCEDURE)),
    }

    console.rule("[bold]Capítulo 13: Quick wins con impacto")
    console.print(f"{len(needs.needs)} necesidades → {len(matrix)} problemas comunes · la "
                  f"similitud de texto solo encuentra {fuzzy.found_by_fuzzy} de "
                  f"{fuzzy.same_issue_pairs} pares del mismo problema")
    for _, i, size in ranked[:5]:
        console.print(f"  • {i.title}: puntuación {i.score}, {i.quadrant}, tamaño {size}")
    console.print("Roadmap: " + " · ".join(f"{q}: {len(v)}" for q, v in roadmap.items()))
    gaps = register[register["huecos"] != ""]["dominio"].unique().tolist()
    console.print(f"Registro de propiedad: {len(register)} activos · dominios con huecos: "
                  f"{', '.join(gaps) or 'ninguno'}")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

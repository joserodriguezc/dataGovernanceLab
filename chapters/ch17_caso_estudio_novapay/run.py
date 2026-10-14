"""Capítulo 17: caso de estudio de NovaPay, de punta a punta, con un solo comando.

Genera los datos de NovaPay, construye su warehouse (data/warehouse/novapay.duckdb) y aplica
las herramientas de los capítulos 1, 3, 6, 7, 8 y 12. No depende del warehouse de NovaMercado.
Uso: uv run python -m chapters.ch17_caso_estudio_novapay.run
"""

from collections import Counter
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from rich.console import Console

from chapters.ch01_que_es_gobierno_datos.business_case import TimelineOption, evaluate_option
from chapters.ch03_equipo_alto_rendimiento.raci import RaciInput
from chapters.ch06_gestion_metadatos.classify import ClassificationPolicy
from chapters.ch12_lanzamiento.messaging import review_memo
from dglab import viz
from dglab.config import load_yaml
from dglab.paths import ROOT, WAREHOUSE_DIR
from dglab.reporting import render_template, write_text

from .case import (
    CURATED_RULES,
    RAW_RULES,
    certify_days,
    document,
    lineage_roots,
    pii_columns,
    run_rules,
    segregation,
)
from .data import Generation, generate
from .warehouse import SQL, build, manual_report, true_report

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CH06_POLICY = ROOT / "chapters" / "ch06_gestion_metadatos" / "inputs" / "classification.yaml"
CHART_NAME = "liquidity_ratio.png"
KEYS = {"raw.liquidity_submissions": "row_id",
        "staging.stg_liquidity_items": "item_key"}


def plot_ratio(manual: pd.DataFrame, curated: pd.DataFrame, truth: pd.DataFrame,
               minimum: float, path: Path) -> Path:
    fig, ax = viz.new_figure(10, 4.4)
    ax.plot(manual.report_date, manual.liquidity_ratio.clip(-1, 3), color=viz.SERIES[1],
            linewidth=1.5, label="Hoja consolidada a mano")
    ax.plot(truth.report_date, truth.liquidity_ratio, color=viz.TEXT_MUTED, linewidth=4,
            alpha=0.5, label="Valor real")
    ax.plot(curated.report_date, curated.liquidity_ratio, color=viz.SERIES[0], linewidth=2,
            label="Informe remediado (huecos: días incompletos)")
    ax.axhline(minimum, color=viz.STATUS["critical"], linestyle="--", linewidth=1)
    ax.annotate(f"Mínimo regulatorio {minimum:.2f}".replace(".", ","),
                (curated.report_date.iloc[0], minimum), xytext=(0, -12),
                textcoords="offset points", fontsize=8, color=viz.TEXT_SECONDARY)
    ax.set_ylim(-1, 3)
    ax.set_ylabel("Activos líquidos / obligaciones", color=viz.TEXT_SECONDARY)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3,
              labelcolor=viz.TEXT_SECONDARY, fontsize=8)
    viz.set_titles(ax, "Ratio de liquidez diaria de NovaPay",
                   "La hoja a mano se recorta entre -1 y 3 para poder verla")
    return viz.save_figure(fig, path)


def main(out_dir: Path | None = None, db_path: Path | None = None) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    db_path = db_path or WAREHOUSE_DIR / "novapay.duckdb"
    console = Console()
    cfg = load_yaml(INPUTS / "novapay.yaml")
    g = Generation.model_validate(cfg["generation"])
    as_of: date = cfg["as_of"]

    # Datos y warehouse
    data = generate(g)
    build(db_path, data, {u: x.side for u, x in g.units.items()})

    # Segregación de funciones (capítulo 3)
    roles = cfg["raci_roles"]
    before = segregation(RaciInput(roles=roles, activities=cfg["raci_before"]),
                         cfg["prepare_activity"], cfg["review_activity"])
    after = segregation(RaciInput(roles=roles, activities=cfg["raci_after"]),
                        cfg["prepare_activity"], cfg["review_activity"])

    policy_cfg = load_yaml(CH06_POLICY)
    policy_cfg["rules"] = cfg["extra_pii_rules"] + policy_cfg["rules"]
    policy = ClassificationPolicy.model_validate(policy_cfg)
    with duckdb.connect(str(db_path)) as con:
        raw_results = run_rules(con, RAW_RULES, KEYS, as_of)
        curated_results = run_rules(con, CURATED_RULES, KEYS, as_of)
        docs = document(con)
        roots = lineage_roots(con, SQL, "curated.fct_liquidity_report.liquidity_ratio")
        pii = pii_columns(con, policy)
        certified, total = certify_days(con, docs > 0, bool(roots))
        manual = manual_report(con)
        curated = con.execute("SELECT * FROM curated.fct_liquidity_report ORDER BY 1").df()
    truth = true_report(data.truth)
    for df in (manual, curated, truth):
        df["report_date"] = pd.to_datetime(df["report_date"])

    minimum = g.regulatory_minimum
    merged = truth.merge(manual, on="report_date", suffixes=("_true", "_manual")).merge(
        curated[["report_date", "liquidity_ratio", "complete"]], on="report_date")
    complete = merged["complete"]
    manual_error = float(np.mean(np.abs(merged.liquidity_ratio_manual
                                        - merged.liquidity_ratio_true)))
    curated_error = float(np.mean(np.abs(merged.liquidity_ratio[complete]
                                         - merged.liquidity_ratio_true[complete])))
    issues_raw = sum(r.failed for r in raw_results)
    issues_after = sum(r.failed for r in curated_results)
    issue_reduction = 1 - issues_after / issues_raw if issues_raw else 0.0
    breakdown = Counter()
    for r in raw_results:
        breakdown[r.rule.dimension] += r.failed

    # Opciones para el comité (capítulo 1)
    options = [evaluate_option(TimelineOption(**o), cfg["annual_benefit"], cfg["horizon_months"],
                               cfg["discount_rate_annual"]) for o in cfg["options"]]
    chosen = next(o for o in options if o.option.id == cfg["chosen_option"])
    automated = np.mean([s["automated"] for s in cfg["manual_steps"]])

    common = dict(
        company=cfg["company"], days=len(truth), quick_wins=cfg["quick_wins"],
        manual_breaches=int((manual.liquidity_ratio < minimum).sum()),
        true_breaches=int((truth.liquidity_ratio < minimum).sum()),
        manual_error=manual_error, curated_error=curated_error, before=before, after=after,
        certified=certified, total=total, plan=cfg["long_term_plan"], sponsors=cfg["sponsors"],
        option=chosen)
    regulator = render_template(TEMPLATES, "regulator_message.md.j2", **common)
    review = review_memo(regulator, 900)
    outputs = {
        "chart": plot_ratio(manual, curated, truth, minimum, out_dir / CHART_NAME),
        "elt": write_text(out_dir / "elt_summary.md", render_template(
            TEMPLATES, "elt_summary.md.j2", **common, issues_raw=issues_raw,
            issue_breakdown=", ".join(f"{dim} {n}" for dim, n in breakdown.most_common()))),
        "regulator": write_text(out_dir / "regulator_message.md", regulator),
        "case": write_text(out_dir / "case_study.md", render_template(
            TEMPLATES, "case_study.md.j2", **common, scenario=cfg["scenario"],
            discovery=cfg["discovery"], themes=cfg["themes"], chart_name=CHART_NAME,
            minimum=minimum,
            curated_breaches=int((curated.liquidity_ratio < minimum).sum()),
            incomplete=int((~curated.complete).sum()), raw_results=raw_results,
            curated_results=curated_results, roots=roots, pii=pii, options=options,
            chosen=cfg["chosen_option"], horizon=cfg["horizon_months"], review=review,
            buckets=cfg["buckets"], docs=docs,
            issue_reduction=issue_reduction,
            automated=automated)),
    }

    console.rule(f"[bold]Capítulo 17: Caso de estudio {cfg['company']}")
    console.print(f"Días por debajo del mínimo: hoja a mano {common['manual_breaches']}, "
                  f"real {common['true_breaches']} · error medio de la ratio: hoja "
                  f"{manual_error:.2f}, remediado {curated_error:.4f}")
    before_txt = "✓" if before.ok else "✗ " + ", ".join(before.overlap)
    console.print(f"Segregación de funciones: antes {before_txt}"
                  f" · después {'✓' if after.ok else '✗'}")
    console.print(f"Incidencias de calidad: {issues_raw} en origen → {issues_after} tras remediar "
                  f"({issue_reduction:.0%} menos)")
    console.print(f"Linaje de la ratio: {len(roots)} orígenes · datos personales: {len(pii)} "
                  f"columnas · días certificados: {certified}/{total}")
    console.print(f"Opción aprobada: {chosen.option.name} (VAN {chosen.npv:,.0f})"
                  f" · mensaje al supervisor sin jerga: {review.ok}")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

"""Capítulo 8: calidad de datos (perfilado, reglas, incidencias, certificación y valor).

Requiere `uv run dglab build`; conviene ejecutar antes los capítulos 6 (documentación y
stewards) y 7 (linaje), porque la certificación los exige.
Uso: uv run python -m chapters.ch08_calidad_datos.run
"""

from pathlib import Path

import pandas as pd
from rich.console import Console

from chapters.ch03_equipo_alto_rendimiento.team import TeamInput
from dglab import viz
from dglab.company import DOMAIN_NAMES
from dglab.config import load_yaml
from dglab.paths import RAW_DIR, WAREHOUSE_DB
from dglab.reporting import fmt_money, render_template, write_text
from dglab.synthetic import read_truth
from dglab.warehouse import connect

from .profiling import profile_table
from .publish import write_quality
from .quality import (
    SEVERITY_LABELS,
    certify,
    evaluate_detection,
    inherited_postal_defects,
    issue_log,
    marketable_contacts,
)
from .rules import DQInput, RuleResult, run_rules, scorecard

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CH03_TEAM = CHAPTER_DIR.parent / "ch03_equipo_alto_rendimiento" / "inputs" / "team.yaml"
CHART_NAME = "dq_rules.png"
COMPANY = "NovaMercado"
REMEDIATION_LABELS = {"estandarizar": "Estandarizar el formato", "excluir": "Excluir del cálculo",
                      "corregir_en_origen": "Corregir en el sistema de origen",
                      "enriquecer": "Enriquecer con un tercero", "aceptar": "Aceptar el riesgo"}


def plot_rules(results: list[RuleResult], path: Path) -> Path:
    """Registros válidos por regla frente a su umbral; forma y color indican si cumple."""
    rows = sorted((r for r in results if r.rule.type != "freshness"), key=lambda r: r.pass_rate)
    skipped = [r.rule.id for r in results if r.rule.type == "freshness"]
    fig, ax = viz.new_figure(9, 0.36 * len(rows) + 1.6)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=viz.GRIDLINE, linewidth=0.8)
    ys = range(len(rows))
    ax.scatter([r.rule.threshold for r in rows], ys, marker="|", s=200, color=viz.TEXT_MUTED,
               linewidths=2, zorder=2, label="Umbral")
    for meets, color, marker, label in [(True, viz.STATUS["good"], "o", "Cumple"),
                                        (False, viz.STATUS["critical"], "X", "No cumple")]:
        pts = [(r.pass_rate, y) for y, r in zip(ys, rows, strict=True)
               if r.meets_threshold == meets]
        if pts:
            ax.scatter(*zip(*pts, strict=True), s=60, color=color, marker=marker,
                       edgecolors=viz.SURFACE, linewidths=1.5, zorder=3, label=label)
    ax.set_yticks(list(ys), [f"{r.rule.id} · {r.rule.dimension}" for r in rows], fontsize=8)
    ax.set_xlim(min(0.75, min(r.pass_rate for r in rows) - 0.02), 1.005)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    ax.set_xlabel("Registros que cumplen la regla", color=viz.TEXT_SECONDARY)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3,
              labelcolor=viz.TEXT_SECONDARY, fontsize=8)
    note = (f" · sin las de actualidad ({', '.join(skipped)}), que miden el conjunto"
            if skipped else "")
    viz.set_titles(ax, "Calidad de datos: cada regla frente a su umbral",
                   f"Ordenadas de peor a mejor{note}")
    return viz.save_figure(fig, path)


def main(out_dir: Path | None = None, db_path: Path = WAREHOUSE_DB,
         raw_dir: Path = RAW_DIR) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    if not db_path.exists():
        raise FileNotFoundError(f"No existe {db_path}: ejecuta antes `uv run dglab build`")
    console = Console()
    inp = DQInput.model_validate(load_yaml(INPUTS / "dq_rules.yaml"))
    roles = TeamInput.model_validate(load_yaml(CH03_TEAM)).functional_roles
    stewards = {r.domain: r.business_stewards for r in roles}
    _, seeded = read_truth(raw_dir)

    with connect(db_path) as con:
        profiles = {t: profile_table(con, t) for t in inp.tables}
        results = run_rules(con, inp)
        issues = issue_log(results, inp, stewards)
        curated = sorted(t for t in inp.tables if t.startswith("curated."))
        certs = certify(con, curated, results, inp)
        meta_rows = write_quality(con, results, issues, certs, inp.as_of)
        email_rule = next(r for r in inp.rules if r.id == "DQ-02")
        crm_total, marketable = marketable_contacts(con, email_rule.pattern)
        consented = con.execute("SELECT count(*) FILTER (WHERE consent_marketing) "
                                "FROM staging.stg_crm_customers").fetchone()[0]
        dq06 = next(r for r in results if r.rule.id == "DQ-06")
        inherited_n = inherited_postal_defects(con, dq06.failed_keys,
                                               seeded.get("order_invalid_postal", []),
                                               seeded.get("ecom_invalid_postal", []))

    detection = evaluate_detection(results, seeded, inp.seeded_defects)
    fixable = consented - marketable
    failed_records = sum(r.failed for r in results if r.rule.type != "freshness")
    manual_hours = failed_records * inp.value.hours_manual_fix_per_issue
    by_dim = scorecard(results, lambda r: r.rule.dimension)
    by_dom = scorecard(results, lambda r: inp.tables[r.rule.table].domain)

    out_dir.mkdir(parents=True, exist_ok=True)
    issues_csv = out_dir / "dq_issues.csv"
    pd.DataFrame([{"issue_id": i.id, "rule_id": i.result.rule.id, "severity": i.severity,
                   "table": i.result.rule.table, "column": i.result.rule.column,
                   "record_key": k, "steward": i.steward, "status": i.status}
                  for i in issues for k in i.result.failed_keys]
                 ).to_csv(issues_csv, index=False, encoding="utf-8")
    outputs = {
        "chart": plot_rules(results, out_dir / CHART_NAME),
        "issues_csv": issues_csv,
        "profile": write_text(out_dir / "data_profile.md", render_template(
            TEMPLATES, "data_profile.md.j2", company=COMPANY, tables=list(profiles.items()),
            mixed=[p for ps in profiles.values() for p in ps if p.mixed_formats])),
        "scorecard": write_text(out_dir / "dq_scorecard.md", render_template(
            TEMPLATES, "dq_scorecard.md.j2", company=COMPANY, as_of=inp.as_of,
            results=results, meets=sum(r.meets_threshold for r in results), issues=issues,
            open_issues=sum(i.status == "abierta" for i in issues), certs=certs,
            certified=[c for c in certs if c.certified], chart_name=CHART_NAME,
            by_dimension=list(by_dim.iterrows()), by_domain=list(by_dom.iterrows()),
            domain_names=DOMAIN_NAMES, severity_labels=SEVERITY_LABELS,
            remediation_labels=REMEDIATION_LABELS,
            dispositions=[i for i in issues if i.disposition],
            blocking=inp.certification.max_severity_blocking, detection=detection,
            inherited={"order_invalid_postal": f"{inherited_n} pedidos son de clientes cuyo "
                       "código postal ya era inválido en el e-commerce: el defecto del maestro "
                       "de cliente se hereda en cada pedido. Se corrige en el cliente, no en el "
                       "pedido."},
            marketable=marketable, crm_total=crm_total, fixable=fixable,
            fixable_value=fixable * inp.value.contacts_marketing_value,
            manual_hours=manual_hours, manual_cost=manual_hours * inp.value.cost_per_hour)),
    }

    console.rule("[bold]Capítulo 8: Calidad de datos")
    console.print(f"{sum(r.meets_threshold for r in results)} de {len(results)} reglas cumplen "
                  f"su umbral · {len(issues)} incidencias · meta: "
                  f"{', '.join(f'{k} {v}' for k, v in meta_rows.items())}")
    for d in detection:
        extra = d.detected - d.true_positives
        console.print(f"  • {d.defect}: recall {d.recall:.0%} ({d.true_positives}/{d.seeded})"
                      + (f", {extra} fuera del solucionario" if extra else ""))
    console.print(f"    {inherited_n} de los pedidos con CP inválido fuera del solucionario "
                  "heredan el defecto de su cliente")
    for c in certs:
        mark = "[green]✓ certificado[/green]" if c.certified else "[red]✗[/red]"
        console.print(f"{c.table}: {mark} {'; '.join(c.reasons)}")
    console.print(f"Contactos aptos para marketing: {marketable}/{crm_total} "
                  f"(+{fixable} corrigiendo el email: "
                  f"{fmt_money(fixable * inp.value.contacts_marketing_value)}/año)")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

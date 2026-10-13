"""Capítulo 10: gestión de datos primarios (golden record de cliente).

Requiere `uv run dglab build`. Escribe en el warehouse el esquema `pdm` (hub de datos
primarios) y `curated.dim_customer`.
Uso: uv run python -m chapters.ch10_datos_primarios_mdm.run
"""

import re
from pathlib import Path

import pandas as pd
from rich.console import Console

from dglab import viz
from dglab.config import load_yaml
from dglab.paths import RAW_DIR, WAREHOUSE_DB
from dglab.reporting import fmt_money, fmt_pct, render_template, write_text
from dglab.synthetic import read_truth
from dglab.warehouse import connect

from .config import PdmConfig, ReferenceData
from .matching import cluster, evaluate, find_pairs
from .parties import load_parties
from .publish import publish
from .reference import enrich, hierarchy_counts, reference_table
from .survivorship import golden_records

CHAPTER_DIR = Path(__file__).parent
INPUTS = CHAPTER_DIR / "inputs"
TEMPLATES = CHAPTER_DIR / "templates"
CHART_NAME = "deduplication.png"
COMPANY = "NovaMercado"
CHECKS = {"Email válido": "email", "Teléfono válido": "phone",
          "Código postal válido": "postal_code"}


def plot_dedup(per_source: list[tuple[str, int]], golden: int, path: Path) -> Path:
    labels = [label for label, _ in per_source] + ["Total registros", "Clientes únicos"]
    values = [n for _, n in per_source] + [sum(n for _, n in per_source), golden]
    colors = [viz.SERIES[0]] * (len(per_source) + 1) + [viz.SERIES[1]]
    fig, ax = viz.new_figure(8, 4.2)
    bars = ax.bar(labels, values, color=colors, width=0.6, edgecolor=viz.SURFACE, linewidth=2)
    for bar, v in zip(bars, values, strict=True):
        ax.annotate(f"{v:,}".replace(",", "."), (bar.get_x() + bar.get_width() / 2, v),
                    xytext=(0, 4), textcoords="offset points", ha="center", fontsize=9,
                    color=viz.TEXT_SECONDARY)
    ax.set_ylabel("Registros", color=viz.TEXT_SECONDARY)
    viz.set_titles(ax, "Deduplicación de clientes",
                   "Registros de cada sistema frente a clientes únicos tras el PDM")
    return viz.save_figure(fig, path)


def _valid_share(series: pd.Series, pattern: str | None) -> float:
    if pattern is None:
        return float(series.notna().mean())
    regex = re.compile(pattern)
    return float(series.map(lambda v: isinstance(v, str) and bool(regex.fullmatch(v))).mean())


def main(out_dir: Path | None = None, db_path: Path = WAREHOUSE_DB,
         raw_dir: Path = RAW_DIR) -> dict[str, Path]:
    out_dir = out_dir or CHAPTER_DIR / "outputs"
    if not db_path.exists():
        raise FileNotFoundError(f"No existe {db_path}: ejecuta antes `uv run dglab build`")
    console = Console()
    cfg = PdmConfig.model_validate(load_yaml(INPUTS / "pdm.yaml"))
    ref = ReferenceData.model_validate(load_yaml(INPUTS / "reference_data.yaml"))
    links, _ = read_truth(raw_dir)
    person = links.set_index("source_id")["person_id"]

    with connect(db_path) as con:
        parties = load_parties(con, cfg)
        auto, review = find_pairs(parties, cfg.matching)
        roots = cluster(len(parties), auto)
        ids = {r: f"NM-C{i + 1:06d}" for i, r in enumerate(sorted(set(roots)))}
        parties["group"] = [ids[r] for r in roots]
        golden, attribution = golden_records(parties, cfg)
        golden = enrich(golden.rename(columns={"group": "golden_id"}), ref)
        truth = parties["source_id"].map(person)
        review_rows = pd.DataFrame([{
            "record_a": f"{parties.at[p.a, 'source']} {parties.at[p.a, 'source_id']}",
            "record_b": f"{parties.at[p.b, 'source']} {parties.at[p.b, 'source_id']}",
            "name_a": parties.at[p.a, "name_key"], "name_b": parties.at[p.b, "name_key"],
            "rule": p.rule, "score": round(p.score, 1), "status": "pendiente",
        } for p in review], columns=["record_a", "record_b", "name_a", "name_b", "rule",
                                     "score", "status"])
        xref = parties[["source", "source_id", "group"]].rename(columns={"group": "golden_id"})
        rows = publish(con, golden, xref, attribution, reference_table(ref), review_rows,
                       pd.Timestamp("2026-10-12").date())
        total_sales, identified_sales, omnichannel, buyers = con.execute("""
            SELECT (SELECT sum(amount) FROM staging.stg_pos_sales)
                 + (SELECT sum(amount) FROM staging.stg_ecom_orders
                    WHERE status NOT IN ('cancelado', 'devuelto')),
                   (SELECT sum(net_sales) FROM curated.dim_customer),
                   (SELECT count(*) FROM curated.dim_customer WHERE channels_purchased = 2),
                   (SELECT count(*) FROM curated.dim_customer WHERE channels_purchased > 0)
            """).fetchone()

    # Evaluación frente al solucionario (y con la revisión del steward simulada)
    score = evaluate(parties["group"], truth)
    confirmed = [p for p in review if truth[p.a] == truth[p.b]]
    score_reviewed = evaluate(pd.Series([ids[r] for r in cluster(len(parties),
                                                                 auto + confirmed)]), truth)

    per_source = [(cfg.sources[s].label, int((parties["source"] == s).sum()))
                  for s in cfg.sources]
    completeness = [(name, _valid_share(parties[col], cfg.attributes[col].validate_),
                     _valid_share(golden[col], cfg.attributes[col].validate_))
                    for name, col in CHECKS.items()]
    postal_re = re.compile(cfg.attributes["postal_code"].validate_)
    bad_postal_groups = set(parties.loc[parties["postal_code"].map(
        lambda v: isinstance(v, str) and not postal_re.fullmatch(v)), "group"])
    postal_fixed = int(golden[golden["golden_id"].isin(bad_postal_groups)]["province"]
                       .notna().sum())
    labels = {s: c.label for s, c in cfg.sources.items()}
    attr_summary = {}
    for attr, part in attribution.groupby("attribute"):
        shares = part["source"].value_counts(normalize=True)
        attr_summary[attr] = " · ".join(f"{labels.get(s, s)} {fmt_pct(v, 1)}"
                                        for s, v in shares.items())
    hier = hierarchy_counts(golden)
    regions = [(region, int(g["customers"].sum()),
                ", ".join(f"{r.community} ({r.customers})" for r in g.itertuples()))
               for region, g in hier.groupby("sales_region")]
    emailable = parties[parties["source"].isin(cfg.attributes["email"].sources)]
    dup_contacts = int(emailable["email"].notna().sum() - golden["email"].notna().sum())
    value = cfg.value
    campaign_saving = dup_contacts * value.campaigns_per_year * value.cost_per_contact
    hours_saving = value.hours_manual_dedup * value.automation_share * value.cost_per_hour

    out_dir.mkdir(parents=True, exist_ok=True)
    review_csv = out_dir / "review_queue.csv"
    review_rows.to_csv(review_csv, index=False, encoding="utf-8")
    review_view = [{"a_label": r.record_a, "b_label": r.record_b, "rule": r.rule,
                    "score": r.score, "same": truth[p.a] == truth[p.b]}
                   for r, p in zip(review_rows.itertuples(), review, strict=True)]
    outputs = {
        "chart": plot_dedup(per_source, len(golden), out_dir / CHART_NAME),
        "review_csv": review_csv,
        "report": write_text(out_dir / "primary_data.md", render_template(
            TEMPLATES, "primary_data.md.j2", company=COMPANY, cfg=cfg, ref=ref,
            records=len(parties), golden_count=len(golden), per_source=per_source,
            chart_name=CHART_NAME,
            rules=pd.Series([p.rule for p in auto]).value_counts().items(),
            review=review_view, score=score, score_reviewed=score_reviewed,
            source_labels=labels, attribution=attr_summary, completeness=completeness,
            postal_fixed=postal_fixed, regions=regions,
            invalid_postal=int(golden["province"].isna().sum()),
            multi_system=int((golden["source_records"] > 1).sum()),
            omnichannel=omnichannel, buyers=buyers, identified_sales=identified_sales,
            identified_share=identified_sales / total_sales,
            consented=int(golden["consent_marketing"].fillna(False).astype(bool).sum()),
            dup_contacts=dup_contacts, campaign_saving=campaign_saving,
            hours_saving=hours_saving)),
    }

    console.rule("[bold]Capítulo 10: Gestión de datos primarios")
    console.print(f"{len(parties)} registros → [bold]{len(golden)} clientes únicos[/bold] "
                  f"({len(auto)} emparejamientos automáticos, {len(review)} en revisión)")
    console.print(f"Frente al solucionario: precisión {score.precision:.2%}, recall "
                  f"{score.recall:.2%} (con revisión: {score_reviewed.recall:.2%})")
    console.print(f"Omnicanal: {omnichannel} de {buyers} clientes que compran · ventas "
                  f"identificadas {fmt_money(identified_sales)} "
                  f"({identified_sales / total_sales:.0%})")
    console.print("Warehouse: " + ", ".join(f"{k} {v}" for k, v in rows.items()))
    console.print(f"Valor estimado: {fmt_money(campaign_saving + hours_saving)}/año")
    for name, path in outputs.items():
        console.print(f"[green]✓[/green] {name}: {path.relative_to(out_dir.parent)}")
    return outputs


if __name__ == "__main__":
    main()

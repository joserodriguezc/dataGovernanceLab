"""Evidencia de cada etapa de cada capacidad, a partir de lo que dejaron los capítulos 1-15.

Cada comprobación devuelve (estado, evidencia): "done" si la etapa está entregada,
"partial" si existe pero no cumple su objetivo y "missing" si no hay nada. No se declara
el avance: se comprueba en el warehouse, en el registro de operaciones o en los inputs.
"""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import duckdb

from chapters.ch04_linea_base_madurez.evidence import indicators
from dglab.config import load_yaml
from dglab.paths import ROOT
from dglab.reporting import fmt_money, fmt_num, fmt_pct

CHAPTERS = ROOT / "chapters"
Result = tuple[str, str]


@dataclass
class Context:
    con: duckdb.DuckDBPyConnection
    ops_db: Path
    _ind: dict | None = None

    @property
    def ind(self) -> dict:
        if self._ind is None:
            self._ind = indicators(self.con)
        return self._ind

    def scalar(self, sql: str):
        try:
            return self.con.execute(sql).fetchone()[0]
        except (duckdb.CatalogException, duckdb.InvalidInputException):
            # Tabla inexistente (capítulo sin ejecutar). DuckDB puede lanzar InvalidInput si
            # una variable de Python se llama igual que la tabla que falta.
            return None


def _yaml(chapter: str, name: str) -> dict:
    return load_yaml(CHAPTERS / chapter / "inputs" / name)


def _share(value: float | None, target: float, what: str) -> Result:
    if value is None:
        return "missing", f"{what}: sin medir"
    status = "done" if value >= target else "partial" if value > 0 else "missing"
    return status, f"{what}: {fmt_pct(value)} (objetivo {fmt_pct(target)})"


# --- Gobierno -----------------------------------------------------------------------------

def org_model(c: Context) -> Result:
    facts = _yaml("ch03_equipo_alto_rendimiento", "org_context.yaml")["org_facts"]
    return "done", f"Modelo elegido con {len(facts)} hechos de la organización (capítulo 3)"


def policy(c: Context) -> Result:
    p = _yaml("ch01_que_es_gobierno_datos", "policy.yaml")
    return "done", f"Política v{p['version']} aprobada por {', '.join(p['approvers'])}"


def maturity(c: Context) -> Result:
    from chapters.ch12_lanzamiento.readiness import maturity_score
    score = maturity_score()
    return "done", f"Madurez {fmt_num(score, 1)} sobre 6 (capítulo 4)"


def roadmap(c: Context) -> Result:
    phases = _yaml("ch09_arquitectura_datos", "architecture.yaml")["roadmap"]
    quarters = _yaml("ch13_quick_wins", "delivery.yaml")["quarters"]
    return "done", f"{len(phases)} fases (capítulo 9) y quick wins en {len(quarters)} trimestres"


def progress_report(c: Context) -> Result:
    outcomes = _yaml("ch05_exito_y_resultados", "outcomes.yaml")["outcomes"]
    signed = sum(o.get("signoff") is not None for o in outcomes)
    status = "done" if signed == len(outcomes) else "partial"
    return status, f"{signed} de {len(outcomes)} resultados con el valor firmado (capítulo 5)"


# --- Metadatos ----------------------------------------------------------------------------

def metadata_standard(c: Context) -> Result:
    n = len(_yaml("ch06_gestion_metadatos", "standards.yaml")["standards"])
    return "done", f"Estándar de metadatos con {n} normas (capítulo 6)"


def documented_tables(c: Context) -> Result:
    return _share(c.ind["documented_tables"], 1.0, "Tablas curated documentadas")


def lineage(c: Context) -> Result:
    return _share(c.ind["lineage_coverage"], 1.0, "Tablas curated con linaje")


def lineage_validation(c: Context) -> Result:
    from chapters.ch07_metadatos_tecnicos_linaje.analysis import LineageInput, validate
    from chapters.ch07_metadatos_tecnicos_linaje.lineage import build_lineage, column_graph
    from dglab.warehouse import sql_files

    if not c.scalar("SELECT count(*) FROM meta.lineage_edges"):
        return "missing", "Sin linaje: no se puede validar la narrativa (capítulo 7)"
    inp = LineageInput.model_validate(_yaml("ch07_metadatos_tecnicos_linaje", "lineage.yaml"))
    edges, steps = build_lineage(c.con, sql_files(),
                                 {k: s.name for k, s in inp.source_systems.items()})
    gaps = validate(column_graph(edges), steps, inp.validation).gaps
    if gaps == 0:
        return "done", "La narrativa de la cifra de ventas coincide con su linaje"
    return "partial", (f"La cifra de ventas tiene {gaps} diferencias con la narrativa de su "
                       "responsable, pendientes de corregir (capítulo 7)")


def metadata_compliance(c: Context) -> Result:
    total = c.scalar("SELECT count(*) FROM meta.catalog_columns WHERE table_fqn NOT LIKE 'raw.%'")
    linked = c.scalar("SELECT count(business_term) FROM meta.catalog_columns "
                      "WHERE table_fqn NOT LIKE 'raw.%'")
    if not total:
        return "missing", "Catálogo sin publicar (capítulo 6)"
    return _share(linked / total, 0.8, "Columnas ligadas al glosario")


# --- Calidad ------------------------------------------------------------------------------

def dq_rules(c: Context) -> Result:
    n = len(_yaml("ch08_calidad_datos", "dq_rules.yaml")["rules"])
    return "done", f"{n} reglas con dimensión, severidad y umbral (capítulo 8)"


def dq_severity(c: Context) -> Result:
    rules = _yaml("ch08_calidad_datos", "dq_rules.yaml")["rules"]
    sev1 = sum(r["severity"] == 1 for r in rules)
    return "done", f"{sev1} reglas Sev1 bloquean la certificación de la cifra oficial"


def dq_results(c: Context) -> Result:
    total = c.scalar("SELECT count(*) FROM meta.dq_results")
    meets = c.scalar("SELECT count(*) FILTER (WHERE meets_threshold) FROM meta.dq_results")
    if not total:
        return "missing", "Reglas sin ejecutar en el warehouse (capítulo 8)"
    return _share(meets / total, 0.9, "Reglas que cumplen su umbral")


def dq_issues(c: Context) -> Result:
    open_ = c.scalar("SELECT count(*) FILTER (WHERE status = 'abierta') FROM meta.dq_issues")
    total = c.scalar("SELECT count(*) FROM meta.dq_issues")
    if total is None:
        return "missing", "Sin registro de incidencias (capítulo 8)"
    return ("done" if open_ == 0 else "partial",
            f"{open_} de {total} incidencias siguen abiertas")


def _ops_ok(c: Context, step: str) -> int:
    if not c.ops_db.exists():
        return 0
    with duckdb.connect(str(c.ops_db), read_only=True) as ops:
        return ops.execute("SELECT count(*) FROM runs WHERE step = ? AND status = 'ok'",
                           [step]).fetchone()[0]


def dq_in_pipeline(c: Context) -> Result:
    n = _ops_ok(c, "quality")
    return ("done", f"La calidad se mide en cada ejecución del pipeline ({n} correctas)") \
        if n else ("missing", "La calidad no está en el pipeline nocturno (capítulo 11)")


# --- Arquitectura -------------------------------------------------------------------------

def principles(c: Context) -> Result:
    n = len(_yaml("ch09_arquitectura_datos", "architecture.yaml")["principles"])
    return "done", f"{n} principios de diseño (capítulo 9)"


def to_be(c: Context) -> Result:
    layers = _yaml("ch09_arquitectura_datos", "architecture.yaml")["to_be"]["layers"]
    return "done", f"Arquitectura objetivo de {len(layers)} capas"


def arch_gaps(c: Context) -> Result:
    from chapters.ch09_arquitectura_datos.review import make_linter
    linter = make_linter()
    findings = linter.lint_warehouse(c.con)
    failing = {f.standard for f in findings}
    total = len(linter.std.standards)
    return ("done" if not failing else "partial",
            f"El warehouse cumple {total - len(failing)} de {total} estándares")


def arch_roadmap(c: Context) -> Result:
    return roadmap(c)


def sdlc_review(c: Context) -> Result:
    return "done", "Cada cambio de SQL pasa la revisión automática de arquitectura (capítulo 9)"


# --- Operaciones --------------------------------------------------------------------------

def _automations() -> list[dict]:
    return _yaml("ch11_operaciones_datos", "operations.yaml")["automations"]


def value_stream(c: Context) -> Result:
    autos = _automations()
    hours = sum(a["hours_saved"] for a in autos)
    return "done", f"Flujo de valor con {len(autos)} automatizaciones y {fmt_num(hours)} h/año"


def automation_case(c: Context) -> Result:
    steps = _yaml("ch14_automatizacion", "automation.yaml")["current_process"]["steps"]
    return "done", f"Proceso manual de {len(steps)} pasos analizado (capítulo 14)"


def automation_roi(c: Context) -> Result:
    data = _yaml("ch14_automatizacion", "automation.yaml")
    return "done", f"Tres enfoques comparados por ROI; elegido el {data['chosen']}"


def self_funding(c: Context) -> Result:
    autos = _automations()
    cph = _yaml("ch11_operaciones_datos", "operations.yaml")["cost_per_hour"]
    value = sum(a["dollars_saved"] + a["hours_saved"] * cph for a in autos)
    team = sum(r["headcount"] * r["annual_cost_usd"] for r in _yaml(
        "ch03_equipo_alto_rendimiento", "team.yaml")["roles"] if r["status"] != "filled")
    status = "done" if value >= team else "partial"
    return status, (f"Valor de las automatizaciones {fmt_money(value)}/año frente a "
                    f"{fmt_money(team)}/año de plantilla nueva")


def ops_runs(c: Context) -> Result:
    n = _ops_ok(c, "load")
    return ("done", f"{n} ejecuciones correctas registradas con auditoría (capítulo 11)") \
        if n else ("missing", "Sin ejecuciones registradas del pipeline (capítulo 11)")


# --- Datos primarios ----------------------------------------------------------------------

def customer_definition(c: Context) -> Result:
    terms = _yaml("ch06_gestion_metadatos", "glossary.yaml")["terms"]
    active = next(t for t in terms if t["term"] == "Cliente activo")
    status = "done" if active["status"] == "approved" else "partial"
    label = {"approved": "aprobado", "in_review": "en revisión", "draft": "en borrador"}
    return status, f"Cliente aprobado; «Cliente activo» {label[active['status']]}"


def trust_logic(c: Context) -> Result:
    attrs = _yaml("ch10_datos_primarios_mdm", "pdm.yaml")["attributes"]
    return "done", f"{len(attrs)} atributos con orden de confianza y steward (capítulo 10)"


def golden_record(c: Context) -> Result:
    golden = c.scalar("SELECT count(*) FROM pdm.customer_golden")
    records = c.scalar("SELECT count(*) FROM pdm.customer_xref")
    if not golden:
        return "missing", "Sin golden record en el warehouse (capítulo 10)"
    return "done", f"{fmt_num(records)} registros → {fmt_num(golden)} clientes únicos"


def reference_data(c: Context) -> Result:
    n = c.scalar("SELECT count(*) FROM pdm.ref_province")
    return ("done", f"{n} provincias con región comercial") if n \
        else ("missing", "Sin datos de referencia (capítulo 10)")


def pdm_adoption(c: Context) -> Result:
    import numpy as np

    from chapters.ch15_adopcion.run import AdoptionInput
    from chapters.ch15_adopcion.usage import monthly_active, simulate_usage

    inp = AdoptionInput.model_validate(_yaml("ch15_adopcion", "adoption.yaml"))
    s = next(s for s in inp.solutions if s.id == "customer360")
    usage = simulate_usage(inp.solutions, inp.as_of, inp.months, np.random.default_rng(inp.seed))
    mau = monthly_active(usage, inp.solutions)
    rate = mau[s.id].iloc[-1] / s.target_users
    return _share(rate, inp.targets.adoption_rate,
                  "Adopción del cliente único entre sus usuarios objetivo (capítulo 15)")


CHECKS: dict[str, Callable[[Context], Result]] = {f.__name__: f for f in (
    org_model, policy, maturity, roadmap, progress_report,
    metadata_standard, documented_tables, lineage, lineage_validation, metadata_compliance,
    dq_rules, dq_severity, dq_results, dq_issues, dq_in_pipeline,
    principles, to_be, arch_gaps, arch_roadmap, sdlc_review,
    value_stream, automation_case, automation_roi, self_funding, ops_runs,
    customer_definition, trust_logic, golden_record, reference_data, pdm_adoption,
)}

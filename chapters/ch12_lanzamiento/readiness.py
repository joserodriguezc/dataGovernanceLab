"""Evaluación de preparación para el lanzamiento: las 5 dimensiones del capítulo.

Cada dimensión va de 1 a 5 y se calcula con evidencia de los capítulos anteriores, con una
fórmula explícita. Si falta la evidencia (un capítulo sin ejecutar), cuenta como 0.
"""

from dataclasses import dataclass

import duckdb

from chapters.ch02_coalicion_defensores.sponsors import SponsorInput, assess_sponsors, recommend
from chapters.ch03_equipo_alto_rendimiento.team import TeamInput
from chapters.ch04_linea_base_madurez.analysis import company_score
from chapters.ch04_linea_base_madurez.evidence import indicators
from chapters.ch04_linea_base_madurez.model import AssessmentInput, MaturityModel
from chapters.ch04_linea_base_madurez.survey import participants, simulate_responses
from dglab.config import load_yaml
from dglab.paths import ROOT
from dglab.reporting import fmt_num, fmt_pct

CHAPTERS = ROOT / "chapters"


@dataclass(frozen=True)
class Dimension:
    id: str
    left: str
    right: str
    score: float  # 1-5
    evidence: list[str]


def _scale(share: float) -> float:
    """Proporción 0-1 a la escala 1-5."""
    return 1 + 4 * max(0.0, min(1.0, share))


def _scalar(con: duckdb.DuckDBPyConnection, sql: str) -> float | None:
    try:
        value = con.execute(sql).fetchone()[0]
    except duckdb.CatalogException:
        return None
    return None if value is None else float(value)


def maturity_score() -> float:
    """Madurez de la empresa (1-6) con el modelo y las respuestas del capítulo 4."""
    base = CHAPTERS / "ch04_linea_base_madurez" / "inputs"
    model = MaturityModel.model_validate(load_yaml(base / "maturity_model.yaml"))
    inp = AssessmentInput.model_validate(load_yaml(base / "assessment.yaml"))
    team = TeamInput.model_validate(load_yaml(CHAPTERS / "ch03_equipo_alto_rendimiento" /
                                              "inputs" / "team.yaml"))
    people = participants(inp, team.functional_roles)
    return company_score(simulate_responses(inp, model, people))


def assess(con: duckdb.DuckDBPyConnection, funding: bool, supporters: list[str]) -> list[Dimension]:
    team = TeamInput.model_validate(load_yaml(CHAPTERS / "ch03_equipo_alto_rendimiento" /
                                              "inputs" / "team.yaml"))
    sponsors = recommend(assess_sponsors(SponsorInput.model_validate(load_yaml(
        CHAPTERS / "ch02_coalicion_defensores" / "inputs" / "sponsors.yaml"))))

    # 1. Función de datos: plantilla cubierta del equipo diseñado en el capítulo 3
    planned = sum(r.headcount for r in team.roles)
    filled = sum(r.headcount for r in team.roles if r.status == "filled")

    # 2. Confianza: datasets curados certificados (capítulo 8)
    certified = _scalar(con, "SELECT avg(CASE WHEN certified THEN 1 ELSE 0 END) "
                             "FROM meta.catalog_tables WHERE layer = 'curated'") or 0.0

    # 3. Capacidades: documentación (6), linaje (7), calidad (8) y cliente único (10)
    ind = indicators(con)
    golden = _scalar(con, "SELECT count(*) FROM pdm.customer_golden") is not None
    caps = [ind["documented_tables"], ind["lineage_coverage"], ind["dq_pass_rate"],
            1.0 - ind["crm_duplicate_phones"] if golden else 0.0]

    # 4. Madurez (capítulo 4): escala 1-6 llevada a 1-5
    maturity = maturity_score()

    # 5. Liderazgo: CDAO en plantilla, sponsor, financiación y apoyo del comité de dirección
    cdao = any(r.id == "cdao" and r.status == "filled" for r in team.roles)
    checks = [cdao, bool(sponsors), funding, len(supporters) >= 2]

    return [
        Dimension("function", "Sin función de datos", "Función de datos consolidada",
                  _scale(filled / planned),
                  [f"{filled} de {planned} personas del equipo del capítulo 3 en plantilla"]),
        Dimension("trust", "Sin confianza en los datos", "Alta confianza en los datos",
                  _scale(certified),
                  [f"{fmt_pct(certified)} de los datasets curados certificados (capítulo 8)"]),
        Dimension("capabilities", "Sin capacidades", "Capacidades sólidas",
                  _scale(sum(caps) / len(caps)),
                  [f"Tablas documentadas {fmt_pct(ind['documented_tables'])}",
                   f"linaje {fmt_pct(ind['lineage_coverage'])}",
                   f"controles de calidad superados {fmt_pct(ind['dq_pass_rate'])}",
                   "golden record de cliente " + ("en producción" if golden else "pendiente")]),
        Dimension("maturity", "Madurez baja", "Madurez alta", 1 + 4 * (maturity - 1) / 5,
                  [f"{fmt_num(maturity, 1)} sobre 6 en la evaluación del capítulo 4"]),
        Dimension("leadership", "Sin líder de datos", "CDAO con poder y financiación",
                  _scale(sum(checks) / len(checks)),
                  [f"CDAO {'en plantilla' if cdao else 'sin cubrir'}",
                   "sponsor " + (f"recomendado: {sponsors[0].candidate.stakeholder.upper()}"
                                 if sponsors else "sin identificar"),
                   f"financiación {'aprobada' if funding else 'pendiente'}",
                   f"{len(supporters)} miembros del comité de dirección apoyan"]),
    ]


def launch_approach(dims: list[Dimension]) -> list[str]:
    """Recomendaciones según el perfil, empezando por la dimensión más débil."""
    advice = {
        "function": "Usa la falta de función central para pedir inversión: lanza con un equipo "
                    "pequeño y crece con cada entrega.",
        "trust": "Empieza por la métrica en la que la dirección no confía (la cifra de ventas): "
                 "es el caso de uso más convincente.",
        "capabilities": "Construye las capacidades a la vez que transformas: lanza con las que "
                        "ya funcionan y comunica el plan para el resto.",
        "maturity": "Usa la puntuación de madurez para que la dirección vea el estado real, sin "
                    "sesgos: es la línea base contra la que se medirá el avance.",
        "leadership": "Antes de un gran lanzamiento, gana apoyo con un proyecto más pequeño y "
                      "conversaciones uno a uno con cada ejecutivo.",
    }
    return [advice[d.id] for d in sorted(dims, key=lambda d: d.score) if d.score < 3.5]

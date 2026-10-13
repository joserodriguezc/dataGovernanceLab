"""Contenido del mensaje de lanzamiento y revisión del memo narrativo.

El memo se escribe en términos de negocio. Antes de publicarlo se revisa como pide el
capítulo: que un no especialista no encuentre jerga de datos y que no pase de unas 10
páginas.
"""

import re
from dataclasses import dataclass

import duckdb

from chapters.ch01_que_es_gobierno_datos.business_case import (
    BusinessCaseInput,
    evaluate_business_case,
)
from chapters.ch01_que_es_gobierno_datos.charter import DATA_SPEAK, ProgramInput
from chapters.ch01_que_es_gobierno_datos.equity import DataEquityInput, evaluate_equity
from chapters.ch02_coalicion_defensores.stakeholders import StakeholderInput
from chapters.ch05_exito_y_resultados.framework import OutcomeFramework
from chapters.ch09_arquitectura_datos.run import Architecture
from dglab.config import load_yaml
from dglab.paths import ROOT
from dglab.reporting import fmt_num, fmt_pct

CHAPTERS = ROOT / "chapters"


def _yaml(chapter: str, name: str) -> dict:
    return load_yaml(CHAPTERS / chapter / "inputs" / name)


@dataclass(frozen=True)
class Win:
    text: str
    evidence: str


def _scalar(con: duckdb.DuckDBPyConnection, sql: str):
    try:
        return con.execute(sql).fetchone()[0]
    except duckdb.CatalogException:
        return None


def delivered_wins(con: duckdb.DuckDBPyConnection) -> list[Win]:
    """Victorias ya entregadas, medidas en el warehouse (para anunciarlas en el lanzamiento)."""
    wins = []
    golden = _scalar(con, "SELECT count(*) FROM pdm.customer_golden")
    records = _scalar(con, "SELECT count(*) FROM pdm.customer_xref")
    if golden:
        wins.append(Win(f"Ya sabemos que nuestros {fmt_num(records)} registros de cliente son "
                        f"{fmt_num(golden)} personas: cada cliente cuenta una sola vez",
                        "Capítulo 10, cliente único"))
    documented = _scalar(con, "SELECT avg(CASE WHEN comment <> '' THEN 1 ELSE 0 END) "
                              "FROM duckdb_tables() WHERE schema_name = 'curated'")
    if documented:
        wins.append(Win(f"El {fmt_pct(documented)} de los datos que usan los informes tiene "
                        "una descripción y un responsable, y se puede buscar",
                        "Capítulo 6, catálogo"))
    lineage = _scalar(con, "SELECT count(DISTINCT target_table) FROM meta.lineage_edges "
                           "WHERE target_table LIKE 'curated.%'")
    if lineage:
        wins.append(Win("Sabemos de dónde sale cada cifra de ventas, y hemos descubierto que no "
                        "sale de donde creíamos", "Capítulo 7, validación del origen"))
    certified = _scalar(con, "SELECT count(*) FILTER (WHERE certified) FROM meta.catalog_tables")
    issues = _scalar(con, "SELECT count(*) FROM meta.dq_issues")
    if issues is not None:
        wins.append(Win(f"Cada carga revisa {_scalar(con, 'SELECT count(*) FROM meta.dq_results')}"
                        f" controles de calidad; {certified or 0} conjunto de datos ya es fuente "
                        "oficial certificada", "Capítulo 8, calidad y certificación"))
    return wins


def memo_context(con: duckdb.DuckDBPyConnection, maturity: float) -> dict:
    program = ProgramInput.model_validate(_yaml("ch01_que_es_gobierno_datos", "program.yaml"))
    bc = BusinessCaseInput.model_validate(_yaml("ch01_que_es_gobierno_datos",
                                                "business_case.yaml"))
    equity = evaluate_equity(DataEquityInput.model_validate(
        _yaml("ch01_que_es_gobierno_datos", "data_equity.yaml")))
    benefit = equity.annual_benefit(vetted_only=not bc.include_unvetted_benefits)
    option = next(r for r in evaluate_business_case(bc, benefit)
                  if r.option.id == bc.recommended_option)
    outcomes = OutcomeFramework.model_validate(_yaml("ch05_exito_y_resultados", "outcomes.yaml"))
    groups = {g.id: g.name for g in StakeholderInput.model_validate(
        _yaml("ch02_coalicion_defensores", "stakeholders.yaml")).groups}
    arch = Architecture.model_validate(_yaml("ch09_arquitectura_datos", "architecture.yaml"))
    stores = {s.id: s.name for s in arch.as_is.stores}
    return {
        "program": program, "bc": bc, "option": option, "benefit": benefit,
        "equity_now": equity.equity("current", vetted_only=True), "maturity": maturity,
        "outcomes": [(o, groups[o.stakeholder]) for o in outcomes.outcomes],
        "retired": [stores[s] for s in arch.to_be.retired],
        "kept": [s.name for s in arch.as_is.stores
                 if s.kind == "aplicación" and s.id not in arch.to_be.retired],
        "wins": delivered_wins(con),
    }


@dataclass(frozen=True)
class MemoReview:
    words: int
    max_words: int
    jargon: dict[str, int]

    @property
    def ok(self) -> bool:
        return self.words <= self.max_words and not self.jargon


def review_memo(text: str, max_words: int) -> MemoReview:
    jargon = {}
    for term in DATA_SPEAK:
        n = len(re.findall(rf"\b{re.escape(term)}\b", text, flags=re.IGNORECASE))
        if n:
            jargon[term] = n
    return MemoReview(len(re.findall(r"\w+", text)), max_words, jargon)

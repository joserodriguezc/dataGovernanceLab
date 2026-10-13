from datetime import date

import pandas as pd
import pytest
from pydantic import ValidationError

from chapters.ch03_equipo_alto_rendimiento.team import FunctionalRoles
from chapters.ch04_linea_base_madurez import run
from chapters.ch04_linea_base_madurez.analysis import (
    company_score,
    dimension_scores,
    group_themes,
    self_assessment_bias,
    unsupported_scores,
)
from chapters.ch04_linea_base_madurez.evidence import Cap, evidence_caps, indicators
from chapters.ch04_linea_base_madurez.model import AssessmentInput, Finding, Scope
from chapters.ch04_linea_base_madurez.survey import participants
from dglab.config import load_yaml
from dglab.warehouse import connect

INPUTS = run.INPUTS


def _responses(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["unit", "dimension", "self_score", "workshop_score"])


# --- Alcance y participantes -------------------------------------------------------------

def test_partial_scope_is_not_enterprise():
    scope = Scope(type="pilot", domains=["customer"], include_data_office=True)
    assert scope.units == ["customer", "data_office"]
    assert "supplier" in scope.missing_domains


def test_domains_without_stewards_fall_back_to_the_executive():
    inp = AssessmentInput.model_validate(load_yaml(INPUTS / "assessment.yaml"))
    roles = [FunctionalRoles(domain="customer", executive="CMO", business_stewards=["B"],
                             technical_stewards=["T"]),
             FunctionalRoles(domain="supplier", executive="Compras", business_stewards=[],
                             technical_stewards=[])]
    people = participants(inp, roles)
    customer = [p for p in people if p.unit == "customer"]
    supplier = [p for p in people if p.unit == "supplier"]
    assert [p.role for p in customer] == ["Steward de negocio", "Steward técnico"]
    assert supplier[0].name == "Compras" and supplier[0].fallback


def test_plan_must_follow_a_finding_theme():
    data = load_yaml(INPUTS / "assessment.yaml")
    data["plan"][0]["theme"] = "Tema inventado"
    with pytest.raises(ValidationError):
        AssessmentInput.model_validate(data)


# --- Análisis ----------------------------------------------------------------------------

def test_company_score_is_simple_average_of_units():
    r = _responses([("a", "x", 3, 2), ("a", "x", 3, 2), ("b", "x", 4, 4), ("a", "y", 1, 1),
                    ("b", "y", 1, 3)])
    assert dimension_scores(r).to_dict() == {"x": 3.0, "y": 2.0}
    assert company_score(r) == 2.5


def test_bias_flags_units_beyond_threshold():
    r = _responses([("a", "x", 4, 2), ("b", "x", 2, 2), ("c", "x", 1, 3)])
    biases = self_assessment_bias(r, threshold=0.75)
    assert [(b.unit, b.direction) for b in biases] == [("a", "se sobrevalora"),
                                                       ("c", "se infravalora")]


def test_evidence_caps_and_unsupported_scores():
    caps = evidence_caps({"documented_tables": 0.0, "lineage_coverage": 1.0,
                          "crm_duplicate_phones": 0.0, "dq_worst_check": 0.99})
    assert {c.dimension for c in caps} == {"metadata", "privacy_security"}
    flags = unsupported_scores(pd.Series({"metadata": 2.5, "privacy_security": 1.5}), caps)
    assert [f.cap.dimension for f in flags] == ["metadata"]
    assert isinstance(flags[0].cap, Cap)


def test_themes_sorted_by_priority_and_reach():
    f = [Finding(text="t", theme="B", dimension="x", domains=["a", "b"], root_cause="r",
                 priority=1),
         Finding(text="t", theme="A", dimension="x", domains=["a"], root_cause="r", priority=1),
         Finding(text="t", theme="C", dimension="y", domains=["a"], root_cause="r", priority=2)]
    assert [t.name for t in group_themes(f)] == ["B", "A", "C"]


def test_indicators_measure_seeded_defects(small_warehouse):
    with connect(small_warehouse, read_only=True) as con:
        ind = indicators(con)
    assert ind["documented_tables"] == 0.0
    assert ind["crm_duplicate_phones"] > 0.01  # los duplicados sembrados comparten teléfono
    assert 0.9 < ind["dq_pass_rate"] < 1.0


# --- Extremo a extremo -------------------------------------------------------------------

def test_run_generates_all_deliverables(tmp_path, small_warehouse):
    outputs = run.main(out_dir=tmp_path, db_path=small_warehouse)
    assert all(p.exists() and p.stat().st_size > 0 for p in outputs.values())
    responses = pd.read_csv(outputs["responses"])
    assert responses.self_score.between(1, 6).all()
    internal = outputs["internal"].read_text(encoding="utf-8")
    assert "Ventas | " in internal and "Se sobrevalora" in internal


def test_run_fails_clearly_without_warehouse(tmp_path):
    with pytest.raises(FileNotFoundError, match="dglab build"):
        run.main(out_dir=tmp_path, db_path=tmp_path / "no_existe.duckdb")


def test_start_date_is_a_date():
    inp = AssessmentInput.model_validate(load_yaml(INPUTS / "assessment.yaml"))
    assert isinstance(inp.start_date, date)

import copy

import duckdb
import pytest
from pydantic import ValidationError

from chapters.ch03_equipo_alto_rendimiento.team import FunctionalRoles
from chapters.ch13_quick_wins import run
from chapters.ch13_quick_wins.ownership import ownership_register
from chapters.ch13_quick_wins.quickwins import (
    Communication,
    Issue,
    Need,
    NeedsInput,
    Solution,
    fuzzy_rationalization,
    issue_matrix,
    measure,
    plan,
)
from dglab.config import load_yaml

RAW = load_yaml(run.INPUTS / "needs.yaml")


def _issue(impact="high", urgency="high", cost="low", **kw) -> Issue:
    base = dict(title="t", outcome="O1", measure="m", impact=impact, urgency=urgency,
                cost=cost, short_term="s", long_term="l", options=["a", "b", "c"],
                funding="cdao")
    return Issue(**(base | kw))


def test_score_and_quadrant():
    assert (_issue().score, _issue().quadrant) == (8, "Quick win")
    assert _issue(cost="high").quadrant == "Estratégico (largo plazo)"
    assert _issue(impact="low", cost="low").quadrant == "Relleno"
    assert _issue(impact="low", cost="high").quadrant == "Evitar"


def test_issue_needs_three_options():
    with pytest.raises(ValidationError):
        _issue(options=["a", "b"])


def test_needs_must_point_to_known_issues():
    data = copy.deepcopy(RAW)
    data["needs"][0]["issue"] = "inventado"
    with pytest.raises(ValidationError):
        NeedsInput.model_validate(data)


def test_matrix_and_fuzzy_rationalization():
    needs = [Need(group="Ventas", text="Varias versiones del mismo cliente", issue="x"),
             Need(group="Marketing", text="Varias versiones de un mismo cliente", issue="x"),
             Need(group="Tiendas", text="El cliente sale duplicado en la web", issue="x")]
    assert issue_matrix(needs) == {"x": {"Ventas", "Marketing", "Tiendas"}}
    check = fuzzy_rationalization(needs)
    assert (check.same_issue_pairs, check.found_by_fuzzy) == (3, 1)
    assert len(check.missed) == 2


def test_plan_respects_capacity():
    issues = {"a": _issue(cost="high"), "b": _issue(cost="medium"), "c": _issue(cost="low"),
              "d": _issue(cost="high", impact="low")}
    roadmap = plan(issues, ["T1", "T2"], capacity=3)
    assert roadmap["T1"] == ["c", "b"]  # mayor puntuación primero, hasta 3 unidades
    assert roadmap["T2"] == ["a"] and roadmap["Backlog"] == ["d"]


def test_measure_handles_missing_tables():
    con = duckdb.connect()
    assert measure(con, _issue(size_sql="SELECT 0.5", size_unit="pct")) == 0.5
    assert measure(con, _issue(size_sql="SELECT 1 FROM pdm.nada", size_unit="pct")) is None
    assert measure(con, _issue()) is None


def test_product_service_asset_and_communication():
    kinds = [Solution(name="p", continuous_support=True, continuous_delivery=True,
                      needs_features=True, monthly_users=1).kind,
             Solution(name="s", continuous_support=True, continuous_delivery=False,
                      needs_features=False, monthly_users=1).kind,
             Solution(name="a", continuous_support=False, continuous_delivery=False,
                      needs_features=False, monthly_users=1).kind]
    assert kinds == ["Producto", "Servicio", "Activo"]
    assert "sin comunicar" in Communication(win="w", impact="high", communicated=False).quadrant


def test_ownership_register_without_catalog():
    roles = [FunctionalRoles(domain="supplier", executive=None, business_stewards=[],
                             technical_stewards=[])]
    reg = ownership_register(duckdb.connect(), roles)
    assert reg.iloc[0]["huecos"] == "ejecutivo de dominio, steward de negocio, steward técnico"


def test_run(tmp_path, small_warehouse):
    outputs = run.main(out_dir=tmp_path, db_path=small_warehouse)
    report = outputs["report"].read_text(encoding="utf-8")
    assert "11 problemas comunes" in report and "sin medir" in report  # sin caps. 6-10

import copy
from datetime import date

import pytest
from pydantic import ValidationError

from chapters.ch05_exito_y_resultados import run
from chapters.ch05_exito_y_resultados.framework import (
    BusinessMetric,
    Capability,
    Deliverable,
    OutcomeFramework,
    warnings,
)
from chapters.ch05_exito_y_resultados.progress import (
    data_outcomes,
    expected_progress,
    outcome_status,
)
from dglab.config import load_yaml

RAW = load_yaml(run.INPUTS / "outcomes.yaml")


def _fw(mutate=None) -> OutcomeFramework:
    data = copy.deepcopy(RAW)
    if mutate:
        mutate(data)
    return OutcomeFramework.model_validate(data)


def _deliverable(**kw) -> Deliverable:
    base = dict(id="D", name="d", start=date(2027, 1, 1), due=date(2027, 1, 31), done=0,
                total=2, data_outcome="x")
    return Deliverable(**(base | kw))


# --- Validación estructural --------------------------------------------------------------

def test_inputs_are_valid():
    assert len(_fw().outcomes) == 3


def test_duplicate_ids_are_rejected():
    def dup(d):
        d["outcomes"][1]["capabilities"][0]["id"] = "C1"
    with pytest.raises(ValidationError, match="repetidos"):
        _fw(dup)


def test_capability_without_deliverables_is_rejected():
    with pytest.raises(ValidationError):
        Capability(id="C", name="c", why="w", deliverables=[])


def test_metric_needs_owner_and_improving_target():
    with pytest.raises(ValidationError):
        BusinessMetric(name="m", unit="hours", baseline=10, target=20, higher_is_better=False,
                       owner="CFO")
    with pytest.raises(ValidationError):
        BusinessMetric(name="m", unit="usd", baseline=1, target=2, higher_is_better=True,
                       owner="")


def test_deliverable_done_cannot_exceed_total():
    with pytest.raises(ValidationError):
        _deliverable(done=3, total=2)


def test_data_outcome_metric_must_be_delivered_by_someone():
    def orphan(d):
        d["data_outcome_metrics"]["Nadie lo entrega"] = {"indicator": "x", "target": 1,
                                                        "higher_is_better": True}
    with pytest.raises(ValidationError, match="nadie entrega"):
        _fw(orphan)


# --- Avisos ------------------------------------------------------------------------------

def test_warnings_flag_missing_signoff_and_components():
    w = warnings(_fw())
    assert any(x.startswith("O3:") and "firmado" in x for x in w)
    assert any(x.startswith("C2:") and "Cultura" in x for x in w)


# --- Progreso ----------------------------------------------------------------------------

def test_business_metric_progress_in_both_directions():
    up = BusinessMetric(name="m", unit="usd", baseline=100, target=300, actual=150,
                        higher_is_better=True, owner="o")
    down = BusinessMetric(name="m", unit="hours", baseline=100, target=20, actual=60,
                          higher_is_better=False, owner="o")
    assert up.progress == 0.25 and down.progress == 0.5


def test_expected_progress_is_linear():
    d = _deliverable(start=date(2027, 1, 1), due=date(2027, 1, 31))
    assert expected_progress(d, date(2026, 12, 1)) == 0
    assert expected_progress(d, date(2027, 1, 16)) == 0.5
    assert expected_progress(d, date(2027, 3, 1)) == 1


def test_status_red_when_overdue_yellow_when_behind():
    fw = _fw()
    o1, o2 = fw.outcomes[0], fw.outcomes[1]
    assert outcome_status(o1, fw.as_of) == "red"  # D5 vencido
    assert outcome_status(o2, fw.as_of) == "green"
    assert outcome_status(o2, date(2027, 5, 1)) == "yellow"  # D6 sin avance a mitad de plazo


def test_data_outcome_achieved_with_measurement():
    fw = _fw()
    o3 = fw.outcomes[2]
    statuses = {s.name: s for s in data_outcomes(o3, fw, {"lineage_coverage": 1.0,
                                                          "dq_pass_rate": 0.9})}
    assert statuses["Linaje documentado de todas las tablas curated"].achieved
    assert not statuses["Controles de calidad superados al 99 %"].achieved


# --- Extremo a extremo -------------------------------------------------------------------

def test_run_generates_all_deliverables(tmp_path, small_warehouse):
    outputs = run.main(out_dir=tmp_path, db_path=small_warehouse)
    assert all(p.exists() and p.stat().st_size > 0 for p in outputs.values())
    framework = outputs["framework"].read_text(encoding="utf-8")
    assert "US$ 1.512.500" in framework  # A1 + L3 del capítulo 1
    assert "QBR T1 2027" in outputs["value_map"].read_text(encoding="utf-8")

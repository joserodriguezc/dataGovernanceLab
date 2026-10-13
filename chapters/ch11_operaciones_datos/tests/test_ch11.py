import copy
import shutil
from datetime import date, datetime

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError

from chapters.ch11_operaciones_datos import run
from chapters.ch11_operaciones_datos.analysis import (
    hotspots,
    row_count_changes,
    sla_summary,
    value_stream,
)
from chapters.ch11_operaciones_datos.config import OpsConfig
from chapters.ch11_operaciones_datos.history import simulate_nights, simulate_tickets
from chapters.ch11_operaciones_datos.pipeline import ops_connect, run_pipeline
from dglab.config import load_yaml

RAW = load_yaml(run.INPUTS / "operations.yaml")
CFG = OpsConfig.model_validate(RAW)


def test_pipeline_must_be_in_dependency_order():
    data = copy.deepcopy(RAW)
    data["pipeline"].reverse()
    with pytest.raises(ValidationError, match="no le preceden"):
        OpsConfig.model_validate(data)


def test_failed_step_is_retried_and_dependents_are_skipped(tmp_path):
    calls = []

    def ok(db, raw, out):
        calls.append("ok")

    def broken(db, raw, out):
        calls.append("broken")
        raise RuntimeError("fichero de origen vacío")

    functions = {"load": ok, "pdm": broken, "metadata": ok, "lineage": ok, "quality": ok}
    ops_db = tmp_path / "ops.duckdb"
    run_id, status = run_pipeline(CFG.pipeline, tmp_path / "no.duckdb", tmp_path, ops_db,
                                  functions=functions)
    assert status == {"load": "ok", "pdm": "fallido", "metadata": "omitido",
                      "lineage": "omitido", "quality": "omitido"}
    assert calls == ["ok", "broken", "broken"]  # un reintento
    with ops_connect(ops_db) as ops:
        rows = ops.execute("SELECT step, attempt, status, error, executed_by FROM runs "
                           "WHERE run_id = ? ORDER BY started_at, attempt", [run_id]).fetchall()
    assert [(r[0], r[1], r[2]) for r in rows[:3]] == [("load", 1, "ok"), ("pdm", 1, "fallido"),
                                                     ("pdm", 2, "fallido")]
    assert "fichero de origen vacío" in rows[1][3] and rows[1][4]  # error y usuario auditados


def test_history_is_deterministic_and_respects_dependencies():
    a = simulate_nights(CFG, np.random.default_rng(1))
    b = simulate_nights(CFG, np.random.default_rng(1))
    pd.testing.assert_frame_equal(a, b)
    for _, night in a.groupby("night"):
        status = dict(zip(night.step, night.status, strict=True))
        for step in CFG.pipeline:
            if any(status[d] != "ok" for d in step.depends_on):
                assert status[step.id] == "omitido"


def test_process_failure_tickets_come_from_failed_nights():
    nights = simulate_nights(CFG, np.random.default_rng(3))
    tickets = simulate_tickets(CFG, nights, np.random.default_rng(3))
    assert (tickets.cause == "Fallos de proceso").sum() == (nights.status == "fallido").sum()


def test_sla_summary():
    nights = pd.DataFrame([
        {"night": date(2026, 1, 1), "step": s.id, "minutes": 10.0, "status": "ok",
         "finished_at": datetime(2026, 1, 1, 2, 0)} for s in CFG.pipeline] + [
        {"night": date(2026, 1, 2), "step": s.id, "minutes": 100.0, "status": "ok",
         "finished_at": datetime(2026, 1, 2, 4, 0)} for s in CFG.pipeline])
    s = sla_summary(CFG, nights)
    assert (s.nights, s.successful, s.on_time) == (2, 2, 1)
    assert s.by_step.loc["load", "over_sla"] == 0.5  # 100 min > 45 min una de dos noches


def test_hotspots_and_value_stream():
    tickets = pd.DataFrame({"ticket": list("abcd"), "system": ["POS", "POS", "CRM", "POS"],
                            "cause": ["Bugs", "Bugs", "Bugs", "Calidad de datos"],
                            "hours": [1.0, 2.0, 3.0, 4.0]})
    top = hotspots(tickets, top=1).iloc[0]
    assert (top.system, top.cause, top.tickets) == ("POS", "Bugs", 2)
    v = value_stream(CFG)
    assert v.automations == len(CFG.automations)
    assert v.dollars == sum(a.dollars_saved for a in CFG.automations) + v.hours * 45


def test_row_count_changes_flag_big_drops(tmp_path):
    with ops_connect(tmp_path / "ops.duckdb") as ops:
        ops.executemany("INSERT INTO row_counts VALUES (?, ?, ?, ?)", [
            ["r1", datetime(2026, 1, 1), "curated.a", 100], ["r1", datetime(2026, 1, 1),
                                                             "curated.b", 100],
            ["r2", datetime(2026, 1, 2), "curated.a", 105], ["r2", datetime(2026, 1, 2),
                                                             "curated.b", 50]])
        df = row_count_changes(ops, 0.2).set_index("table_fqn")
    assert not df.loc["curated.a", "alert"] and df.loc["curated.b", "alert"]


def test_run_executes_pipeline_and_reports(tmp_path, small_warehouse):
    db = tmp_path / "w.duckdb"
    shutil.copy(small_warehouse, db)
    outputs = run.main(out_dir=tmp_path / "out", db_path=db,
                       raw_dir=small_warehouse.parent / "raw", ops_db=tmp_path / "ops.duckdb")
    report = outputs["report"].read_text(encoding="utf-8")
    assert report.count("✅ Correcto") >= 5  # los 5 pasos de la ejecución real
    assert "curated.dim_customer" in report  # el pipeline incluye el golden record

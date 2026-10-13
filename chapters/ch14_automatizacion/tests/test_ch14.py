import shutil
from datetime import date

import duckdb
import numpy as np
import pandas as pd
import pytest

from chapters.ch10_datos_primarios_mdm import run as ch10
from chapters.ch14_automatizacion import run
from chapters.ch14_automatizacion.automation import complete_weeks, monitor
from chapters.ch14_automatizacion.enrichment import (
    Vendor,
    evaluate_vendor,
    pick_vendor,
    simulate_vendor,
)
from chapters.ch14_automatizacion.roi import Approach, CurrentProcess, approach_roi

PROCESS = CurrentProcess(frequency_per_year=52, people="p", steps=[
    {"step": "a", "minutes": 60, "manual": True, "error_prone": True},
    {"step": "b", "minutes": 120, "manual": True, "error_prone": False}])


def test_roi_formula():
    a = Approach(name="A", capabilities=[], automated_steps=[1], maintain_hours_per_year=4,
                 build_hours=100)
    r = approach_roi("A", a, PROCESS, cost_per_hour=50, horizon_years=3)
    assert r.hours_removed == 104                      # 2 h × 52 semanas
    assert r.annual_saving == (104 - 4) * 50
    assert r.one_time_cost == 5000 and r.roi == pytest.approx((15000 - 5000) / 5000)
    with pytest.raises(ValueError):
        approach_roi("X", a.model_copy(update={"automated_steps": [9]}), PROCESS, 50, 3)


def _report(values: list[float]) -> pd.DataFrame:
    weeks = pd.date_range("2026-01-05", periods=len(values), freq="7D").date
    return pd.DataFrame({"week": weeks, "region": "Norte", "net_sales": values, "lines": 1})


def test_volume_alert_only_for_anomalous_drops():
    con = duckdb.connect()
    normal = [100, 105, 95, 102, 98, 101, 99, 103, 97, 100]
    assert not monitor(con, _report([0] + normal + [96, 0]), 8, 2, 1, True)
    alerts = monitor(con, _report([0] + normal + [20, 100, 0]), 8, 2, 1, True)
    assert [(a.kind, a.region) for a in alerts] == [("Caída de volumen anómala", "Norte")]


def test_complete_weeks_drops_first_and_last():
    assert len(complete_weeks(_report([1, 2, 3, 4]))) == 2


def test_vendor_evaluation_penalises_wrong_answers():
    orders = pd.DataFrame({"true_postal": [f"28{i:03d}" for i in range(1000)]})
    sloppy = Vendor(name="s", coverage=1.0, accuracy=0.6, price=0.01)
    careful = Vendor(name="c", coverage=0.8, accuracy=1.0, price=0.03)
    rng = np.random.default_rng(0)
    results = [evaluate_vendor(orders, simulate_vendor(orders, v, rng), v)
               for v in (sloppy, careful)]
    assert results[1].wrong == 0 and results[0].wrong > 300
    assert pick_vendor(results).vendor.name == "c"


def test_run_reconciles_with_official_figure(tmp_path, small_warehouse):
    db = tmp_path / "w.duckdb"
    shutil.copy(small_warehouse, db)
    raw = small_warehouse.parent / "raw"
    with pytest.raises(RuntimeError, match="capítulo 10"):
        run.main(out_dir=tmp_path / "a", db_path=db, raw_dir=raw)
    ch10.main(out_dir=tmp_path / "ch10", db_path=db, raw_dir=raw)
    outputs = run.main(out_dir=tmp_path / "b", db_path=db, raw_dir=raw)
    report = outputs["report"].read_text(encoding="utf-8")
    assert "| Diferencia con la cifra oficial de ventas | No cuadra | US$ 0,00 |" in report
    weekly = pd.read_csv(outputs["weekly"])
    assert weekly["week"].min() >= str(date(2024, 12, 30))

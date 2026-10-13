from datetime import date

import numpy as np
import pandas as pd
import pytest

from chapters.ch15_adopcion import run
from chapters.ch15_adopcion.diagnosis import adoption_cost, diagnose
from chapters.ch15_adopcion.usage import (
    Solution,
    adoption_by_department,
    monthly_active,
    retention,
    simulate_usage,
)


def _solution(**sim) -> Solution:
    return Solution(id="s", name="S", go_live=date(2026, 7, 1), build_cost=300, annual_run_cost=100,
                    target={"Ventas": 100, "Datos": 10},
                    simulation={"share": 0.5, "monthly_active": 1.0, "churn": 0.0} | sim,
                    old_way={"name": "hoja", "hours_per_user_month": 2})


def test_simulation_respects_share_and_go_live():
    s = _solution(share=0.5)
    usage = simulate_usage([s], date(2026, 12, 31), 12, np.random.default_rng(1))
    assert usage["month"].min() == "2026-07"
    adopters = usage["user"].nunique()
    assert 40 < adopters < 70  # ~ 50 % de 110


def test_data_team_only_adoption_and_churn():
    s = _solution(share=0.0, data_team_share=1.0, data_team_churn=0.0)
    usage = simulate_usage([s], date(2026, 12, 31), 6, np.random.default_rng(0))
    assert set(usage["department"]) == {"Datos"}
    by_dept = adoption_by_department(usage, s, "2026-12")
    assert by_dept == {"Ventas": 0.0, "Datos": 1.0}


def test_retention_and_mau():
    usage = pd.DataFrame({"solution": "s", "department": "Ventas",
                          "user": ["a", "b", "a", "c"],
                          "month": ["2026-07", "2026-07", "2026-08", "2026-08"]})
    assert retention(usage, "s") == 0.5
    late = _solution().model_copy(update={"go_live": date(2026, 8, 1)})
    assert np.isnan(monthly_active(usage, [late]).loc["2026-07", "s"])


def test_adoption_cost():
    cost = adoption_cost(_solution(), rate=0.25, cost_per_hour=10)
    assert cost.unused_investment == pytest.approx((100 + 100) * 0.75)
    assert cost.duplicated_hours == pytest.approx(110 * 0.75 * 2 * 12)


def test_diagnosis_groups_weak_scores_by_cause():
    scores = {"usability": 2, "relevance": 4, "data_trust": 4, "workflow_fit": 4,
              "leadership_use": 1.5, "training": 4, "change_comms": 4, "leader_listens": 4}
    causes = {d.cause: [w[0] for w in d.weak] for d in diagnose(scores, 3)}
    assert causes == {"solution": ["usability"], "company": ["leadership_use"]}


def test_run_flags_the_failed_launch(tmp_path):
    outputs = run.main(out_dir=tmp_path)
    report = outputs["report"].read_text(encoding="utf-8")
    assert "### Plataforma de visualización corporativa" in report  # diagnóstico del fallo
    assert report.count("✅ Adoptada") == 3

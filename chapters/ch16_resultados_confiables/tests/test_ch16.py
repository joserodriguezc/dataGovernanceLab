import shutil
from datetime import date

import duckdb
import pytest

from chapters.ch16_resultados_confiables import run
from chapters.ch16_resultados_confiables.evidence import CHECKS, Context, _share
from chapters.ch16_resultados_confiables.results import Commitment, Variance, status_counts

VAR = Variance(why="w", plan="p", owner="o", new_date=date(2027, 3, 1), adjustment="a")


def _c(met=False, overdue=False, variance=None) -> Commitment:
    return Commitment("O1", "n", "t", "m", met, date(2027, 1, 1), overdue, variance)


@pytest.mark.parametrize(("c", "status", "message"), [
    (_c(met=True), "met", False),
    (_c(), "on_track", False),
    (_c(variance=VAR), "at_risk", True),
    (_c(overdue=True, variance=VAR), "late", True),
    (_c(overdue=True), "late_unexplained", True),
])
def test_commitment_status(c, status, message):
    assert (c.status, c.needs_message) == (status, message)


def test_status_counts():
    counts = status_counts([_c(met=True), _c(met=True), _c(overdue=True)])
    assert counts["met"] == 2 and counts["late_unexplained"] == 1


def test_share_levels():
    assert _share(1.0, 1.0, "x")[0] == "done"
    assert _share(0.5, 1.0, "x")[0] == "partial"
    assert _share(0.0, 1.0, "x")[0] == "missing"
    assert _share(None, 1.0, "x")[0] == "missing"


def test_every_configured_check_exists():
    from dglab.config import load_yaml
    review = load_yaml(run.INPUTS / "review.yaml")
    used = {st["check"] for cap in review["capabilities"] for st in cap["stages"].values()}
    assert used <= set(CHECKS)


def test_evidence_without_later_chapters(tmp_path, small_warehouse):
    with duckdb.connect(str(small_warehouse), read_only=True) as con:
        ctx = Context(con, tmp_path / "no_ops.duckdb")
        assert CHECKS["golden_record"](ctx)[0] == "missing"
        assert CHECKS["ops_runs"](ctx)[0] == "missing"
        assert CHECKS["documented_tables"](ctx)[0] == "missing"
        assert CHECKS["policy"](ctx)[0] == "done"


def test_run_builds_html(tmp_path, small_warehouse):
    db = tmp_path / "w.duckdb"
    shutil.copy(small_warehouse, db)
    outputs = run.main(out_dir=tmp_path / "out", db_path=db, ops_db=tmp_path / "ops.duckdb")
    html = outputs["report"].read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>") and "data:image/png;base64," in html
    assert "Revisión de capacidades de NovaMercado" in html

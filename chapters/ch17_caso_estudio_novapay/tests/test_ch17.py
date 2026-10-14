import duckdb
import pandas as pd
import pytest

from chapters.ch03_equipo_alto_rendimiento.raci import RaciInput
from chapters.ch17_caso_estudio_novapay import run
from chapters.ch17_caso_estudio_novapay.case import segregation
from chapters.ch17_caso_estudio_novapay.data import Generation, generate, spanish_text
from chapters.ch17_caso_estudio_novapay.warehouse import build, manual_report, true_report
from dglab.config import load_yaml

CFG = load_yaml(run.INPUTS / "novapay.yaml")
ROLES = {"a": "Ana", "b": "Bea"}


@pytest.fixture(scope="module")
def small():
    g = Generation.model_validate({**CFG["generation"], "days": 20, "customers": 50})
    return g, generate(g)


def test_spanish_text():
    assert spanish_text(1234567.891) == "1.234.567,89"


def test_segregation_detects_overlap():
    acts = [{"name": "P", "A": "a", "R": ["a"]}, {"name": "V", "A": "a", "R": ["b"]}]
    s = segregation(RaciInput(roles=ROLES, activities=acts), "P", "V")
    assert not s.ok and s.overlap == ["Ana"]


def test_segregation_ok():
    acts = [{"name": "P", "A": "a", "R": ["a"]}, {"name": "V", "A": "b", "R": ["b"]}]
    assert segregation(RaciInput(roles=ROLES, activities=acts), "P", "V").ok


def test_yaml_raci_before_and_after():
    acts = (CFG["prepare_activity"], CFG["review_activity"])
    before = segregation(RaciInput(roles=CFG["raci_roles"], activities=CFG["raci_before"]), *acts)
    after = segregation(RaciInput(roles=CFG["raci_roles"], activities=CFG["raci_after"]), *acts)
    assert not before.ok and after.ok


def test_defects_are_seeded(small):
    _, data = small
    s = data.submissions
    assert s.row_id.str.startswith("D").any()
    assert s.amount.isna().any()
    assert s.amount.str.contains(",", na=False).any()
    assert s.amount.str.startswith("-", na=False).any()


def test_curated_matches_truth_on_complete_days(small, tmp_path):
    g, data = small
    db = tmp_path / "np.duckdb"
    build(db, data, {u: x.side for u, x in g.units.items()})
    with duckdb.connect(str(db)) as con:
        curated = con.execute("SELECT * FROM curated.fct_liquidity_report ORDER BY 1").df()
        manual = manual_report(con)
    truth = true_report(data.truth)
    for df in (curated, manual, truth):
        df["report_date"] = pd.to_datetime(df["report_date"])
    m = truth.merge(curated, on="report_date", suffixes=("_true", ""))
    done = m[m.complete]
    assert len(done) > 0
    assert (done.liquidity_ratio - done.liquidity_ratio_true).abs().max() < 1e-9
    assert m[~m.complete].liquidity_ratio.isna().all()
    # La hoja a mano se equivoca
    mm = truth.merge(manual, on="report_date", suffixes=("_true", "_manual"))
    assert (mm.liquidity_ratio_manual - mm.liquidity_ratio_true).abs().mean() > 0.05


def test_main_end_to_end(tmp_path):
    outputs = run.main(out_dir=tmp_path / "out", db_path=tmp_path / "novapay.duckdb")
    assert all(p.exists() for p in outputs.values())
    case = outputs["case"].read_text(encoding="utf-8")
    assert "Dato financiero personal - IBAN" in case
    assert "⬅️ aprobada" in case
    regulator = outputs["regulator"].read_text(encoding="utf-8")
    assert "{" not in regulator and "linaje" not in regulator.lower()

import shutil

import duckdb
import pytest

from chapters.ch10_datos_primarios_mdm import run as ch10
from chapters.ch12_lanzamiento import run
from chapters.ch12_lanzamiento.messaging import delivered_wins, review_memo
from chapters.ch12_lanzamiento.readiness import Dimension, _scale, assess, launch_approach


def test_scale_maps_share_to_1_5():
    assert (_scale(0), _scale(0.5), _scale(1), _scale(2)) == (1, 3, 5, 5)


def test_launch_approach_starts_with_weakest_dimension():
    dims = [Dimension("trust", "", "", 1.5, []), Dimension("maturity", "", "", 2.5, []),
            Dimension("leadership", "", "", 4.5, [])]
    advice = launch_approach(dims)
    assert len(advice) == 2 and "cifra de ventas" in advice[0]


def test_memo_review_flags_jargon_and_length():
    review = review_memo("Lanzamos un data lake con su linaje y metadatos de PII.", 5)
    assert set(review.jargon) == {"data lake", "linaje", "metadatos", "pii"}
    assert review.words > 5 and not review.ok
    assert review_memo("Decidimos con cifras fiables.", 100).ok


def test_no_wins_before_the_capabilities_exist():
    assert delivered_wins(duckdb.connect()) == []


@pytest.fixture
def warehouse_with_pdm(small_warehouse, tmp_path):
    db = tmp_path / "w.duckdb"
    shutil.copy(small_warehouse, db)
    ch10.main(out_dir=tmp_path / "ch10", db_path=db, raw_dir=small_warehouse.parent / "raw")
    return db


def test_readiness_uses_the_evidence(warehouse_with_pdm):
    with duckdb.connect(str(warehouse_with_pdm), read_only=True) as con:
        dims = {d.id: d for d in assess(con, funding=True, supporters=["CMO", "CFO"])}
    assert dims["leadership"].score == 5  # CDAO, sponsor, financiación y 2 apoyos
    assert dims["trust"].score == 1       # sin capítulo 8 no hay nada certificado
    assert "en producción" in " ".join(dims["capabilities"].evidence)


def test_run_produces_memo_without_jargon(tmp_path, warehouse_with_pdm):
    outputs = run.main(out_dir=tmp_path / "out", db_path=warehouse_with_pdm)
    plan = outputs["plan"].read_text(encoding="utf-8")
    memo = outputs["memo"].read_text(encoding="utf-8")
    assert "Sin jerga de datos" in plan
    assert "registros de cliente son" in memo  # victoria entregada por el capítulo 10

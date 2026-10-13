import duckdb
import pytest
from typer.testing import CliRunner

from chapters.ch09_arquitectura_datos import review, run
from chapters.ch09_arquitectura_datos.lint import Linter
from chapters.ch09_arquitectura_datos.review import make_linter

SCHEMA = {
    "raw": {"crm_customers": {"customer_id": "VARCHAR", "email": "VARCHAR", "phone": "VARCHAR"}},
    "staging": {"stg_pos_sales": {"line_id": "VARCHAR", "amount": "DOUBLE"},
                "stg_crm_customers": {"customer_id": "VARCHAR", "email": "VARCHAR"}},
}


@pytest.fixture(scope="module")
def linter() -> Linter:
    return make_linter()


def _standards(findings) -> list[str]:
    return sorted({f.standard for f in findings})


def test_good_sql_passes(linter):
    sql = ("CREATE TABLE curated.fct_x AS SELECT line_id, amount AS net_amount "
           "FROM staging.stg_pos_sales")
    assert linter.lint_sql(sql, SCHEMA) == []


@pytest.mark.parametrize(("sql", "expected"), [
    ("CREATE TABLE curated.report AS SELECT line_id FROM staging.stg_pos_sales", ["ARQ-01"]),
    ("CREATE TABLE curated.fct_x AS SELECT * FROM staging.stg_pos_sales", ["ARQ-04"]),
    ("CREATE TABLE curated.fct_x AS SELECT customer_id FROM raw.crm_customers", ["ARQ-03"]),
    ("CREATE TABLE staging.stg_x AS SELECT line_id FROM staging.stg_pos_sales", ["ARQ-03"]),
    ("CREATE TABLE curated.fct_x AS SELECT line_id AS lineId FROM staging.stg_pos_sales",
     ["ARQ-02"]),
    ("CREATE TABLE curated.dim_x AS SELECT customer_id, email FROM staging.stg_crm_customers",
     ["ARQ-09"]),
])
def test_each_standard_is_detected(linter, sql, expected):
    assert _standards(linter.lint_sql(sql, SCHEMA)) == expected


def test_select_star_with_pii_is_caught_after_expansion(linter):
    sql = "CREATE TABLE curated.dim_x AS SELECT * FROM staging.stg_crm_customers"
    assert "ARQ-09" in _standards(linter.lint_sql(sql, SCHEMA))


def test_warehouse_lint_types_keys_and_pii():
    con = duckdb.connect()
    for s in ("raw", "staging", "curated"):
        con.execute(f"CREATE SCHEMA {s}")
    con.execute("CREATE TABLE staging.stg_pos_sales AS SELECT * FROM (VALUES "
                "('a', 1.5::DOUBLE, '2025-01-01'), ('a', 2.0::DOUBLE, NULL)) "
                "AS v(line_id, amount, sale_date)")
    con.execute("CREATE TABLE staging.stg_crm_customers AS SELECT 'c' AS customer_id, "
                "'x@y.es' AS email")
    con.execute("CREATE TABLE staging.stg_ecom_customers AS SELECT 'e' AS ecom_user_id, "
                "'x@y.es' AS email")
    con.execute("CREATE TABLE curated.fct_y AS SELECT 'a' AS id")  # sin documentar
    linter = make_linter()
    linter.std.keys = {"staging.stg_pos_sales": "line_id"}
    found = {(f.standard, f.target) for f in linter.lint_warehouse(con)}
    assert ("ARQ-06", "staging.stg_pos_sales.amount") in found
    assert ("ARQ-05", "staging.stg_pos_sales.sale_date") in found
    assert ("ARQ-07", "staging.stg_pos_sales") in found
    assert ("ARQ-08", "curated.fct_y") in found
    assert ("ARQ-10", "PII directa - email") in found
    assert linter.pii_places["PII directa - email"] == {"staging.stg_crm_customers",
                                                        "staging.stg_ecom_customers"}


def test_review_cli_rejects_the_proposal(small_warehouse):
    proposal = run.INPUTS / "proposals" / "20_curated_customer_report.sql"
    result = CliRunner().invoke(review.app, [str(proposal), "--db", str(small_warehouse)])
    assert result.exit_code == 1
    for sid in ("ARQ-01", "ARQ-02", "ARQ-03", "ARQ-04", "ARQ-09"):
        assert sid in result.output


def test_run_generates_report(tmp_path, small_warehouse):
    outputs = run.main(out_dir=tmp_path, db_path=small_warehouse)
    text = outputs["architecture"].read_text(encoding="utf-8")
    assert "| Flujos punto a punto | 17 | 8 |" in text
    assert "ARQ-06" in text and "sin medir" in text  # sin los capítulos 6-8

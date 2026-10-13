import re

import numpy as np
import pandas as pd
import pytest

from dglab.synthetic import Scale, SyntheticConfig, generate, read_raw, read_truth, write_dataset
from dglab.synthetic.noise import phone_format, strip_accents, typo
from dglab.warehouse import build_warehouse, connect

SMALL = SyntheticConfig(scale=Scale(persons=300, products=60, suppliers=20, stores=5,
                                    pos_lines=2000, ecom_lines=800))


@pytest.fixture(scope="module")
def ds():
    return generate(SMALL)


def _ids(ds, table: str, key: str, ids: list[str]) -> pd.DataFrame:
    df = ds.tables[table]
    return df[df[key].isin(ids)]


def test_same_seed_same_data(ds):
    again = generate(SMALL)
    for name, df in ds.tables.items():
        pd.testing.assert_frame_equal(df, again.tables[name])
    assert ds.defects == again.defects


def test_different_seed_different_data(ds):
    other = generate(SyntheticConfig(seed=7, scale=SMALL.scale))
    assert not ds.tables["crm_customers"].equals(other.tables["crm_customers"])


def test_defect_counts_follow_rates(ds):
    rates = SMALL.defects
    assert len(ds.defects["pos_negative_price"]) == round(SMALL.scale.pos_lines *
                                                          rates.pos_negative_price)
    assert len(ds.defects["product_missing_category"]) == round(
        SMALL.scale.products * rates.product_missing_category)
    n_ecom = len(ds.tables["ecom_customers"])
    assert len(ds.defects["ecom_bad_date_format"]) == round(n_ecom * rates.ecom_bad_date_format)


def test_seeded_defects_are_really_in_the_data(ds):
    d = ds.defects
    assert _ids(ds, "crm_customers", "customer_id", d["crm_null_email"]).email.isna().all()
    assert (_ids(ds, "pos_sales", "line_id", d["pos_negative_price"]).unit_price < 0).all()
    assert _ids(ds, "erp_products", "sku", d["product_missing_category"]).category.isna().all()
    assert _ids(ds, "erp_suppliers", "supplier_id",
                d["supplier_missing_contact"]).contact_email.isna().all()
    bad_dates = _ids(ds, "ecom_customers", "ecom_user_id", d["ecom_bad_date_format"])
    assert bad_dates.created_at.str.fullmatch(r"\d{2}/\d{2}/\d{4}").all()
    bad_postal = _ids(ds, "ecom_customers", "ecom_user_id", d["ecom_invalid_postal"])
    assert not bad_postal.postal_code.str.fullmatch(r"\d{5}").any()


def test_clean_records_have_no_defects(ds):
    d = ds.defects
    sales = ds.tables["pos_sales"]
    assert (sales[~sales.line_id.isin(d["pos_negative_price"])].unit_price > 0).all()
    crm = ds.tables["crm_customers"]
    assert crm[~crm.customer_id.isin(d["crm_null_email"])].email.notna().all()


def test_crm_duplicates_point_to_the_same_person(ds):
    links = ds.customer_links.set_index("source_id").person_id
    dupes = ds.defects["crm_duplicates"]
    assert len(dupes) % 2 == 0
    persons = links.loc[dupes]
    assert persons.value_counts().ge(2).all()


def test_every_customer_record_is_linked_to_a_person(ds):
    linked = set(ds.customer_links.source_id)
    for table, key in [("crm_customers", "customer_id"), ("ecom_customers", "ecom_user_id"),
                       ("pos_loyalty_cards", "card_id")]:
        assert set(ds.tables[table][key]) <= linked


def test_orders_have_a_single_user_per_order(ds):
    assert ds.tables["ecom_orders"].groupby("order_id").ecom_user_id.nunique().eq(1).all()


def test_noise_helpers():
    assert strip_accents("José Núñez") == "Jose Nunez"
    assert phone_format("612345678", "international") == "+34 612 345 678"
    assert phone_format("612345678", "dashes") == "612-345-678"
    assert sorted(typo("Carmen", np.random.default_rng(0))) == sorted("Carmen")


def test_write_read_and_build_warehouse(ds, tmp_path):
    raw_dir = tmp_path / "raw"
    write_dataset(ds, raw_dir)
    assert read_raw("crm_customers", raw_dir).shape == ds.tables["crm_customers"].shape
    links, defects = read_truth(raw_dir)
    assert len(links) == len(ds.customer_links) and defects == ds.defects

    db = tmp_path / "test.duckdb"
    counts = build_warehouse(db, raw_dir)
    assert counts["raw.pos_sales"] == SMALL.scale.pos_lines
    assert counts["curated.fct_sales"] == SMALL.scale.pos_lines + SMALL.scale.ecom_lines
    with connect(db, read_only=True) as con:
        unparsed = con.execute("SELECT count(*) FROM staging.stg_ecom_customers "
                               "WHERE created_at IS NULL").fetchone()[0]
        phones = con.execute("SELECT phone FROM staging.stg_crm_customers "
                             "WHERE phone IS NOT NULL").fetchall()
    assert unparsed == 0  # las dos variantes de fecha se interpretan
    assert all(re.fullmatch(r"\d{9}", p) for (p,) in phones)

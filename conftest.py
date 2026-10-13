"""Fixtures compartidos por los tests del paquete y de los capítulos."""

import pytest

from dglab.synthetic import Scale, SyntheticConfig, generate, write_dataset
from dglab.warehouse import build_warehouse

SMALL_SCALE = Scale(persons=300, products=60, suppliers=20, stores=5, pos_lines=2000,
                    ecom_lines=800)


@pytest.fixture(scope="session")
def small_warehouse(tmp_path_factory):
    """Warehouse DuckDB pequeño y determinista, construido una sola vez por sesión."""
    root = tmp_path_factory.mktemp("warehouse")
    write_dataset(generate(SyntheticConfig(scale=SMALL_SCALE)), root / "raw")
    db = root / "novamercado.duckdb"
    build_warehouse(db, root / "raw")
    return db

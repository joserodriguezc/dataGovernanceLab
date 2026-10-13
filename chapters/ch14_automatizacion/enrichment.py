"""Enriquecimiento de terceros: evaluar proveedores antes de comprar.

Los proveedores se simulan: para cada código postal de envío inválido devuelven un código
con una cobertura y una exactitud dadas. Lo importante es la evaluación, que el libro pide
hacer antes de comprometerse: se compara lo que devuelve cada proveedor con el código
postal real de la persona (solucionario de la Fase 0) y se calcula el coste por registro
corregido de verdad. Un proveedor que devuelve datos erróneos empeora la calidad.
"""

from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class Vendor(BaseModel):
    name: str
    coverage: float = Field(ge=0, le=1)
    accuracy: float = Field(ge=0, le=1)
    price: float = Field(ge=0)


def invalid_orders_with_truth(con: duckdb.DuckDBPyConnection,
                              links: pd.DataFrame) -> pd.DataFrame:
    """Pedidos con código postal de envío inválido y el código real de la persona."""
    orders = con.execute("""
        SELECT order_line_id, ecom_user_id, shipping_postal_code
        FROM staging.stg_ecom_orders
        WHERE NOT regexp_full_match(shipping_postal_code, '\\d{5}')""").df()
    # Código postal real: el del CRM o la tarjeta de tienda de la misma persona (no se
    # corrompen en la generación); si no, el del propio usuario online si es válido.
    known = con.execute("""
        SELECT customer_id AS source_id, postal_code FROM staging.stg_crm_customers
        UNION ALL SELECT card_id, postal_code FROM staging.stg_pos_loyalty_cards
        UNION ALL SELECT ecom_user_id, postal_code FROM staging.stg_ecom_customers
        WHERE regexp_full_match(postal_code, '\\d{5}')""").df()
    by_person = (known.merge(links, on="source_id").groupby("person_id")["postal_code"]
                 .first())
    person_of = links.set_index("source_id")["person_id"]
    orders["true_postal"] = orders["ecom_user_id"].map(person_of).map(by_person)
    return orders.dropna(subset=["true_postal"]).reset_index(drop=True)


def simulate_vendor(orders: pd.DataFrame, v: Vendor, rng: np.random.Generator) -> pd.Series:
    """Respuesta del proveedor por pedido (None si no devuelve nada)."""
    out = []
    for truth in orders["true_postal"]:
        if rng.random() >= v.coverage:
            out.append(None)
        elif rng.random() < v.accuracy:
            out.append(truth)
        else:
            out.append(f"{int(rng.integers(1, 53)):02d}{int(rng.integers(0, 1000)):03d}")
    return pd.Series(out, index=orders.index)


@dataclass(frozen=True)
class VendorResult:
    vendor: Vendor
    queried: int
    returned: int
    correct: int

    @property
    def wrong(self) -> int:
        return self.returned - self.correct

    @property
    def cost(self) -> float:
        return self.queried * self.vendor.price

    @property
    def cost_per_correct(self) -> float:
        return self.cost / self.correct if self.correct else float("inf")


def evaluate_vendor(orders: pd.DataFrame, answers: pd.Series, v: Vendor) -> VendorResult:
    returned = answers.notna()
    correct = returned & (answers == orders["true_postal"])
    return VendorResult(v, len(orders), int(returned.sum()), int(correct.sum()))


def pick_vendor(results: list[VendorResult]) -> VendorResult:
    """Menor coste por corrección real, penalizando cada dato erróneo como uno no corregido."""
    return min(results, key=lambda r: r.cost / max(r.correct - r.wrong, 1))

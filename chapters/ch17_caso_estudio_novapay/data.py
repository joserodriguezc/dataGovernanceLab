"""Datos sintéticos de NovaPay: hojas de cálculo diarias de cada unidad y clientes.

Cada unidad envía cada día sus partidas del informe de liquidez. Se siembran los defectos
típicos de un proceso con hojas de cálculo (filas duplicadas, importes como texto con
formato español, importes vacíos y signos cambiados) y se guarda el valor correcto de cada
partida para poder medir cuánto se equivoca el informe.
"""

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd
from faker import Faker
from pydantic import BaseModel, Field

from dglab.synthetic.noise import pick


class Unit(BaseModel):
    side: str
    items: dict[str, float]


class Defects(BaseModel):
    duplicate_rows: float = Field(ge=0, le=1)
    text_amounts: float = Field(ge=0, le=1)
    missing_amount: float = Field(ge=0, le=1)
    wrong_sign: float = Field(ge=0, le=1)


class Generation(BaseModel):
    seed: int
    start: date
    days: int = Field(gt=0)
    customers: int = Field(gt=0)
    units: dict[str, Unit]
    daily_noise: float = Field(ge=0)
    defects: Defects
    regulatory_minimum: float = Field(gt=0)


@dataclass
class NovaPayData:
    submissions: pd.DataFrame  # filas tal como llegan de las hojas de cálculo
    truth: pd.DataFrame        # valor correcto de cada partida y día
    customers: pd.DataFrame


def spanish_text(amount: float) -> str:
    """1234567.891 -> '1.234.567,89'."""
    return f"{amount:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def generate(g: Generation) -> NovaPayData:
    rng = np.random.default_rng(g.seed)
    fake = Faker("es_ES")
    fake.seed_instance(g.seed)
    truth = []
    for d in range(g.days):
        day = g.start + timedelta(days=d)
        for unit, u in g.units.items():
            for item, base in u.items.items():
                value = round(base * (1 + rng.normal(0, g.daily_noise)), 2)
                truth.append({"report_date": day, "business_unit": unit, "side": u.side,
                              "item": item, "amount": value})
    truth_df = pd.DataFrame(truth)

    rows = []
    preparers = {unit: fake.name() for unit in g.units}
    for i, t in enumerate(truth_df.itertuples()):
        rows.append({"row_id": f"R{i + 1:06d}", "report_date": t.report_date.isoformat(),
                     "business_unit": t.business_unit, "item": t.item,
                     "amount": f"{t.amount:.2f}", "submitted_by": preparers[t.business_unit]})
    n, d = len(rows), g.defects
    for i in pick(n, d.text_amounts, rng):
        rows[i]["amount"] = spanish_text(float(rows[i]["amount"]))
    for i in pick(n, d.missing_amount, rng):
        rows[i]["amount"] = None
    liabilities = [i for i, t in enumerate(truth_df.itertuples()) if t.side == "liability"]
    for i in rng.choice(liabilities, size=round(len(liabilities) * d.wrong_sign),
                        replace=False):
        if rows[i]["amount"] and not rows[i]["amount"].count(","):
            rows[i]["amount"] = f"-{rows[i]['amount']}"
    dupes = [dict(rows[i], row_id=f"D{k + 1:06d}")
             for k, i in enumerate(sorted(pick(n, d.duplicate_rows, rng)))]
    submissions = pd.DataFrame(rows + dupes).sample(frac=1, random_state=g.seed)

    customers = pd.DataFrame([{
        "account_id": f"NP{i + 1:06d}", "holder_name": fake.name(),
        "iban": f"ES{int(rng.integers(10, 99))}{int(rng.integers(0, 10**18)):020d}",
        "phone": f"6{int(rng.integers(0, 10**8)):08d}",
        "kyc_status": rng.choice(["verificado", "verificado", "verificado", "pendiente"]),
        "opened_at": (g.start - timedelta(days=int(rng.integers(30, 900)))).isoformat(),
    } for i in range(g.customers)])
    return NovaPayData(submissions.reset_index(drop=True), truth_df, customers)

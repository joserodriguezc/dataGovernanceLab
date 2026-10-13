"""Logs de uso simulados de las soluciones de datos y KPI de adopción.

En un caso real, los logs saldrían de las herramientas (accesos al marketplace, consultas
al buscador, aperturas de cuadros de mando). Aquí se simulan con una semilla: cada usuario
objetivo la adopta o no, se da de alta en los primeros meses, cada mes la usa o no y puede
abandonarla para volver al método anterior.
"""

from datetime import date

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


class Simulation(BaseModel):
    share: float = Field(ge=0, le=1)          # parte de los usuarios objetivo que la adopta
    monthly_active: float = Field(ge=0, le=1)  # probabilidad de que un adoptante la use en un mes
    churn: float = Field(ge=0, le=1)          # probabilidad mensual de abandonarla
    ramp_months: int = Field(3, ge=1)         # meses en los que se reparten las altas
    data_team_share: float | None = None      # adopción en el equipo de datos, si es distinta
    data_team_churn: float | None = None      # abandono en el equipo de datos, si es distinto


class OldWay(BaseModel):
    name: str
    hours_per_user_month: float = Field(ge=0)


class Solution(BaseModel):
    id: str
    name: str
    go_live: date
    build_cost: float = Field(ge=0)
    annual_run_cost: float = Field(ge=0)
    target: dict[str, int]
    simulation: Simulation
    old_way: OldWay

    @property
    def target_users(self) -> int:
        return sum(self.target.values())


def simulate_usage(solutions: list[Solution], as_of: date, months: int,
                   rng: np.random.Generator) -> pd.DataFrame:
    """Un registro por usuario, solución y mes en el que la usa."""
    start = pd.Period(as_of, "M") - (months - 1)
    rows = []
    for s in solutions:
        sim = s.simulation
        first = max(start, pd.Period(s.go_live, "M"))
        periods = list(pd.period_range(first, pd.Period(as_of, "M"), freq="M"))
        for dept, n in s.target.items():
            data_team = dept == "Datos"
            share, churn = sim.share, sim.churn
            if data_team and sim.data_team_share is not None:
                share = sim.data_team_share
            if data_team and sim.data_team_churn is not None:
                churn = sim.data_team_churn
            for i in range(n):
                if rng.random() >= share:
                    continue  # nunca la adopta
                joined = int(rng.integers(0, sim.ramp_months))
                for m, period in enumerate(periods):
                    if m < joined:
                        continue
                    if m > joined and rng.random() < churn:
                        break  # la abandona y vuelve al método anterior
                    if rng.random() < sim.monthly_active:
                        rows.append({"solution": s.id, "department": dept,
                                     "user": f"{s.id}-{dept[:3].lower()}-{i:03d}",
                                     "month": str(period)})
    return pd.DataFrame(rows, columns=["solution", "department", "user", "month"])


def monthly_active(usage: pd.DataFrame, solutions: list[Solution]) -> pd.DataFrame:
    """Usuarios activos al mes por solución (vacío antes de su salida en vivo)."""
    mau = usage.groupby(["solution", "month"])["user"].nunique().unstack(0).fillna(0)
    for s in solutions:
        live = str(pd.Period(s.go_live, "M"))
        if s.id in mau:
            mau.loc[mau.index < live, s.id] = float("nan")
    return mau


def retention(usage: pd.DataFrame, solution: str) -> float:
    """Media de usuarios activos un mes que siguen activos el mes siguiente."""
    months = list(usage[usage.solution == solution].groupby("month")["user"].apply(set)
                  .sort_index())
    rates = [len(a & b) / len(a) for a, b in zip(months, months[1:], strict=False) if a]
    return float(np.mean(rates)) if rates else 0.0


def adoption_by_department(usage: pd.DataFrame, s: Solution, month: str) -> dict[str, float]:
    active = usage[(usage.solution == s.id) & (usage.month == month)]
    counts = active.groupby("department")["user"].nunique()
    return {d: counts.get(d, 0) / n for d, n in s.target.items()}

"""Paso 4 del capítulo: ROI de cada enfoque con la fórmula del libro.

Ahorro anual = horas manuales eliminadas × coste/hora − horas de mantenimiento × coste/hora.
Coste puntual = horas de construcción × coste/hora.
ROI a N años = (ahorro × N − coste puntual) / coste puntual.
"""

from dataclasses import dataclass

from pydantic import BaseModel, Field


class ProcessStep(BaseModel):
    step: str
    minutes: float = Field(gt=0)
    manual: bool
    error_prone: bool


class CurrentProcess(BaseModel):
    frequency_per_year: int = Field(gt=0)
    people: str
    steps: list[ProcessStep] = Field(min_length=1)

    @property
    def hours_per_year(self) -> float:
        return sum(s.minutes for s in self.steps) / 60 * self.frequency_per_year


class Approach(BaseModel):
    name: str
    capabilities: list[str]
    automated_steps: list[int]
    maintain_hours_per_year: float = Field(ge=0)
    build_hours: float = Field(gt=0)


@dataclass(frozen=True)
class ApproachRoi:
    key: str
    approach: Approach
    hours_removed: float
    annual_saving: float
    one_time_cost: float
    horizon_years: int

    @property
    def net_benefit(self) -> float:
        return self.annual_saving * self.horizon_years - self.one_time_cost

    @property
    def roi(self) -> float:
        return self.net_benefit / self.one_time_cost

    @property
    def payback_weeks(self) -> float:
        return self.one_time_cost / (self.annual_saving / 52) if self.annual_saving > 0 \
            else float("inf")


def approach_roi(key: str, a: Approach, process: CurrentProcess, cost_per_hour: float,
                 horizon_years: int) -> ApproachRoi:
    bad = [i for i in a.automated_steps if not 0 <= i < len(process.steps)]
    if bad:
        raise ValueError(f"{key}: pasos inexistentes {bad}")
    minutes = sum(process.steps[i].minutes for i in a.automated_steps)
    hours = minutes / 60 * process.frequency_per_year
    saving = (hours - a.maintain_hours_per_year) * cost_per_hour
    return ApproachRoi(key, a, hours, saving, a.build_hours * cost_per_hour, horizon_years)

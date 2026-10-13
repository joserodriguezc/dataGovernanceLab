"""Quick wins: racionalizar las necesidades, medir su tamaño, priorizar y planificar.

Pasos del capítulo: identificar las necesidades por grupo, racionalizar la lista en
problemas comunes (aunque estén dichos con otras palabras), priorizar por impacto,
urgencia y coste, separar la solución rápida de la de largo plazo, y planificar las
entregas con la capacidad del equipo (entrega continua).
"""

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Literal

import duckdb
from pydantic import BaseModel, Field, model_validator
from rapidfuzz import fuzz

from chapters.ch10_datos_primarios_mdm.parties import name_key

Level = Literal["low", "medium", "high"]
LEVEL = {"low": 1, "medium": 2, "high": 3}
LEVEL_LABELS = {"low": "Bajo", "medium": "Medio", "high": "Alto"}
FUNDING_LABELS = {"cdao": "Oficina del CDAO", "stakeholder": "Stakeholder", "hybrid": "Híbrida"}


class Need(BaseModel):
    group: str
    text: str
    issue: str


class Issue(BaseModel):
    title: str
    outcome: str
    measure: str
    size_sql: str | None = None
    size_unit: Literal["pct", "count"] | None = None
    impact: Level
    urgency: Level
    cost: Level
    short_term: str
    long_term: str
    options: list[str] = Field(min_length=3)  # el libro pide al menos tres opciones
    funding: Literal["cdao", "stakeholder", "hybrid"]

    @property
    def score(self) -> int:
        """Más impacto y urgencia suben; más coste baja (de -1 a 8)."""
        return 2 * LEVEL[self.impact] + LEVEL[self.urgency] - LEVEL[self.cost]

    @property
    def quadrant(self) -> str:
        high_impact, low_cost = LEVEL[self.impact] >= 2, self.cost == "low"
        if high_impact and low_cost:
            return "Quick win"
        if high_impact:
            return "Estratégico (largo plazo)"
        if low_cost:
            return "Relleno"
        return "Evitar"


class NeedsInput(BaseModel):
    needs: list[Need] = Field(min_length=1)
    issues: dict[str, Issue]

    @model_validator(mode="after")
    def _known(self) -> "NeedsInput":
        unknown = {n.issue for n in self.needs} - set(self.issues)
        if unknown:
            raise ValueError(f"necesidades asignadas a problemas inexistentes: {sorted(unknown)}")
        return self


def issue_matrix(needs: list[Need]) -> dict[str, set[str]]:
    """Problema -> grupos que lo han mencionado (tabla 13.2 del libro)."""
    out: dict[str, set[str]] = defaultdict(set)
    for n in needs:
        out[n.issue].add(n.group)
    return out


@dataclass(frozen=True)
class FuzzyCheck:
    same_issue_pairs: int
    found_by_fuzzy: int
    missed: list[tuple[str, str]]


def fuzzy_rationalization(needs: list[Need], threshold: float = 80) -> FuzzyCheck:
    """¿Cuántas necesidades del mismo problema encontraría un emparejamiento automático?

    Demuestra la advertencia del libro: el mismo problema dicho con otras palabras no se
    detecta comparando textos; hay que conocer el contenido.
    """
    pairs = [(a, b) for a, b in combinations(needs, 2) if a.issue == b.issue]
    found = [(a, b) for a, b in pairs
             if fuzz.token_set_ratio(name_key(a.text), name_key(b.text)) >= threshold]
    missed = [(a.text, b.text) for a, b in pairs if (a, b) not in found]
    return FuzzyCheck(len(pairs), len(found), missed)


def measure(con: duckdb.DuckDBPyConnection, issue: Issue) -> float | None:
    """Tamaño del problema medido en el warehouse (None si no hay evidencia todavía)."""
    if not issue.size_sql:
        return None
    try:
        value = con.execute(issue.size_sql).fetchone()[0]
    except duckdb.CatalogException:
        return None
    return None if value is None else float(value)


def plan(issues: dict[str, Issue], quarters: list[str], capacity: int) -> dict[str, list[str]]:
    """Reparte las soluciones a corto plazo por trimestres según la capacidad del equipo.

    Se toman en orden de puntuación; cada una consume su coste (bajo=1, medio=2, alto=3).
    Lo que no cabe se queda en el backlog.
    """
    roadmap: dict[str, list[str]] = {q: [] for q in quarters}
    used = dict.fromkeys(quarters, 0)
    for key, issue in sorted(issues.items(), key=lambda kv: (-kv[1].score, kv[0])):
        for q in quarters:
            if used[q] + LEVEL[issue.cost] <= capacity:
                roadmap[q].append(key)
                used[q] += LEVEL[issue.cost]
                break
        else:
            roadmap.setdefault("Backlog", []).append(key)
    return roadmap


# --- Mentalidad de producto ---------------------------------------------------------------

class Solution(BaseModel):
    name: str
    continuous_support: bool
    continuous_delivery: bool
    needs_features: bool
    monthly_users: int = Field(ge=0)

    @property
    def kind(self) -> str:
        """Producto, servicio o activo según los criterios del libro."""
        if self.continuous_support and self.continuous_delivery and self.needs_features:
            return "Producto"
        if self.continuous_support:
            return "Servicio"
        return "Activo"


class Communication(BaseModel):
    win: str
    impact: Literal["low", "high"]
    communicated: bool

    @property
    def quadrant(self) -> str:
        return {
            ("high", True): "✅ Impacto alto y bien comunicado",
            ("high", False): "⚠️ Impacto alto sin comunicar: nadie sabe que existe",
            ("low", True): "❌ Impacto bajo sobrecomunicado: resta credibilidad",
            ("low", False): "Impacto bajo sin comunicar: buscar algo con más impacto",
        }[(self.impact, self.communicated)]


class Idea(BaseModel):
    idea: str
    submitted_by: str
    channel: str
    issue: str


class DeliveryInput(BaseModel):
    solutions: list[Solution]
    communication: list[Communication]
    ideas: list[Idea]
    capacity_per_quarter: int = Field(gt=0)
    quarters: list[str] = Field(min_length=1)

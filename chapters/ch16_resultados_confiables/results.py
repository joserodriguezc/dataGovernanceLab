"""Compromisos frente a resultados y mensajes de desvío.

Los compromisos son los resultados de datos del capítulo 5. Se miden otra vez ahora, con
el warehouse tal como lo han dejado los capítulos 6-14. Lo que aún no vence va "en plazo";
lo retrasado, y cada riesgo que ya se ve aunque no haya vencido, lleva un mensaje de desvío
con la estructura del capítulo: qué ha pasado, por qué, qué vamos a hacer (con responsable
y fecha) y qué ajustamos.
"""

from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel

from chapters.ch05_exito_y_resultados.framework import OutcomeFramework
from chapters.ch05_exito_y_resultados.progress import data_outcomes


class Variance(BaseModel):
    why: str
    plan: str
    owner: str
    new_date: date
    adjustment: str


STATUS_LABELS = {
    "met": "✓ Cumplido",
    "on_track": "En plazo",
    "at_risk": "~ Riesgo anticipado",
    "late": "~ Retrasado, con plan",
    "late_unexplained": "✗ Retrasado, sin causa raíz",
}
STATUS_CLASS = {"met": "done", "on_track": "done", "at_risk": "partial", "late": "partial",
                "late_unexplained": "missing"}


@dataclass(frozen=True)
class Commitment:
    outcome_id: str
    name: str
    target: str
    measured: str
    met: bool
    due: date
    overdue: bool
    variance: Variance | None

    @property
    def status(self) -> str:
        if self.met:
            return "met"
        if self.overdue:
            return "late" if self.variance else "late_unexplained"
        return "at_risk" if self.variance else "on_track"

    @property
    def needs_message(self) -> bool:
        """Se comunica todo lo retrasado y, de forma proactiva, los riesgos anticipados."""
        return self.status in {"at_risk", "late", "late_unexplained"}


def commitments(fw: OutcomeFramework, indicators: dict[str, float],
                variances: dict[str, Variance]) -> list[Commitment]:
    out = []
    for o in fw.outcomes:
        for s in data_outcomes(o, fw, indicators):
            if s.metric and s.measured is not None:
                target = f"{s.metric.target:.1%}".replace(".", ",")
                measured = f"{s.measured:.1%}".replace(".", ",")
            else:
                done = sum(d.done for d in s.deliverables)
                total = sum(d.total for d in s.deliverables)
                target, measured = "entregables completos", f"{done} de {total} hitos"
            due = max(d.due for d in s.deliverables)
            out.append(Commitment(o.id, s.name, target, measured, s.achieved, due,
                                  not s.achieved and due < fw.as_of,
                                  None if s.achieved else variances.get(s.name)))
    return out


def status_counts(items: list[Commitment]) -> dict[str, int]:
    return {s: sum(c.status == s for c in items) for s in STATUS_LABELS}

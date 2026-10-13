"""Coste de la baja adopción y diagnóstico de por qué falla.

Las tres causas del capítulo: la solución (usabilidad, relevancia, confianza en el dato,
encaje en el flujo de trabajo), la empresa (liderazgo que la usa, formación, gestión del
cambio) y el líder (escucha y adapta). Se diagnostica con la encuesta.
"""

from dataclasses import dataclass

from .usage import Solution

CAUSES = {
    "solution": ("La solución", {"usability": "Usabilidad", "relevance": "Relevancia",
                                 "data_trust": "Confianza en el dato",
                                 "workflow_fit": "Encaje en el flujo de trabajo"}),
    "company": ("La empresa", {"leadership_use": "La dirección la usa",
                               "training": "Formación y soporte",
                               "change_comms": "Gestión del cambio"}),
    "leader": ("El líder", {"leader_listens": "Escucha y adapta"}),
}
ACTIONS = {
    "usability": "Simplificar la interfaz con los usuarios que la abandonaron",
    "relevance": "Volver a definir el problema con cada grupo (¿se diagnosticó mal?)",
    "data_trust": "Usar solo datos certificados (capítulo 8) y mostrar su origen",
    "workflow_fit": "Llevar la solución al flujo de trabajo: integrarla donde ya trabajan",
    "leadership_use": "Que el sponsor la use en el comité y lo cuente",
    "training": "Formación continua tras la salida en vivo, no solo en el lanzamiento",
    "change_comms": "Campeones de datos en cada departamento y casos de éxito",
    "leader_listens": "Pedir feedback, buscar un mentor y ajustar el enfoque",
}


@dataclass(frozen=True)
class AdoptionCost:
    unused_investment: float     # parte de la inversión que no se aprovecha
    duplicated_effort: float     # horas al año de quienes siguen con el método anterior
    duplicated_hours: float

    @property
    def total(self) -> float:
        return self.unused_investment + self.duplicated_effort


def adoption_cost(s: Solution, rate: float, cost_per_hour: float) -> AdoptionCost:
    gap = max(0.0, 1 - rate)
    unused = (s.build_cost / 3 + s.annual_run_cost) * gap  # construcción amortizada en 3 años
    hours = s.target_users * gap * s.old_way.hours_per_user_month * 12
    return AdoptionCost(unused, hours * cost_per_hour, hours)


@dataclass(frozen=True)
class Diagnosis:
    cause: str
    label: str
    weak: list[tuple[str, str, float]]  # (clave, etiqueta, puntuación)


def diagnose(scores: dict[str, float], weak_score: float) -> list[Diagnosis]:
    out = []
    for cause, (label, items) in CAUSES.items():
        weak = [(k, name, scores[k]) for k, name in items.items() if scores[k] < weak_score]
        if weak:
            out.append(Diagnosis(cause, label, sorted(weak, key=lambda w: w[2])))
    return out

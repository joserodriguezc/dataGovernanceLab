"""Estilo común de los gráficos (matplotlib) para que todos los capítulos se lean igual.

Paleta categórica validada para daltonismo: asignar los colores siempre en este orden,
nunca en ciclo. Con más de 3 series en gráficos de dispersión, agrupar en "Otros".
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sin pantalla: los gráficos se guardan como fichero

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
# Rampa secuencial de un solo tono (azul, de claro a oscuro) para magnitudes ordenadas
SEQUENTIAL_BLUE = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
SURFACE = "#fcfcfb"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
TEXT_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
STATUS = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b"}


def new_figure(width: float = 9, height: float = 5) -> tuple[Figure, Axes]:
    """Crea una figura con superficie, rejilla y ejes discretos."""
    fig, ax = plt.subplots(figsize=(width, height), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(BASELINE)
    ax.grid(axis="y", color=GRIDLINE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=TEXT_MUTED, labelcolor=TEXT_SECONDARY, length=0)
    return fig, ax


def set_titles(ax: Axes, title: str, subtitle: str | None = None) -> None:
    """Título alineado a la izquierda y subtítulo opcional en tinta secundaria."""
    ax.set_title(title, loc="left", fontsize=13, color=TEXT_PRIMARY, pad=24 if subtitle else 10)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color=TEXT_SECONDARY)


def save_figure(fig: Figure, path: Path) -> Path:
    """Guarda la figura en PNG y libera memoria."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path

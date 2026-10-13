"""Helpers de reporting: plantillas jinja2 y formato de cifras en convención española."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined


def fmt_eur(value: float, decimals: int = 0) -> str:
    """Formatea un importe en euros: 1234567.8 -> '1.234.568 €'."""
    text = f"{value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{text} €"


def fmt_pct(value: float, decimals: int = 0) -> str:
    """Formatea una proporción como porcentaje: 0.425 -> '42,5 %' (con decimals=1)."""
    return f"{value * 100:.{decimals}f}".replace(".", ",") + " %"


def fmt_num(value: float, decimals: int = 0) -> str:
    """Formatea un número con separador de miles español."""
    return fmt_eur(value, decimals).removesuffix(" €")


def template_env(template_dir: Path) -> Environment:
    """Entorno jinja2 estricto (falla ante variables no definidas) con los filtros de formato."""
    env = Environment(
        loader=FileSystemLoader(template_dir),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters.update(eur=fmt_eur, pct=fmt_pct, num=fmt_num)
    return env


def render_template(template_dir: Path, name: str, **context: Any) -> str:
    """Renderiza la plantilla `name` de `template_dir` con el contexto dado."""
    return template_env(template_dir).get_template(name).render(**context)


def write_text(path: Path, text: str) -> Path:
    """Escribe texto en UTF-8 creando las carpetas intermedias."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path

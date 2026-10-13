"""Rutas canónicas del proyecto, para que ningún capítulo dependa del directorio actual."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
TRUTH_DIR = RAW_DIR / "_truth"  # solucionario de los datos sintéticos (solo para evaluar)
WAREHOUSE_DIR = DATA_DIR / "warehouse"
WAREHOUSE_DB = WAREHOUSE_DIR / "novamercado.duckdb"
# Registro de operaciones (ejecuciones, auditoría): fuera del warehouse para que no se
# pierda al reconstruirlo
OPS_DB = WAREHOUSE_DIR / "operations.duckdb"
CHAPTERS_DIR = ROOT / "chapters"


def chapter_dir(number: int) -> Path:
    """Devuelve la carpeta del capítulo `number` (p. ej. 6 -> chapters/ch06_gestion_metadatos)."""
    matches = sorted(CHAPTERS_DIR.glob(f"ch{number:02d}_*"))
    if not matches:
        raise FileNotFoundError(f"No existe carpeta para el capítulo {number}")
    return matches[0]


def chapter_outputs(number: int) -> Path:
    """Devuelve (y crea si hace falta) la carpeta de salidas del capítulo."""
    out = chapter_dir(number) / "outputs"
    out.mkdir(parents=True, exist_ok=True)
    return out

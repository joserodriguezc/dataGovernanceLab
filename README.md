# Data Governance Lab

*Data Governance Handbook* (Wendy S. Batchelder, Packt 2024) convertido en 17 microproyectos prácticos, uno por capítulo, sobre la empresa ficticia **NovaMercado**.

El plan completo, el orden de trabajo y el estado de cada capítulo están en [PLAN.md](PLAN.md).

## Requisitos

[uv](https://docs.astral.sh/uv/). uv instala Python 3.12 automáticamente.

## Instalación

```bash
uv sync
```

## Uso

```bash
# Ejecutar el microproyecto de un capítulo
uv run python chapters/ch01_que_es_gobierno_datos/run.py

# Tests (todos o los de un capítulo)
uv run pytest
uv run pytest chapters/ch08_calidad_datos

# Lint
uv run ruff check .
```

## Estructura

```
src/dglab/        paquete compartido (rutas, empresa ficticia, datos sintéticos, reporting)
data/raw/         CSV sintéticos (generados, no versionados)
data/warehouse/   base DuckDB de NovaMercado (generada, no versionada)
chapters/chNN_*/  un microproyecto por capítulo: README, inputs/, run.py, outputs/, tests/
docs/             referencia bibliográfica y notas (el libro no se versiona)
tests/            tests del paquete compartido
```

## Referencia y derechos

Proyecto de aprendizaje basado en *Data Governance Handbook* (Wendy S. Batchelder, Packt Publishing, 2024, ISBN 978-1-80324-072-5). El libro tiene copyright y no se distribuye aquí: el repositorio solo lo referencia (ver [docs/README.md](docs/README.md)). Todo el código y los datos sintéticos son originales.

# Capítulo 1: ¿Qué es el gobierno de datos?

> **Libro:** *What Is Data Governance?*. Parte 1: Diseñar el camino hacia datos confiables.
> **Microproyecto:** Charter del programa y caso de negocio.

**Estado:** ✅ hecho

## Objetivo

Definir qué es (y qué no es) el gobierno de datos para NovaMercado y justificar el programa como habilitador de valor de negocio, no como centro de coste.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| El gobierno de datos crea valor de negocio: **data equity = activos − pasivos de datos** | Valoramos cada activo y pasivo de NovaMercado en su situación actual y en la objetivo | [equity.py](equity.py) |
| Si el negocio no ha validado la valoración, no es creíble | Las líneas sin `vetted_by` quedan fuera del caso de negocio conservador | [equity.py](equity.py) |
| Caso de negocio con plantilla fija y **tres opciones de timeline** | Calculamos VAN, ROI y payback de las opciones preferida, rápida y lenta | [business_case.py](business_case.py) |
| *Why statement* claro, memorable y sin *data speak* | Un linter avisa de jerga técnica y de exceso de palabras | [charter.py](charter.py) |
| Misión del programa: "Hacemos X para Y mediante A, B y C" | La plantilla se rellena desde YAML | [charter.py](charter.py) |
| Cuándo lanzar y cuándo esperar | Se lanza si hay al menos un impulsor y ninguna señal de alerta | [charter.py](charter.py) |
| La política como primer bloque, con un esquema de 10 secciones | La política se genera y un test comprueba que tiene las 10 secciones | [policy.py](policy.py) |
| **EDG Scorecard** corporativo y por dominio, en verde, amarillo o rojo | Las métricas se derivan del estado de cada dominio y sus sistemas | [scorecard.py](scorecard.py) |
| Guía rápida de términos para toda la organización | Un glosario compartido por el charter y la política | [inputs/program.yaml](inputs/program.yaml) |

## Entregables (`outputs/`)

| Archivo | Contenido |
|---|---|
| `charter.md` | Visión y su revisión, misiones, componentes, decisión de lanzamiento y glosario |
| `data_equity.md` | Activos, pasivos y data equity actual y objetivo, separando lo validado de lo pendiente |
| `business_case.md` | Caso de negocio con la plantilla del libro y la comparación de las 3 opciones |
| `business_case_cashflow.png` | Flujo de caja neto acumulado por opción, con el mes de payback marcado |
| `data_governance_policy.md` | Política corporativa con las 10 secciones |
| `edg_scorecard.md` | Scorecard corporativo y de cada uno de los 6 dominios |

Todo se genera desde los YAML de [inputs/](inputs/). Para cambiar un supuesto, se edita el YAML y se vuelve a ejecutar.

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch01_que_es_gobierno_datos.run
uv run pytest chapters/ch01_que_es_gobierno_datos
```

## Decisiones de modelado

- **Valoración anual.** Activo = ingresos + horas ahorradas × coste/hora + valor de cliente. Pasivo = probabilidad de multa × importe + horas perdidas × coste/hora + impacto en el cliente. La mejora anual (más activo o menos pasivo) es el beneficio del caso de negocio.
- **Conservador por defecto** (`include_unvetted_benefits: false`). Las líneas A3 y L4 no las ha validado aún el negocio y no cuentan: suman 840.000 €/año que quedan como potencial adicional.
- **Flujos mensuales a 36 meses.** La construcción se paga a partes iguales durante la duración de cada opción y la operación empieza al terminarla. El beneficio crece de forma lineal mientras se construye, porque se entrega de forma iterativa.
- **Estado del scorecard.** Verde si la métrica está completa o falta tiempo, amarillo si la fecha comprometida está a 30 días o menos, y rojo si ha vencido sin completarse.

## Conclusiones para NovaMercado

1. **La data equity actual es negativa (−1,08 M€).** Los pasivos (PII sin clasificar, métricas inconsistentes, duplicados) pesan más que el valor que hoy se obtiene de los datos. El programa la lleva a +2,16 M€, con una mejora validada de **2,58 M€/año**.
2. **El timeline preferido es la opción con más VAN** (2,25 M€, payback en el mes 21). La opción rápida llega antes al valor completo, pero su sobrecoste no se compensa en 36 meses. La lenta recupera antes la inversión (mes 17) porque gasta menos al mes, pero acumula menos valor. Por eso conviene presentar las tres: la dirección ve que se pensó en sus expectativas.
3. **Decisión: lanzar.** Hay tres impulsores (regulatorio, petición ejecutiva y petición de negocio) y ninguna señal de alerta.
4. **El scorecard ya muestra dónde actuar.** Falta el ejecutivo del dominio de proveedores, cuya fecha ha vencido, y el owner del POS en el dominio de cliente, que está en riesgo. Son las primeras conversaciones del capítulo 2 (coalición de defensores).

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada

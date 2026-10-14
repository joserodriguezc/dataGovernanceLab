# Capítulo 17: Caso de estudio: institución financiera

> **Libro:** *Case Study – Financial Institution*. Parte 4: Caso de estudio.
> **Microproyecto:** NovaPay de punta a punta.

**Estado:** ✅ hecho

## Objetivo

Aplicar el programa completo a **NovaPay**, la filial financiera regulada de NovaMercado (monedero digital y tarjeta). El escenario es análogo al del libro: el supervisor ha detectado errores en el informe diario de liquidez, el CDAO acaba de llegar y hay tres retos:

1. encontrar **quick wins** bajo presión regulatoria;
2. **explicar la solución de largo plazo** al comité de dirección y al supervisor;
3. **diseñar una entrega iterativa** que demuestre impacto.

Un solo comando genera los datos, construye un warehouse propio y produce todo el caso. No depende del warehouse de NovaMercado.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| Descubrimiento en las dos primeras semanas: hablar con todos y agrupar en temas | Hallazgos por interlocutor y 5 temas clave (responsabilidad, segregación, formación, calidad, comunicación) | [inputs/novapay.yaml](inputs/novapay.yaml) |
| El informe se monta a mano con hojas de cálculo de varias unidades | Datos sintéticos con duplicados, importes en texto con formato español, vacíos y signos cambiados; se guarda el valor real de cada partida | [data.py](data.py) |
| Quien prepara el informe también lo revisa | Comprobación de segregación de funciones sobre la RACI del capítulo 3, antes y después | [case.py](case.py) |
| Lista priorizada de incidencias con reglas de calidad | 4 reglas sobre lo enviado y 2 sobre lo remediado, con el motor del capítulo 8 | [case.py](case.py) |
| Documentar el flujo de datos hasta el informe | Linaje de columna de la ratio con el parser del capítulo 7; tablas documentadas con `COMMENT ON` | [case.py](case.py), [sql/novapay.sql](sql/novapay.sql) |
| Datos de clientes sensibles en una entidad regulada | Política de clasificación del capítulo 6, ampliada con una regla para el IBAN | [inputs/novapay.yaml](inputs/novapay.yaml) |
| Opciones de plan para el comité: rápida, equilibrada, mínima | VAN y recuperación con el caso de negocio del capítulo 1 | [run.py](run.py) |
| Mismos materiales para el comité y el supervisor, con transparencia | Resumen para el comité y mensaje al supervisor; el mensaje pasa la revisión de jerga del capítulo 12 | [templates/](templates/) |
| Indicador de confianza en el informe | Un día se certifica si está documentado, tiene linaje y está completo | [case.py](case.py) |
| Resultados a 3, 6 y 12 meses | Lo de 3 meses y las metas de 12 meses (reducción de incidencias, procesos automatizados) se miden | [templates/case_study.md.j2](templates/case_study.md.j2) |

## Entregables (`outputs/`)

| Archivo | Contenido |
|---|---|
| `case_study.md` | El caso completo: descubrimiento, datos, calidad, linaje, PII, quick wins, opciones, mensaje al supervisor, entrega iterativa y resultados |
| `elt_summary.md` | Resumen para el comité de dirección en tres bloques: responsabilidad, proceso y calidad, pasos inmediatos |
| `regulator_message.md` | Mensaje al supervisor: qué ha pasado, qué se ha hecho, qué se va a hacer, cómo lo verá y el seguimiento |
| `liquidity_ratio.png` | Ratio diaria: hoja consolidada a mano, informe remediado y valor real, con el mínimo regulatorio |

Además se crea `data/warehouse/novapay.duckdb`, con las capas raw, staging y curated.

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch17_caso_estudio_novapay.run
uv run pytest chapters/ch17_caso_estudio_novapay
```

## Decisiones de modelado

- **Un warehouse propio.** NovaPay es una entidad separada y regulada, así que sus datos no se mezclan con los de NovaMercado. Las *herramientas* sí se reutilizan: RACI, reglas, linaje, clasificación, caso de negocio y revisión de jerga.
- **La hoja a mano se simula tal cual.** Suma todo lo que es número, así que las duplicadas cuentan dos veces, los importes en texto se pierden y los signos cambiados restan. El error se mide frente al valor real, no se supone.
- **No se inventan datos.** Si a un día le falta alguna partida, el informe remediado no calcula la ratio: el día queda incompleto y se pide el reenvío a la unidad. Por eso hay 77 días certificados de 90.
- **SQL sin CTE.** La primera versión usaba CTE y el linaje se quedaba en ellas sin llegar a raw. Se reescribió con una SELECT por tabla. La lección para el caso: el SQL de un informe regulado se escribe para que se pueda trazar.
- **La política de clasificación se amplía, no se copia.** La de NovaMercado es la de un retail y no conocía el IBAN. NovaPay añade su regla antes de clasificar.
- **La opción aprobada no es la de mayor VAN.** El comité elige la rápida porque el VAN solo mide el beneficio interno, no las sanciones ni la confianza del supervisor. El informe lo dice explícitamente.

## Conclusiones para NovaPay

1. **La hoja a mano daba una imagen falsa:** 25 días por debajo del mínimo regulatorio cuando fueron 6, con un error medio de 0,80 puntos en la ratio. El informe remediado coincide exactamente con el valor real en los 77 días completos.
2. **Los quick wins son de personas y procesos antes que de tecnología.** Hay que nombrar un preparador en Finanzas y separar la preparación de la revisión. La RACI pasa de fallar a cumplir la segregación.
3. **El 90 % de las incidencias de calidad se resuelve en el warehouse:** 143 en origen y 14 tras remediar. Las que quedan son importes que faltan y se corrigen en origen, con los stewards de cada unidad.
4. **El mensaje al supervisor no lleva jerga** y usa los mismos datos que ve el comité: transparencia en lugar de una versión maquillada.
5. **Metas de 12 meses ya medibles:** reducción de incidencias (90 %) y procesos manuales automatizados (4 de 10 pasos).

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada
- [x] Paso añadido al recorrido del README raíz

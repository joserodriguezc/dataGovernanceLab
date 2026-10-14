# Capítulo 16: Resultados confiables con resultados que importan

> **Libro:** *Delivering Trusted Results with Outcomes That Matter*. Parte 3: Generar confianza con entregas basadas en valor.
> **Microproyecto:** Revisión de capacidades y reporte ejecutivo.

**Estado:** ✅ hecho

## Objetivo

Consolidar los resultados del programa de NovaMercado y comunicarlos de forma que generen confianza:
- la **revisión de capacidades** del libro (6 capacidades × 5 etapas), con un estado que sale de la **evidencia** de los capítulos 1 a 15;
- los compromisos del capítulo 5 frente a lo realmente medido;
- un mensaje estructurado para cada desvío;
- un mensaje adaptado a cada audiencia.

Todo se reúne en un informe HTML consolidado.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| Revisión de capacidades: Definir, Documentar, Analizar, Optimizar, Sostener y probar | Gobierno, metadatos, calidad, arquitectura y operaciones (las del libro) más datos primarios | [inputs/review.yaml](inputs/review.yaml) |
| Cada etapa tiene un entregable y un impacto para el stakeholder | El estado de cada etapa se comprueba en el warehouse, el registro de operaciones o los inputs | [evidence.py](evidence.py) |
| Coherencia entre lo prometido y lo entregado | Compromisos del capítulo 5 medidos de nuevo, con su fecha | [results.py](results.py) |
| Comunicar los desvíos: proactivo, con claridad, contexto, solución y plan | Mensaje por desvío: qué ha pasado, por qué, qué vamos a hacer (responsable y fecha) y qué ajustamos | [results.py](results.py) |
| "Fallar construye confianza": no pintar todo de verde | Se separan los compromisos en plazo, los riesgos anticipados y los retrasos, y se cuentan los que no tienen causa raíz | [results.py](results.py) |
| Mensajes a medida de cada audiencia, sin jerga | Comité de dirección, directores y stewards; el mensaje ejecutivo pasa la revisión de jerga del capítulo 12 | [run.py](run.py) |

## Entregables (`outputs/`)

| Archivo | Contenido |
|---|---|
| `capability_review.html` | Informe autocontenido (modo claro y oscuro): resumen, mapa de capacidades, detalle por etapa con su evidencia, compromisos frente a resultados, mensajes de desvío y mensajes por audiencia |
| `capability_matrix.png` | Matriz de capacidades × etapas (también incrustada en el HTML) |

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch11_operaciones_datos.pipeline   # warehouse completo y registro de operaciones
uv run python -m chapters.ch16_resultados_confiables.run
uv run pytest chapters/ch16_resultados_confiables
```

Abre `outputs/capability_review.html` en el navegador. Si falta un capítulo en el warehouse, sus etapas aparecen como pendientes: el estado nunca se declara a mano.

## Decisiones de modelado

- **30 comprobaciones de evidencia,** una por etapa. Por ejemplo:
  - Documentar metadatos = % de tablas documentadas.
  - Analizar calidad = reglas que cumplen su umbral.
  - Sostener operaciones = ejecuciones registradas del pipeline.
  - Optimizar operaciones = valor de las automatizaciones frente al coste de la plantilla nueva.
  - Sostener datos primarios = adopción del cliente único (capítulo 15).

  Algunas reutilizan directamente el código de otros capítulos: la validación del linaje del 7, el linter del 9 y la simulación de adopción del 15.
- **Cuatro estados para cada compromiso**, porque no todo lo incumplido es un desvío:
  - **cumplido**;
  - **en plazo**: no ha vencido;
  - **riesgo anticipado**: no ha vencido, pero ya se ve el desvío, y se comunica antes, como pide el libro;
  - **retrasado**: ha vencido, con o sin causa raíz.

  La primera versión marcaba como "sin causa raíz" la clasificación de PII, que no vence hasta julio.
- **Datos primarios como sexta capacidad:** el libro revisa cinco. Se añade la del capítulo 10 porque es la que más valor aporta a la CMO.

## Conclusiones para NovaMercado

1. **Están entregadas 22 de las 30 etapas.** Las capacidades fallan sobre todo en *Optimizar* y *Sostener*: es fácil definir y documentar, y lo difícil es que los cambios lleguen al origen y se mantengan.
2. **Las etapas parciales señalan el trabajo pendiente:**
   - la definición de "cliente activo" sigue sin aprobar;
   - la narrativa de la cifra de ventas no coincide con su linaje;
   - solo el 32 % de las columnas está ligado al glosario;
   - solo el 41 % de las reglas de calidad cumple su umbral, y 9 de 10 incidencias siguen abiertas;
   - el warehouse cumple 8 de 10 estándares de arquitectura;
   - el valor de las automatizaciones no cubre aún el coste de la plantilla nueva;
   - el valor firmado está pendiente en el resultado del CFO.
3. **Compromisos de datos:** 4 de 9 cumplidos, 1 en plazo, 3 riesgos anticipados y 1 retrasado (los stewards de cliente), todos con causa, plan, responsable y fecha. **No queda ningún retraso sin explicar.**
4. **El mensaje al comité cabe en tres frases sin jerga:** qué se ha cumplido, qué ya usa el negocio y qué falta para que la cifra de ventas sea oficial.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada
- [x] Paso añadido al recorrido del README raíz

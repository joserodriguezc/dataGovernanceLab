# Capítulo 12: Lanzar con fuerza

> **Libro:** *Launch Powerfully*. Parte 3: Generar confianza con entregas basadas en valor.
> **Microproyecto:** Kit de lanzamiento del programa.

**Estado:** ✅ hecho

## Objetivo

Preparar el lanzamiento del programa de gobierno de datos de NovaMercado:
- evaluar si el **negocio** está preparado;
- construir un mensaje simple (visión, as-is frente a to-be y una versión por audiencia);
- escribir el **memo narrativo** (North Star) sin jerga de datos;
- dejar un proceso repetible de comunicación y de feedback.

Todo se apoya en lo construido en los capítulos 1 a 10, y el lanzamiento anuncia victorias **ya entregadas**.

## Ideas del capítulo que aplicamos

| Idea del libro | Cómo la aplicamos | Módulo |
|---|---|---|
| Evaluar la preparación del negocio en 5 dimensiones: función de datos, confianza, capacidades, madurez y liderazgo | Cada dimensión (1-5) se calcula con una fórmula explícita sobre la evidencia de los capítulos 2, 3, 4, 6, 7, 8 y 10 | [readiness.py](readiness.py) |
| El perfil de preparación decide *cómo* lanzar | Recomendaciones empezando por la dimensión más débil | [readiness.py](readiness.py) |
| Mensaje simple: visión, as-is frente a to-be en una página | Visión y misión del capítulo 1; 5 pares as-is/to-be en términos de negocio | [inputs/launch.yaml](inputs/launch.yaml) |
| Mensajes por audiencia: colaboradores, mandos y comité de dirección | Necesidades, formato y cadencia de cada una | [inputs/launch.yaml](inputs/launch.yaml) |
| Memo narrativo: por qué cambiar, qué cambia, cómo y quién participa | Generado con el valor (1), los sponsors (2), la madurez (4), los resultados (5) y la arquitectura (9) | [templates/narrative_memo.md.j2](templates/narrative_memo.md.j2) |
| Que un no especialista lea la estrategia y señale la jerga; menos de 10 páginas | Revisión automática: términos de datos y número de palabras | [messaging.py](messaging.py) |
| Diseñar a partir de los resultados de negocio | El memo presenta resultados y valor, no capacidades | [templates/narrative_memo.md.j2](templates/narrative_memo.md.j2) |
| Proceso repetible: memo, plan, actualizaciones, estado, presupuesto y KPI | Plan de comunicación con responsables | [inputs/launch.yaml](inputs/launch.yaml) |
| Bucles de feedback: foros, encuestas y flujo de trabajo | Canales y cómo se usan | [inputs/launch.yaml](inputs/launch.yaml) |
| Fijar expectativas: "antes no podías, ahora puedes" | Hitos de negocio para cada entrega | [inputs/launch.yaml](inputs/launch.yaml) |
| No esperar al lanzamiento: llegar con una victoria ya entregada | Victorias medidas en el warehouse | [messaging.py](messaging.py) |

## Entregables (`outputs/`)

| Archivo | Contenido |
|---|---|
| `narrative_memo.md` | Memo de estrategia para toda la empresa |
| `launch_plan.md` | Preparación y enfoque, mensaje central, audiencias, revisión del memo, comunicación, feedback, expectativas y victorias ya entregadas |
| `launch_readiness.png` | Las cinco escalas de preparación con la posición actual |

## Cómo ejecutarlo

```bash
uv run python -m chapters.ch11_operaciones_datos.pipeline   # warehouse completo (capítulos 6, 7, 8 y 10)
uv run python -m chapters.ch12_lanzamiento.run
uv run pytest chapters/ch12_lanzamiento
```

Sin los capítulos 6 a 10 en el warehouse, la preparación baja y el memo no tiene victorias que anunciar.

## Decisiones de modelado

- **Preparación medida, no opinada.** Así se calcula cada dimensión:
  - **Función de datos:** plantilla cubierta del equipo diseñado en el capítulo 3.
  - **Confianza:** datasets curados certificados (capítulo 8).
  - **Capacidades:** media de documentación, linaje, controles de calidad superados y cliente único.
  - **Madurez:** la puntuación del capítulo 4, llevada de la escala 1-6 a 1-5.
  - **Liderazgo:** CDAO en plantilla, sponsor identificado, financiación aprobada y al menos dos apoyos en el comité de dirección.
- **Un solo origen para cada contenido.** El memo no repite cifras a mano: la visión y el caso de negocio vienen del capítulo 1, los resultados y su valor del 5 y lo que se retira del 9. Si cambia un capítulo, el memo cambia.
- **El roadmap técnico del capítulo 9 no entra en el memo.** Está lleno de términos como "golden record" o "SDLC"; en su lugar van los hitos de negocio ("ahora podrás...").
- **La revisión de jerga reutiliza la lista del capítulo 1,** ampliada con "PII". Detectó dos problemas reales en los hitos ("Golden record de cliente en producción" y "Clasificación de PII"), que se reescribieron.

## Conclusiones para NovaMercado

1. **El perfil de preparación es desigual:** liderazgo 5,0 y capacidades 4,9 (los capítulos 6 a 10 ya funcionan), pero función de datos 3,0, madurez 2,0 y confianza 1,8.
2. **Hay que lanzar empezando por la confianza.** Solo 1 de los 5 datasets curados está certificado. El caso de uso con el que abrir es la cifra de ventas en la que la dirección no confía (capítulos 2, 7 y 8).
3. **El memo ocupa 666 palabras, sin jerga,** y se apoya en un argumento claro: los datos cuestan hoy US$ 1,01 M al año más de lo que aportan, y el programa se recupera en el mes 21.
4. **NovaMercado llega al lanzamiento con 4 victorias entregadas:** el cliente único, el catálogo, el origen de la cifra de ventas y los controles en cada carga. Es lo que el libro recomienda para generar confianza desde el primer día.

## Definición de hecho

- [x] `run.py` genera todos los entregables en `outputs/`
- [x] Tests en verde
- [x] Este README documenta las decisiones y las conclusiones
- [x] Checklist de `PLAN.md` actualizada
- [x] Paso añadido al recorrido del README raíz

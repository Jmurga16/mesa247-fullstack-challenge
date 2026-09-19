# Auditoría del análisis previo — Mesa247

Fecha: 16 de septiembre de 2026.

## Para qué sirve esta carpeta

Contiene la revisión crítica del análisis previo del proyecto, realizada con asistencia de IA y desde la perspectiva de arquitectura y liderazgo técnico.

**Estado: cerrado el 16/09/2026.** Los hallazgos ya se resolvieron y se aplicaron a los documentos originales.
La disposición de cada uno —aplicado, aceptado con límite o rechazado con argumento— está en
[02 · Resolución de hallazgos](02_resolucion_de_hallazgos.md).

El informe se conserva tal como se escribió, con fecha, porque es la trazabilidad de por qué el diseño cambió.
No es un plan alternativo: **el alcance y el contrato vigentes están en [09_alcance_y_plan_de_implementacion.md](../analisis/09_alcance_y_plan_de_implementacion.md)**.

## Orden de lectura

1. [02 · Resolución de hallazgos](02_resolucion_de_hallazgos.md): qué se decidió con cada hallazgo y dónde quedó. **Empieza por aquí.**
2. [01 · Informe de auditoría](01_informe_de_auditoria.md): el informe original, con el detalle y la evidencia de cada hallazgo. Útil si quieres el razonamiento completo.

## Dictamen

La arquitectura base es razonable: FastAPI + React, un servicio, polling, SQLite local y cuatro tablas para el corte. No se recomienda sustituirla, y no se sustituyó.

Los cuatro problemas críticos que había que resolver antes de implementar, hoy resueltos:

| ID | Hallazgo crítico | Consecuencia |
|---|---|---|
| C1 | Recuperación del turno activo mediante teléfono, sin acreditar posesión | Un tercero podría obtener el token y cancelar un turno ajeno. |
| C2 | Contrato incompleto de acciones y efectos comunes | API, estados, eventos y restricciones pueden comportarse de forma distinta. |
| C3 | Cierre de servicio subordinado al reporte | Turnos antiguos pueden persistir y bloquear nuevas altas. |
| C4 | Corte demasiado amplio y recortes inconsistentes | Riesgo de exceder el timebox de 4 horas o dejar piezas sin terminar. |

También se identificaron nueve hallazgos importantes y cinco menores. Los identificadores C1–C4, I1–I9 y M1–M5 se mantienen en ambos documentos para facilitar el seguimiento.

Una recomendación se **rechazó con argumento**: retirar el tiempo estimado (ETA) del corte de cuatro horas (I2). El encargo lo pide de forma explícita, así que omitirlo sería incumplir un requisito, no recortar con criterio. Se implementa etiquetado como aproximado y no calibrado.

## Alcance y límites

- Se leyó primero [00_contexto_del_analisis.md](../analisis/00_contexto_del_analisis.md) y después todo el conjunto documental: `01` a `08`, el DDL, el diagrama PNG y los cuatro archivos de `prompts/`.
- Se contrastó el análisis con el [enunciado publicado](https://prueba-fullstack-mesa247.pages.dev/).
- Se consultaron fuentes oficiales para algunos puntos de MySQL, Cloud Run, Cloud Tasks y WhatsApp. Están enlazadas junto al hallazgo correspondiente.
- La revisión es estática: no se ejecutó el DDL contra MySQL ni se verificó una implementación de la aplicación.
- Los escenarios de fallo describen consecuencias del diseño documentado; no son vulnerabilidades reproducidas sobre código existente.
- El informe original no corrigió los documentos; la corrección se hizo después y está registrada en el documento 02.

## Cómo compartirlo

Para una lectura autónoma, comparte `01_informe_de_auditoria.md` y `02_resolucion_de_hallazgos.md`. Para que funcionen los enlaces a la evidencia, comparte la carpeta `mesa247-docs` completa, conservando su estructura.

El material original contiene referencias personales y de otros proyectos. Revisa esa información antes de compartir la carpeta completa.

Esta carpeta es un anexo de trabajo; no sustituye la nota técnica de una o dos páginas.

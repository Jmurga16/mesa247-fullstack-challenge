# Mesa247 · Lista de espera — Contexto del análisis

Análisis realizado el 15–16/09/2026, antes de escribir código.
Fuente del encargo: https://prueba-fullstack-mesa247.pages.dev/

## Qué es esto
Material de referencia para implementar la lista de espera: el análisis del problema, las propuestas
argumentadas y las decisiones que sostienen el corte. No es el código ni la nota técnica.

## Orden de lectura sugerido
1. 01_enunciado_checklist.md ............ lo que pide el encargo, en formato checklist
2. 02_lectura_del_problema.md ........... actores, hallazgos del prototipo, huecos, riesgos
3. 07_disenador_preguntas_y_devolucion.md  las 3 preguntas, supuestos y qué devolverle al diseñador
4. 05_alcance_estimaciones_y_orden.md ... qué construir, qué cortar, estimaciones y orden de ataque
5. 03_arquitectura_y_decisiones.md ...... arquitectura, decisiones (reversibles e irreversibles), qué rechazar
6. 04_modelo_de_datos.md ................ tablas, estados, transiciones, posición/ETA, consulta del reporte
   04b_modelo_de_datos_mysql.sql ........ DDL de referencia (MySQL 8)
   04c_diagrama_estados.png ............. diagrama de estados del turno
7. 06_produccion_y_tests.md ............. despliegue en GCP, alarmas, "viernes 9 pm", costos, tests que importan
8. 08_decisiones_y_preguntas_tecnicas.md  preguntas frecuentes sobre el diseño y conceptos del código
9. **09_alcance_y_plan_de_implementacion.md** ............ EL QUE MANDA al implementar: alcance obligatorio/opcional/fuera,
                                          matriz de acciones, contrato de API, tests y plan hora a hora
10. ../entrega_y_uso_de_ia.md ........... restricciones, entregables y declaración del uso de IA
11. ../conversaciones/ .................. registro de prompts, decisiones y conversaciones
12. ../auditoria/ ....................... la revisión crítica y qué se hizo con cada hallazgo

> Para ir directo a programar: basta el **09**. El resto es el porqué.
> Donde 00–08 contradigan al 09, manda el 09.

## La tesis en 10 líneas
1. Lo que decide el resultado es el criterio: qué se construye, qué se corta, qué se pregunta y qué no se puede deshacer. El código es la evidencia, no el fin.
2. Corte v1 del **piloto** = reemplazar el cuaderno: unirse por QR (y alta manual del anfitrión), ver el turno con polling, cola del anfitrión con Llamar / Sentar / No vino, y cada evento registrado desde el día 1. En el **corte de 4 horas**, el alta manual es lo primero de la lista de opcionales (09 § 2.2): valiosa, pero no bloquea el flujo punta a punta.
3. Fuera del código: WhatsApp real, arrastrar para reordenar, cliente frecuente y reporte por correo. Se explican con estimación y dependencia (la aprobación de la plantilla de Meta es la dependencia externa crítica).
4. Sin WebSocket: polling (wifi malo en la puerta; en Cloud Run con varias instancias exigiría Redis). Se puede cambiar después sin tocar el dominio.
5. Sin arrastrar en el piloto: poder "Llamar" a cualquier fila ya permite priorizar al frecuente, sin conflictos entre dos anfitriones ni números que suben.
6. Difíciles de deshacer, en tres niveles: lo que **no se recupera** (los eventos que no se capturaron, el consentimiento que no se pidió); lo **caro y externo** (la URL del QR impreso, la plantilla y el remitente de WhatsApp, los mensajes ya enviados); y lo **interno pero costoso** (normalización E.164, definiciones de métricas, modelo de tiempo, location_id en todo). Decir "irreversible" de los nueve por igual es más débil que separarlos.
7. Lo que hay que resolver bien: transiciones atómicas (dos anfitriones), alta idempotente por request_id y que **no entrega el turno a quien solo sabe el teléfono**, tokens no adivinables, Santiago en UTC-3 desde el 6/09, cobro de WhatsApp que cambia el 1/10/2026 (sin confirmar en el rate card: se cita como aviso de proveedores), alarma de "silencio" del negocio un viernes a las 9 pm.
8. Tests solo de fallos, seis no negociables (09 § 7.1): reintento del alta y no-filtración del token, doble llamado, transiciones inválidas, aislamiento entre locales, liberación de la clave activa en todo estado terminal, normalización de teléfonos.
9. Tres conversaciones separadas desde el inicio (nota, backend, frontend), empezando por preguntas y datos, con rechazos explícitos.
10. Backend simple (SQLAlchemy síncrono) y pocas dependencias: todo lo que entra hay que poder explicarlo y mantenerlo.

## Organización actual

La documentación está en `mesa247-docs/`; el código va en las carpetas hermanas `mesa247-api/` y
`mesa247-web/`. Consulta el [README principal](../README.md) para navegar por los documentos.

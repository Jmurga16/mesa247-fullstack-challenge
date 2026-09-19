Documentos creados y modificados
Creado (1)

09_alcance_y_plan_de_implementacion.md — el único que necesitas abierto al programar: alcance obligatorio/opcional/fuera, matriz de acciones, contrato de API con formas de respuesta, deltas del modelo, tests y plan hora a hora. Declara explícitamente que manda sobre 00–08.
Modificados (13)

00_contexto_del_analisis.md — orden de lectura con el 09; tesis 2, 6, 7 y 8 realineadas.
02_lectura_del_problema.md — H1/H3/H17 separan observación de inferencia; S5 corregido; dos riesgos nuevos.
03_arquitectura_y_decisiones.md — contrato de API, regla anti-IDOR del alta, D3/D5/D8/D13/D17/D18/D22 reescritas, D23 nueva (OIDC), §6 reversibilidad en tres niveles, tabla de rechazos ampliada.
04_modelo_de_datos.md — active_key con service_date, desempate (sort_key, id), §3.1 invariante, matriz de transiciones, límites del reporte, índices.
04b_modelo_de_datos_mysql.sql — colación binaria, VARCHAR(64), índice de cola con service_date, consultas corregidas.
05_alcance_estimaciones_y_orden.md — contradicciones de alcance resueltas, bloques de tiempo recalculados, margen del piloto declarado.
06_produccion_y_tests.md — 4 alarmas prioritarias, límites de alarmas, IAM por servicio, retención por tipo de dato, tests repriorizados, costos suavizados.
07_disenador_preguntas_y_devolucion.md — P3 ampliada con "¿puede alejarse el comensal?".
08_decisiones_y_preguntas_tecnicas.md — 7 preguntas nuevas sobre el diseño y cifras de WhatsApp acotadas.
prompts/00, A, B, C — alineados al alcance congelado; quitadas las "respuestas esperadas".
auditoria/README.md y auditoria/01_INFORME — marcados como cerrados.
auditoria/02_resolucion_de_hallazgos.md — reemplazado por la resolución de cada hallazgo. Era el riesgo mayor del set: un plan alternativo compitiendo con los originales.
No borré nada. El .png queda con una nota: le falta una flecha y el Mermaid es la fuente válida.

Decisiones que cambié o confirmé
Cambiadas

El alta pública nunca devuelve el token de un turno existente. Con el QR pegado en la puerta, quien conozca un teléfono podía cancelar turnos ajenos. Ahora: request_id del navegador para idempotencia, 409 sin token para deduplicación. Es la corrección más importante del conjunto.
active_key incluye service_date y la cola filtra por día. Sin eso, el pendiente del viernes bloquea a ese teléfono el sábado.
Alta manual y «Voy en camino» pasan a opcionales, y salen de la definición de listo. Estaban como obligatorios en unos documentos y recortables en otros.
Alembic fuera de las 4 horas. 15–20 min que no compran nada en local.
Consentimiento sin casilla. La casilla contradecía tu propia tesis (El Libro murió por fricción). Tensión legal declarada, no escondida.
«Se fue» solo desde waiting. Desde called la acción correcta es «No vino»; dos caminos al mismo hecho rompen el reporte.
Desempate (sort_key, id). Con reloj congelado en tests, el empate es seguro, no improbable.
Hook propio, no TanStack Query; CSS plano, no Tailwind. Decisiones que estaban abiertas y te costarían tiempo a mitad del build.
Confirmadas

Arquitectura FastAPI + React/TS + SQLite: correcta para el stack y para 4 horas. No la toqué.
Polling sobre WebSocket: bien decidido, mal justificado. Arreglé el argumento (Cloud Run no exige Redis; exige alguna sincronización).
Rechacé una recomendación de la auditoría previa: quitar el ETA. El encargo lo pide de forma explícita; no entregarlo se lee como incumplimiento, no como criterio. Se queda, etiquetado como aproximado y no calibrado.
Riesgos y dudas que quedan
El plan de 4:00 sigue sin margen, incluso con el alcance reducido. Lo realista es 4:30–5:00. Está declarado en el 09.
Las tarifas de WhatsApp del 1/10/2026 no están verificadas en el rate card de Meta, ni por la auditoría previa ni por mí. No las cites como hecho.
"Espera media" del prototipo sigue sin cuadrar con sus propias filas. Es la pregunta 2 al diseñador; el supuesto está declarado.
¿El reporte cuenta grupos o personas? El modelo cuenta grupos, el encargo habla de gente. No afecta al código, pero hay que decidirlo antes de la primera semana del piloto.
El cierre del día sigue sin implementar. Mitigado por el filtro de service_date, pero los pendientes quedan abiertos. Es deuda declarada.
La documentación es extensa para un corte de 4 horas (~210 KB, 18 archivos). No es un problema para el código, pero sí lo es si se intenta volcar entera en una nota de 1–2 páginas.
Orden para empezar
config.py · db.py (PRAGMA de SQLite: WAL y busy_timeout, o la demo se bloquea con dos tablets) · main.py + /healthz
models.py con create_all
domain/time.py (reloj inyectable + service_date) → domain/phones.py → domain/queue.py (transiciones + invariante)
auth.py → notifier.py
routers/public.py → routers/host.py
seed.py
Los seis tests no negociables
Punto de control a las 1:50: si pytest no está en verde, corta opcionales del frontend antes de empezarlo
api.ts + usePolling.ts → JoinPage → TicketPage → HostPage
README + clon limpio cronometrado → nota técnica
Qué NO implementar en este corte
WhatsApp/SMS reales, webhook de Meta, outbox, Cloud Tasks · cierre del día automático · reporte y correo · arrastrar para reordenar · cliente frecuente · re-llamar y deshacer llamado · pausar la lista · panel de administración · login por persona · rate limiting · Alembic · servir el build de React desde FastAPI · Docker · CI/CD · i18n · asignación de mesas.

Y los cuatro opcionales — alta manual, «Voy en camino», botón de borrar, animación — solo si las doce piezas obligatorias están cerradas. Si algo de lo obligatorio está a medias, ninguno de los cuatro se empieza.
# Resolución de los hallazgos de auditoría

Fecha de resolución: 16/09/2026.
Estado: **cerrado**. Cada hallazgo del [informe](01_informe_de_auditoria.md) tiene aquí una decisión —
aplicado, aceptado con límite explícito, o rechazado con argumento— y dónde quedó.

Este archivo sustituye a la versión anterior, que proponía cambios sin aplicarlos. Mantener a la vez un
plan original y un plan alternativo era el mayor riesgo del set: obligaba a reconciliarlos mentalmente
justo cuando hay que escribir código. Las decisiones viven ahora en los documentos originales y, cuando
son de alcance o contrato, en **[09_alcance_y_plan_de_implementacion.md](../analisis/09_alcance_y_plan_de_implementacion.md)**.

## 1. Críticos

| ID | Decisión | Dónde quedó |
|---|---|---|
| C1 · Turno ajeno por conocer el teléfono | **Aplicado.** El alta pública lleva `request_id` (uuid del navegador, guardado antes de enviar). Mismo `request_id` → mismo turno, incluso si ya terminó. Mismo teléfono con otro `request_id` → **409 sin token**. Idempotencia y deduplicación quedan separadas y nombradas así. Sin OTP: sería reinventar el login que mató la lista de El Libro. | 09 §4–5 · 03 §4 (reglas HTTP, D8, D18) · 04 §2 y §3.1 · 04b · 06 T1a/T1b · prompts B3/C2 |
| C2 · Contrato de acciones incompleto | **Aplicado.** Matriz única con actor, origen, destino, efectos y política de repetición. Invariante común: todo estado terminal fija `status`, `closed_at` y `active_key = NULL` en el mismo UPDATE, con el evento en la misma transacción. `leave` solo desde `waiting`; `remove` desde `waiting` y `called`; `on-my-way` marca solo la primera vez. | 09 §4 · 04 §3 y §3.1 · 03 §4 y D22 |
| C3 · Ciclo diario supeditado al reporte | **Aplicado en lo que toca al corte.** `service_date` entra en `active_key` y en la consulta de la cola: el pendiente de ayer ni aparece hoy ni bloquea ese teléfono. El cierre automático sigue en fase 2, pero se separa del correo: el cierre existe desde el día 1 del piloto aunque sea manual. | 09 §2.4, §3 y §9.1 · 04 §2 y §8 · 04b · 05 §3 |
| C4 · Corte demasiado amplio | **Aplicado.** Doce piezas obligatorias, cuatro opcionales ordenadas, una lista explícita de lo que no se escribe. Alembic, rate limiting y servir el build desde FastAPI salen del corte. Alta manual y «Voy en camino» pasan a opcionales y desaparecen de la definición de listo. Bloques de tiempo recalculados y declarados sin margen. | 09 §2 y §8 · 05 §1, §2, §4, §5 · 00 tesis · prompts B y C |

## 2. Importantes

| ID | Decisión |
|---|---|
| I1 · El reporte puede cuadrar y medir mal | **Aplicado.** El reporte separa desenlaces confirmados de cierre administrativo (`expired` y los `called` sin resolver no son hechos observados). Se añade que el modelo cuenta grupos y el encargo habla de personas, y que la espera media solo mide a quienes se quedaron. → 04 §6 |
| I2 · Inferencias del prototipo como hechos | **Aplicado, con una discrepancia.** H1, H3 y H17 quedan marcados como observación / inferencia / supuesto, y el 78 % de llamados como supuesto de presupuesto. **Se rechaza retirar el ETA del corte**: el encargo lo pide de forma explícita ("un tiempo estimado"), y no entregarlo se lee como no cumplir un requisito, no como recortar con criterio. Se entrega etiquetado como aproximado y no calibrado, guardando lo prometido para medir el error. → 02 H1/H3/H17 · 04 §4 · 06 §5 · 09 §2.4 |
| I3 · Orden sin desempate y texto ambiguo | **Aplicado.** Se ordena y se cuenta siempre por `(sort_key, id)`. Texto público congelado en "Hay N grupos antes que ti". `sort_key` se conserva, pero con la justificación correcta: reordenar es un requisito del diseñador aplazado, no rechazado — "evitar una migración" era un argumento flojo. Se reconoce que los huecos entre enteros se agotan. → 04 §2 y §4 · 03 D5 · 09 §3 |
| I4 · Garantías de entrega excesivas | **Aplicado.** Se abandona toda formulación de "exactamente una vez": la promesa es una sola *transición*, y el envío es "al menos una vez con deduplicación por `attempt_key` y resultado a veces incierto". Se nombran los cuatro fallos (muerte tras el commit, respuesta perdida, tarea no creada, correo sin marcar). Deshacer y re-llamar quedan fuera. → 03 D13 · 04 §3 · 08 |
| I5 · DDL vs modelo documentado | **Aplicado.** Colación binaria en `public_token`, `token_hash` y `public_code`; `active_key` a `VARCHAR(64)`; índice de cola con `service_date`; techo del dato (50) separado del límite de negocio (`max_party_size`); UTC escrito por la aplicación, no por `DEFAULT`; `day_cutoff_hour` leído de la fila. **Aceptado con límite**: `ticket_events.location_id` se deriva del ticket en un único punto del código, sin FK compuesta — no vale la complejidad con cuatro tablas. La prueba en MariaDB se declara como evidencia parcial. → 04b · 04 §2 y §8 · 09 §3 |
| I6 · `/internal/*` no lo protege su nombre | **Aplicado.** El permiso de Cloud Run es por servicio, no por ruta: la aplicación verifica el token OIDC (emisor, audiencia y cuenta de servicio). En el corte de 4 horas no hay endpoints internos. → 03 D23 · 06 §6 |
| I7 · Retención y credenciales incompletas | **Aplicado.** La retención se define por tipo de dato, no por columna (nombre, JSON de eventos, payloads, logs, respaldos). Se admite que limpiar el token de la URL desde JS es cosmético y que Cloud Run registra la query string; el link fijo del seed es una comodidad local que no viaja al piloto. → 06 §6 · 09 §9.9 · prompt C4 |
| I8 · Tests desalineados con el corte | **Aplicado.** Seis no negociables, encabezados por idempotencia + no-filtración del token y por la liberación de `active_key` en todo estado terminal (parametrizado). Cinco más si alcanza. Se conserva un test integrado del camino feliz. → 09 §7 · 06 §7 · prompt B6 |
| I9 · Preguntas con producto por precisar | **Parcialmente aplicado.** Las tres preguntas se conservan (están bien elegidas y ya llevan su supuesto), pero P3 se amplía con la mitad que faltaba: **si el comensal puede alejarse**. El polling pausado no despierta un teléfono bloqueado, así que WhatsApp no es un canal más — es el único que alcanza a quien se fue a caminar. Si Meta rechaza la plantilla, la regla del piloto pasa a ser "quédate cerca" + llamado por voz. → 07 P3 · 08 |

## 3. Menores

| ID | Decisión |
|---|---|
| M1 · "Irreversible" demasiado amplio | **Aplicado.** Tres niveles: lo que no se recupera (datos no capturados, consentimiento no pedido), lo caro y externo (QR impreso, plantilla y remitente, mensajes enviados), lo interno pero costoso (E.164, métricas, modelo de tiempo, multi-local). Se añade que E.164 normaliza el contacto, no la identidad de una persona. → 03 §6 · 00 tesis · 08 |
| M2 · Polling bien elegido, mal justificado | **Aplicado.** Cloud Run no exige Redis: exige alguna forma de repartir eventos entre instancias, y Redis es una opción. La defensa se reduce a lo que se sostiene: para esta cola una demora de segundos es aceptable y el polling la consigue con mucho menos. → 03 D3 |
| M3 · Costos con más certeza que evidencia | **Aplicado.** Los 400 req/s se declaran escenario, no medición (omiten tablets e intervalos acelerados). El cambio de tarifas del 1/10/2026 se cita como aviso de proveedores pendiente de confirmar en el rate card. Se añade que Meta cobra por mercado del destinatario, no por país del local. → 06 §5 · 08 P8 · 02 §5 |
| M4 · Precisiones de datos y operación | **Aplicado.** `SUM`/`AVG` sin filas devuelven NULL: "sin datos" y "cero" se muestran distinto. Las alarmas porcentuales necesitan volumen mínimo y horario, y "cero altas" no prueba caída sin línea base. → 04 §6 · 06 §3 · 09 §5.2 |
| M5 · Prompts demasiado guionizados | **Aplicado.** Advertencia al inicio de `prompts/00`: son checklist de contexto, no libreto; si la IA acierta a la primera, se acepta. Se quitan las "respuestas esperadas" de A4 y A1. → prompts/00 §3 · prompts/A |

## 4. Lo que la auditoría no vio y se corrigió igual

Hallazgos propios de esta pasada, ya aplicados:

1. **SQLite sin WAL se bloquea en la demo.** Dos pestañas de tablet escribiendo a la vez dan "database is
   locked". `journal_mode=WAL` + `busy_timeout` + `check_same_thread=False`. → 03 §2 · 09 §6
2. **El bloque de backend no cabía en 70 minutos**: eran ~11 endpoints, 4 modelos y 7 tests. Se subió a 80,
   se redujo el alcance y se puso un punto de control a las 1:50. → 05 §4 · 09 §8.4
3. **La casilla de consentimiento contradecía la tesis del propio análisis** (la lista de El Libro murió por
   fricción). Pasa a aviso visible + consentimiento por acción, con la tensión legal declarada. → 03 D18 · 09 §2.4
4. **La nota es de 1–2 páginas y el material da para diez.** Cuatro alarmas prioritarias en vez de diez,
   y el resto como catálogo de operación. → 06 §3
5. **`GET /host/queue` no tenía forma de respuesta definida**, ni el turno público tampoco: se congelaron
   ambas, con `server_now` para que las cuentas regresivas no dependan del reloj del celular. → 09 §5
6. **Faltaban edge cases operativos** que van a aparecer la primera semana del piloto: cambiar el tamaño de
   un grupo, un teléfono para dos familias, "Llamar" y "Sentar" simultáneos. → 09 §9 · 04 §3 · 08

## 5. Lo que sigue abierto

No se resolvió, y no bloquea empezar a programar:

- **La definición de "espera media" del encabezado del prototipo** sigue sin cuadrar con sus propias filas.
  Es parte de la pregunta 2 al diseñador; el supuesto (espera real de los sentados del día) está declarado.
- **El origen del dato "cliente frecuente"** sigue indefinido. Está fuera del piloto, así que no bloquea.
- **La verificación del cambio de tarifas de WhatsApp del 1/10/2026.** Esta auditoría tampoco pudo
  confirmarlo en el rate card oficial. No se cita como verificado en ningún documento ni debe
  presentarse como tal.
- **Si el reporte cuenta grupos o personas.** Hay que decidirlo antes de la primera semana del piloto:
  cambiarlo a mitad invalida la comparación. No afecta al código del corte.

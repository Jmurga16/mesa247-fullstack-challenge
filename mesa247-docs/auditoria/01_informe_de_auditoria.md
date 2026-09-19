# Informe de auditoría del análisis previo

**Proyecto:** Mesa247 — «El encargo».  
**Fecha:** 16 de septiembre de 2026.  
**Estado:** **cerrado.** Los hallazgos se resolvieron; ver [02 · Resolución de hallazgos](02_resolucion_de_hallazgos.md).
Este informe se conserva como estaba, con su fecha: es la trazabilidad, no el plan vigente.
El alcance y el contrato que mandan hoy están en [09_alcance_y_plan_de_implementacion.md](../analisis/09_alcance_y_plan_de_implementacion.md).  
**Método:** revisión documental completa, contraste con el enunciado y análisis adversarial de los flujos. No se ejecutó el DDL ni se auditó código implementado.

## 1. Evaluación general

**La arquitectura base es razonable y conservaría su dirección. No empezaría a implementar siguiendo los documentos literalmente:** hay un problema de autorización en el alta, reglas incompletas entre API y estados, y un alcance mayor de lo que sugiere la etiqueta «corte mínimo».

La interpretación del encargo es correcta. El [enunciado](https://prueba-fullstack-mesa247.pages.dev/) pide explícitamente decidir qué se construye primero, qué se recorta y con qué argumento. También exige ejecución: un flujo completo y un README que permita levantarlo. Recortar no exime de hacer coherente y verificable lo que sí entra.

La recomendación principal es **conservar la arquitectura y reducir los compromisos**, cerrando antes seguridad, transiciones y funcionamiento entre días.

### Criterio de severidad

| Severidad | Significado |
|---|---|
| Crítico | Corregir la decisión o el contrato antes de implementar el flujo afectado. |
| Importante | Revisar y resolver explícitamente; algunos puntos de infraestructura bloquean producción, pero no la demo local. |
| Menor | Mejorar precisión; puede esperar si no afecta el corte implementado. |

### Material revisado

- [00 · Organización y tesis](../analisis/00_contexto_del_analisis.md).
- [01 · Enunciado y checklist](../analisis/01_enunciado_checklist.md).
- [02 · Lectura del problema](../analisis/02_lectura_del_problema.md).
- [03 · Arquitectura y decisiones](../analisis/03_arquitectura_y_decisiones.md).
- [04 · Modelo de datos](../analisis/04_modelo_de_datos.md).
- [04b · DDL MySQL](../analisis/04b_modelo_de_datos_mysql.sql).
- [04c · Diagrama de estados](../analisis/04c_diagrama_estados.png).
- [05 · Alcance, estimaciones y orden](../analisis/05_alcance_estimaciones_y_orden.md).
- [06 · Producción y tests](../analisis/06_produccion_y_tests.md).
- [07 · Preguntas y devolución al diseñador](../analisis/07_disenador_preguntas_y_devolucion.md).
- [08 · Decisiones y preguntas técnicas](../analisis/08_decisiones_y_preguntas_tecnicas.md).
- Prompts: instrucciones (`prompts/00_como_usar_los_prompts.md`, archivo histórico no incluido), nota (`prompts/A_conversacion_nota.md`, archivo histórico no incluido), backend (`prompts/B_conversacion_backend.md`, archivo histórico no incluido) y frontend (`prompts/C_conversacion_frontend.md`, archivo histórico no incluido).

## 2. CRÍTICO

### C1. Recuperación y control de turnos ajenos mediante teléfono

**Archivos involucrados:** [03, contrato público](../analisis/03_arquitectura_y_decisiones.md), [04, deduplicación](../analisis/04_modelo_de_datos.md), prompt B3 (`prompts/B_conversacion_backend.md`, archivo histórico no incluido), prompt C2 (`prompts/C_conversacion_frontend.md`, archivo histórico no incluido).

**Problema.** El alta pública devuelve el turno existente si el teléfono ya tiene uno activo. El frontend necesita su token para navegar a la pantalla del turno. Conocer un teléfono no acredita posesión ni autoriza a controlar ese turno.

**Escenario de fallo.** Carla tiene un turno activo. Un tercero conoce su teléfono y el código público del local, envía el formulario, recibe el mismo turno y lo cancela. La aleatoriedad del token no protege si otro endpoint lo entrega sin autorización.

También se confunden deduplicación e idempotencia: si el turno original ya terminó cuando llega un reintento tardío, la clave activa queda libre y puede crearse otro turno.

**Recomendación mínima.** Usar una clave aleatoria de solicitud también en el alta pública, conservarla en el navegador y devolver el resultado original al repetir esa solicitud. Una solicitud distinta con el mismo teléfono no debe revelar el token existente. Definir el comportamiento si se reutiliza la clave con otro contenido. La recuperación desde otro dispositivo puede quedar a cargo del anfitrión; no hace falta incorporar OTP al corte.

**Trade-off.** Se limita la recuperación automática sin aumentar la fricción del alta normal. La regla de un turno activo por teléfono sigue siendo una decisión de negocio, no autenticación.

### C2. Contrato incompleto de acciones y efectos comunes

**Archivos involucrados:** [03, API y reglas HTTP](../analisis/03_arquitectura_y_decisiones.md), [04, tabla de transiciones](../analisis/04_modelo_de_datos.md), [04c, diagrama](../analisis/04c_diagrama_estados.png), prompt B2 (`prompts/B_conversacion_backend.md`, archivo histórico no incluido), prompt C4 (`prompts/C_conversacion_frontend.md`, archivo histórico no incluido).

**Problema.** El Mermaid y el PNG coinciden sustancialmente, pero su relación con la API tiene vacíos:

- `/leave` promete «se fue sin sentarse», pero la transición del anfitrión solo está definida desde `waiting`. Falta el caso de alguien llamado que avisa en persona que se va.
- `/remove` aparece como acción general; el diagrama solo permite borrar desde `waiting`. Falta decidir qué hacer con un duplicado ya llamado.
- `on-my-way` mantiene `called`. La regla genérica de origen/destino no basta para conservar la primera marca y evitar eventos repetidos.
- `closed_at` y liberación de `active_key` se detallan en unas transiciones y no en todas. La intención global existe, pero falta una regla común inequívoca.
- No se explicita que el cambio de estado y el evento de negocio se confirman en la misma transacción.

**Escenario de fallo.** El frontend ofrece «Se fue» en una fila llamada, pero el backend rechaza la acción o la cuenta en otra categoría. Otro cierre puede dejar la clave activa ocupada y bloquear una nueva alta.

**Recomendación mínima.** Una matriz única de acción, origen, actor, destino, efectos y reintento. Todo estado terminal libera la clave activa, fija el cierre y registra el evento atómicamente. Las acciones que mantienen estado necesitan reglas propias de idempotencia.

### C3. El cierre de servicio sostiene la operación, no solo el reporte

**Archivos involucrados:** [03, cierre](../analisis/03_arquitectura_y_decisiones.md), [04, fecha y reporte](../analisis/04_modelo_de_datos.md), [04b, consultas de cola](../analisis/04b_modelo_de_datos_mysql.sql), [05, alcance y calendario](../analisis/05_alcance_estimaciones_y_orden.md).

**Problema.** La cola selecciona todos los `waiting/called`, sin fecha de servicio. La unicidad por teléfono tampoco distingue servicios. Esto requiere una política de resolución de pendientes, pero el cierre está en fase 2, pausar/cerrar admisiones está pospuesto y no se define recuperación si Scheduler falla.

**Escenario de fallo.** Un turno del viernes permanece abierto el sábado, sigue apareciendo y bloquea otra alta con ese teléfono. Filtrar solo la fecha ocultaría la fila, pero no liberaría la restricción.

Además, cerrar nuevas admisiones y resolver turnos existentes son acciones distintas. La semántica de `is_active` no está suficientemente definida para cubrirlas.

**Recomendación mínima.** Separar admisión, resolución de pendientes y envío del reporte. El correo puede esperar; el ciclo diario necesita una política desde el primer día del piloto, aunque sea manual y documentada. Para la demo puede declararse una sesión de servicio única, sin presentarla como operación diaria completa.

### C4. Corte demasiado amplio y recortes que no se propagan

**Archivos involucrados:** [00, tesis y tiempo](../analisis/00_contexto_del_analisis.md), [05, alcance y timebox](../analisis/05_alcance_estimaciones_y_orden.md), prompt B (`prompts/B_conversacion_backend.md`, archivo histórico no incluido), prompt C (`prompts/C_conversacion_frontend.md`, archivo histórico no incluido), [08, decisiones](../analisis/08_decisiones_y_preguntas_tecnicas.md).

**Problema.** La distinción entre el corte de 4 horas y el piloto está bien planteada en `05`, pero no se mantiene en todos los documentos:

- Alta manual: obligatoria en la tesis, opcional en `05`, requerida otra vez por el prompt frontend.
- «Voy en camino»: recortable en `05`, obligatorio en la definición de listo y en los prompts.
- Backend: setenta minutos para modelos, autenticación, estados, eventos, deduplicación, normalización, endpoints, fake, tests y seed.
- Frontend: setenta minutos para tres pantallas, polling robusto, errores, acciones, alta manual y revisión.
- Piloto: prácticamente quince días comprometidos y, simultáneamente, un día declarado como margen.

La complejidad principal está en la suma de compromisos funcionales y operativos, no en las tecnologías elegidas.

El enunciado tampoco establece que el análisis específico de la solución quede fuera de las cuatro horas. Conviene declarar el tiempo real distinguiendo planificación, investigación e implementación, sin asumir que el reloj empieza después del diseño.

**Recomendación mínima.** Definir alcance obligatorio y opcional. Los primeros candidatos a salir son ETA, animación, «Voy en camino», deshacer/rellamar e indicadores de cabecera. Conservar el flujo completo, seguridad, reintentos, cancelación/cierre básico y README verificable. Propagar el corte a los prompts y a la definición de listo.

## 3. IMPORTANTE

### I1. El reporte puede cuadrar y medir mal el abandono

**Archivos involucrados:** [02, H4](../analisis/02_lectura_del_problema.md), [04, métricas](../analisis/04_modelo_de_datos.md), [07, supuesto P2](../analisis/07_disenador_preguntas_y_devolucion.md).

Convertir todos los pendientes en abandonos o ausencias confunde resultado observado con falta de registro. Si el anfitrión sienta a alguien y olvida marcarlo, el cierre puede contarlo como «no vino». La igualdad contable se cumple y el resultado es falso.

También falta precisar:

- El modelo cuenta turnos/grupos; el encargo habla de gente. Contar personas requiere `party_size`.
- Cancelar después del llamado y no aparecer son hechos distintos, aunque se agreguen en un indicador.
- Excluir `removed` de «se unieron» significa contar altas válidas, no todos los registros creados.
- La espera media de sentados no representa la experiencia de quienes abandonaron.

**Recomendación.** Separar desenlaces confirmados y cierre administrativo. `expired` puede conservarse y mostrarse por separado. La partición del reporte es un test contable útil, pero no demuestra validez del indicador.

### I2. Inferencias del prototipo presentadas como hechos

**Archivos involucrados:** [02, H1/H3/H17](../analisis/02_lectura_del_problema.md), [04, ETA](../analisis/04_modelo_de_datos.md), [06, costos](../analisis/06_produccion_y_tests.md), prompt A1b (`prompts/A_conversacion_nota.md`, archivo histórico no incluido).

- Una fila llamada fuera de orden sugiere selección por mesa; no demuestra la causa.
- H3 supone que las siete filas no visibles llevan menos de quince minutos. No está demostrado y no se sostiene si hubo reordenamiento.
- «Puesto 7 ≈ 25 minutos» es ilustrativo; no mide capacidad real.
- `111/142` no demuestra un 78 % de llamados: el diseño permite sentar sin llamar.

El ETA de cuatro minutos por posición es una hipótesis, no una estimación conservadora validada. Si no se libera ninguna mesa, prometer cinco minutos al primero puede fallar ampliamente.

**Recomendación.** Retirar ETA del corte de cuatro horas o declararlo expresamente no calibrado. Distinguir observaciones, inferencias y supuestos en el análisis.

### I3. Orden sin desempate y texto público ambiguo

**Archivos involucrados:** [03, D4/D5](../analisis/03_arquitectura_y_decisiones.md), [04b, consultas](../analisis/04b_modelo_de_datos_mysql.sql), prompt C3 (`prompts/C_conversacion_frontend.md`, archivo histórico no incluido).

Dos altas pueden compartir milisegundo. Con `sort_key < actual`, ambas pueden recibir la misma posición y su orden relativo no queda determinado.

«Puesto N» y «N grupos antes que tú» difieren en uno. Con llamados fuera de orden, la segunda frase expresa antigüedad, no necesariamente el orden de atención. Además, insertar enteros entre vecinos no resuelve indefinidamente un futuro reordenamiento: se agotan los huecos.

**Recomendación.** Orden y conteo con el mismo desempate, por ejemplo llegada e ID. Elegir una sola semántica pública. Mantener `sort_key` es opcional; evitar una futura migración no justifica por sí solo esta decisión.

### I4. Garantías excesivas de entrega de notificaciones

**Archivos involucrados:** [03, D13](../analisis/03_arquitectura_y_decisiones.md), [04, outbox y reportes](../analisis/04_modelo_de_datos.md), [04b, fase 2](../analisis/04b_modelo_de_datos_mysql.sql), [08, doble llamado](../analisis/08_decisiones_y_preguntas_tecnicas.md).

El UPDATE condicional evita dos transiciones simultáneas `waiting → called`. No demuestra entrega exactamente una vez al proveedor.

| Fallo | Consecuencia |
|---|---|
| Commit de `called` seguido de caída antes del BackgroundTask | No sale el aviso. |
| Proveedor acepta el mensaje, pero se pierde la respuesta | Reintentar puede duplicarlo. |
| Outbox confirmada, creación de Cloud Tasks fallida | Hace falta volver a despachar pendientes. |
| Correo enviado, caída antes de escribir `emailed_at` | La PK del reporte no evita repetir el envío. |

[Cloud Tasks documenta ejecuciones duplicadas](https://docs.cloud.google.com/tasks/docs/common-pitfalls). La solución debe admitirlas.

La deduplicación de webhooks también necesita precisar `external_id`: si representa solo el mensaje, puede descartar actualizaciones legítimas posteriores de ese mensaje. Se deben distinguir duplicados y cambios de estado, y tolerar llegada fuera de orden.

Deshacer/rellamar añade respuestas tardías a llamados anteriores. El token del turno, por sí solo, no identifica el intento de llamado al que responde el cliente.

**Recomendación.** Fake explícito para el corte. Para producción, describir reintentos, deduplicación, recuperación de pendientes y resultado incierto; no prometer exactamente una entrega. Diferir deshacer/rellamar.

### I5. Diferencias entre integridad documentada y DDL

**Archivos involucrados:** [04, modelo](../analisis/04_modelo_de_datos.md), [04b, DDL](../analisis/04b_modelo_de_datos_mysql.sql), [03, validación y aislamiento](../analisis/03_arquitectura_y_decisiones.md).

| Punto | Riesgo o diferencia | Ajuste proporcional |
|---|---|---|
| `active_key` | La unicidad solo protege la cadena guardada; no su correspondencia con teléfono, local y estado. | Centralizar mantenimiento y probar todos los cierres. |
| Local en eventos/notificaciones | La FK al ticket permite un `location_id` que no coincide con el suyo. | Derivarlo del ticket o asegurar la relación compuesta. Una FK simple adicional a locales no basta. |
| Tamaño de grupo | API/prompts 1–20; SQL 1–50; además existe `max_party_size`. | Diferenciar techo absoluto y límite por local, o unificarlos. |
| Token público | No se fija comparación sensible a mayúsculas. | Comparación binaria para credenciales opacas. |
| UTC | `DATETIME` y `CURRENT_TIMESTAMP` no garantizan por sí solos la política declarada. | Fijar UTC en conexión/escritura y serialización explícita. |
| Corte diario | Existe `day_cutoff_hour`, pero fórmulas y prompts fijan cinco horas. | Elegir configuración o constante, sin dos fuentes de verdad. |

MySQL documenta las [comparaciones insensibles a mayúsculas por defecto](https://dev.mysql.com/doc/refman/8.0/en/case-sensitivity.html) y que [`DATETIME` no convierte automáticamente a UTC](https://dev.mysql.com/doc/refman/8.0/en/time-zone-support.html).

La prueba citada en MariaDB 10.11 es evidencia parcial, no una validación completa de MySQL. No es necesario abandonar SQLite local; sí evitar prometer equivalencia total.

### I6. Cloud Run público no protege `/internal/*` automáticamente

**Archivos involucrados:** [03, diagrama de producción](../analisis/03_arquitectura_y_decisiones.md), [06, seguridad](../analisis/06_produccion_y_tests.md).

La API pública y los endpoints internos comparten servicio. Configurar acceso público afecta al servicio; el prefijo `/internal` no aplica IAM por ruta. Véase [acceso público de Cloud Run](https://docs.cloud.google.com/run/docs/authenticating/public).

**Recomendación.** Verificar en aplicación el token OIDC y autorizar la identidad prevista de Tasks/Scheduler, incluyendo emisor y audiencia. Separar otro servicio privado es una alternativa, no una obligación para este diseño. Puede quedar documentado sin implementarlo; bloquea desplegar endpoints internos reales sin protección.

### I7. Retención y credenciales no cubren todos los soportes

**Archivos involucrados:** [03, D8/D21](../analisis/03_arquitectura_y_decisiones.md), [04b, payloads](../analisis/04b_modelo_de_datos_mysql.sql), [06, logs y privacidad](../analisis/06_produccion_y_tests.md), prompt C4 (`prompts/C_conversacion_frontend.md`, archivo histórico no incluido).

Borrar `phone_e164` no anonimiza nombres, payloads de webhook, JSON de eventos, logs y respaldos. Falta concretar consentimiento en altas manuales con teléfono.

También existe tensión entre «no loguear tokens» y ponerlos en rutas o en `?token=`. Limpiar la URL desde JavaScript sucede después de la primera petición. Cloud Run genera [request logs](https://docs.cloud.google.com/run/docs/logging), y [`requestUrl` incluye ruta y query](https://docs.cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry).

**Recomendación.** Política breve por tipo de dato, captura mínima y tratamiento de credenciales en logs de aplicación e infraestructura. La URL de emparejamiento fija es una comodidad local que no debe trasladarse automáticamente al piloto.

### I8. Prioridades de tests desalineadas con el corte

**Archivos involucrados:** [06, tests](../analisis/06_produccion_y_tests.md), prompt B6 (`prompts/B_conversacion_backend.md`, archivo histórico no incluido).

Se conservarían transición inválida, doble llamado y aislamiento. Se subirían de prioridad:

1. Un solicitante distinto con igual teléfono no obtiene el token.
2. Reintento de la misma solicitud, incluso después de terminar el turno; conflicto de clave y contenido.
3. Liberación de unicidad en cada estado terminal.
4. Atomicidad entre estado y evento de negocio.
5. Fecha de servicio: ya se escribe en el alta, aunque el reporte no se implemente.
6. Privacidad de la respuesta pública.
7. Empate en el orden de llegada.

Llamar dos veces secuencialmente no demuestra concurrencia real; el documento lo reconoce correctamente. Dos pestañas tampoco garantizan simultaneidad.

**Recomendación.** Pocos tests de invariantes y casos parametrizados. Mantener una prueba integrada del flujo exitoso: unirse → llamar → consultar estado público. Ese test verifica un contrato central, no un detalle trivial de implementación.

### I9. Preguntas buenas, pero con decisiones de producto por precisar

**Archivos involucrados:** [07, preguntas](../analisis/07_disenador_preguntas_y_devolucion.md), prompt A2 (`prompts/A_conversacion_nota.md`, archivo histórico no incluido), [03, polling y canales](../analisis/03_arquitectura_y_decisiones.md).

Se conservarían los temas orden/promesa, ausencias/métricas e inclusión. Se reformularían alrededor de:

1. Qué promesa hacer cuando una mesa permite atender a un grupo posterior.
2. Qué cuenta como abandono y cómo distinguir cancelación, ausencia confirmada y pendiente sin resolver.
3. Si el cliente puede alejarse y qué alternativa acepta el local sin canal digital.

El tercer punto importa porque el polling pausado con la pestaña oculta no avisa activamente al teléfono bloqueado. La demo puede demostrar el cambio de estado; el piloto necesita canal real o una regla de permanencia y llamado por voz.

No tener WhatsApp y no poder escanear un QR son casos distintos. Intervalos, tokens, motor local y mecanismo técnico de autenticación se pueden decidir sin bloquear al diseñador.

## 4. MENOR

### M1. «Irreversible» se usa con demasiada amplitud

**Archivos:** [03, reversibilidad](../analisis/03_arquitectura_y_decisiones.md), [08, reversibilidad](../analisis/08_decisiones_y_preguntas_tecnicas.md).

Plantillas, remitentes y métricas pueden cambiar, con costos y consecuencias. Conviene distinguir datos que no podrán capturarse retroactivamente, compromisos externos costosos y decisiones técnicas reversibles. E.164 normaliza contacto; no es identidad personal estable.

### M2. Polling correcto, justificación demasiado absoluta

**Archivos:** [00, tesis](../analisis/00_contexto_del_analisis.md), [03, D3](../analisis/03_arquitectura_y_decisiones.md), [08, polling](../analisis/08_decisiones_y_preguntas_tecnicas.md).

Cloud Run no exige Redis específicamente. Requiere una estrategia de sincronización para repartir eventos entre instancias; [Google documenta varias opciones](https://docs.cloud.google.com/run/docs/triggering/websockets). SSE no elimina ese problema por sí solo.

La defensa suficiente: se acepta una demora de segundos y polling reduce trabajo para este corte.

### M3. Costos y capacidad con más certeza que evidencia

**Archivos:** [02, contexto externo](../analisis/02_lectura_del_problema.md), [06, costos](../analisis/06_produccion_y_tests.md), [08, cifras de WhatsApp](../analisis/08_decisiones_y_preguntas_tecnicas.md).

Los 400 req/s son un escenario, no una prueba de capacidad; omiten tablets e intervalos acelerados. El país del restaurante es una aproximación al mercado del destinatario que falla con turistas. Meta describe el [cobro por entrega y mercado/categoría](https://whatsappbusiness.com/products/platform-pricing/).

En esta revisión no se pudo corroborar el anuncio específico de octubre de 2026 y sus importes en el rate card oficial: la página técnica devolvió error de acceso. No se concluye que sea falso; se recomienda no presentarlo como verificado por esta auditoría. Tampoco es necesario para justificar evitar mensajes innecesarios.

### M4. Precisiones secundarias de datos y operación

**Archivos:** [04, reporte e historial](../analisis/04_modelo_de_datos.md), [06, alarmas y flags](../analisis/06_produccion_y_tests.md).

- Sin tickets, `SUM(...)` devuelve NULL: contadores cero y media «sin datos» deben diferenciarse.
- Los flags de WhatsApp/SMS necesitan una ubicación definida: configuración o BD.
- Reconstruir posiciones con eventos requiere capturar datos suficientes del orden; una columna JSON no lo garantiza.
- Alarmas porcentuales necesitan volumen mínimo y horarios definidos.
- Cero altas no prueba una caída sin contexto y línea base.

### M5. Prompts demasiado guionizados

**Archivos:** instrucciones de prompts (`prompts/00_como_usar_los_prompts.md`, archivo histórico no incluido), prompt A (`prompts/A_conversacion_nota.md`, archivo histórico no incluido).

«Respuesta esperada», preguntas obligatorias para demostrar escepticismo y rechazos predeterminados pueden perpetuar errores y consumir tiempo. Se recomienda usarlos como checklist de contexto y restricciones. Los desacuerdos deberían surgir de problemas reales.

El análisis previo y esta auditoría forman parte de la trazabilidad de decisiones si se utilizan para construir la solución.

## 5. Decisiones bien resueltas

| Decisión | Por qué conservarla | Evidencia |
|---|---|---|
| FastAPI + React, un servicio y pocas capas | Suficiente para el problema y defendible por una persona. | [03](../analisis/03_arquitectura_y_decisiones.md) |
| SQLite local y MySQL como destino | Levantar el proyecto es inmediato; el encargo lo permite. | [01](../analisis/01_enunciado_checklist.md), [03](../analisis/03_arquitectura_y_decisiones.md) |
| Polling con último dato y recuperación | Adecuado al corte y a conectividad variable. | [03](../analisis/03_arquitectura_y_decisiones.md), prompt C (`prompts/C_conversacion_frontend.md`, archivo histórico no incluido) |
| UPDATE condicional | Resuelve competencia por la misma transición. | [04](../analisis/04_modelo_de_datos.md) |
| Estado actual y bitácora pequeña | Conserva hechos útiles sin event sourcing. Debe ser transaccional. | [03](../analisis/03_arquitectura_y_decisiones.md), [04](../analisis/04_modelo_de_datos.md) |
| No modelar clientes, mesas ni reservas | Mantiene una frontera razonable con El Libro. | [04](../analisis/04_modelo_de_datos.md) |
| Separar «Se fue» y «Borrar por error» | Protege la interpretación del reporte. | [03](../analisis/03_arquitectura_y_decisiones.md) |
| UTC, zona IANA y fecha de servicio | Base temporal correcta para Lima y Santiago. | [04](../analisis/04_modelo_de_datos.md) |
| README probado, migraciones fuera del arranque y rollback | Reduce riesgos reales de despliegue y operación. | [05](../analisis/05_alcance_estimaciones_y_orden.md), [06](../analisis/06_produccion_y_tests.md) |
| Contingencia en papel | Reconoce la continuidad operativa del restaurante. | [06](../analisis/06_produccion_y_tests.md) |

## 6. Decisiones y trade-offs que conviene documentar

| Decisión y documentos | Trade-off que conviene explicar |
|---|---|
| Polling — 03/08 | Demora y lecturas repetidas a cambio de menor complejidad. La capacidad se mide. |
| Token por tablet — 03/06 | Menor fricción a cambio de menor atribución personal y necesidad de revocación. |
| SQLite local — 03/04b/06 | Facilidad de arranque a cambio de validar diferencias de motor antes del piloto. |
| Llamar cualquier fila — 02/07 | Selección según mesa disponible; no equivale a reservar una prioridad futura. |
| Un turno activo por teléfono — 02/04 | Reduce duplicados, pero puede bloquear grupos distintos con contacto compartido. No autentica. |
| Bitácora — 03/04 | Conserva hechos a cambio de otra escritura transaccional y retención definida. |
| Notificador fake — 03/05 | Demuestra flujo sin credenciales; no valida entrega, reintentos ni teléfono bloqueado. |
| Aplazar ETA — 02/04/05 | Renuncia a una promesa sin evidencia para entregar un estado fiable. |

## 7. Cambios recomendados antes de programar

1. Corregir autorización e idempotencia del alta pública — C1.
2. Cerrar matriz de acciones e invariantes — C2.
3. Fijar alcance obligatorio de cuatro horas y propagarlo — C4.
4. Separar ciclo diario de reporte/correo — C3.
5. Definir métricas observables — I1.
6. Alinear DDL y contratos, incluyendo desempate — I3/I5.
7. Reordenar tests por riesgo del corte real — I8.
8. Acotar las promesas de producción y su justificación — I4/I6/I7/M1/M2/M3.

Las ocho quedaron resueltas. La [resolución de hallazgos](02_resolucion_de_hallazgos.md) registra qué se decidió en cada caso y en qué documento quedó.

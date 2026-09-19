# 09 · Corte congelado, contrato y plan de implementación

Fecha de congelamiento: 16/09/2026.
**Este documento manda.** Donde contradiga a 00–08 o al material de `../conversaciones/`, vale lo que dice aquí.
Los documentos 02–04 y 06 conservan el *porqué*; este conserva el *qué*, ya decidido.
La disposición de cada hallazgo de la auditoría está en `../auditoria/02_resolucion_de_hallazgos.md`.

Regla de uso actualizada el 18/09/2026: si aparece una propuesta o cambia el plan, revisar y actualizar
el contrato de API, este alcance y la estructura documentada (§ 2.6). La deuda diferida sigue en § 9.

---

## 1. El corte, en una frase

Un comensal se une por QR desde su celular, ve su turno actualizándose solo, y el anfitrión lo ve
aparecer en la tablet y lo llama, lo sienta o lo marca como que no vino — con cada hecho registrado
y sin que dos anfitriones puedan pisarse.

Eso es lo que pide el enunciado como mínimo ("un comensal se une a la cola → el anfitrión la ve →
llama al siguiente"). Todo lo demás de esta lista es elección, y cada elección se defiende.

## 2. Alcance congelado

### 2.1 OBLIGATORIO (si falta algo de esto, el corte no está listo)

| # | Pieza | Por qué es obligatorio |
|---|---|---|
| O1 | Unirse desde `/q/{code}` con nombre, teléfono y tamaño de grupo | es la entrada; sin esto no hay producto |
| O2 | Alta segura ante reintentos: `request_id` del navegador; el mismo reintento devuelve el mismo turno | la puerta tiene mala señal; el doble toque es seguro que pasa |
| O3 | Un turno activo por teléfono, local y día, recuperable con el teléfono desde «Ya estoy en la lista de espera» (**enmienda § 2.5**) | evita el turno duplicado y da salida a quien perdió el link |
| O4 | Página del turno `/t/{token}` con polling: grupos delante, tiempo aproximado, estado, «Ya no voy» | la promesa central al comensal |
| O5 | Cola del anfitrión `/host` autenticada por token de dispositivo y aislada por local | núcleo operativo; un local no ve a otro |
| O6 | Llamar / Sentar / No vino / Se fue, con transición atómica y segundo toque sin efecto | dos anfitriones un viernes |
| O7 | `ticket_events` escrito en la misma transacción que el cambio de estado | lo que no se registra no se recupera |
| O8 | Notificador falso: registra el aviso y el evento; si falla, el turno sigue llamado | el estado del negocio no depende de Meta |
| O9 | Estados de red: "sin conexión, reintentando" conservando el último dato; nunca un error técnico en pantalla | el wifi de la puerta es malo |
| O10 | Los 7 tests no negociables (§7) en verde | "tests de lo que se rompe" |
| O11 | README probado desde un clon limpio en ≤ 5 min | requisito explícito del encargo |
| O12 | Seed de 3 locales (2 Lima, 1 Santiago) con links impresos en consola | para que lo levanten sin preguntarte nada |
| O13 | «Ya estoy en la lista de espera»: consulta por teléfono que devuelve el turno activo del día con su token | cerrar la pestaña no puede dejar al comensal sin salida (07 § 3.1 P3) |

### 2.2 OPCIONAL — solo si O1–O13 está cerrado y sobra tiempo, en este orden

1. **Alta manual en la tablet** (`POST /api/host/tickets`, formulario plegable). La más valiosa de las cuatro: es el argumento de adopción de toda la nota.
2. **«Voy en camino»** (`POST .../on-my-way` + botón + marca en la tablet).
3. **«Borrar (error/duplicado)»** en el menú secundario de la tablet (el endpoint sí se implementa; lo opcional es el botón).
4. **Animación CSS** cuando el número baja.

Si no entran, van a la nota con su estimación. **No se empiezan si algo de §2.1 está a medias.**

### 2.3 FUERA — no se escribe ni una línea

WhatsApp y SMS reales · webhook de Meta · outbox y Cloud Tasks · cierre del día automático ·
reporte y correo · arrastrar para reordenar · cliente frecuente · re-llamar y deshacer llamado ·
pausar la lista · panel de administración · login por persona · rate limiting · Alembic ·
servir el build de React desde FastAPI · Docker de la API · CI/CD · i18n · asignación de mesas.

Todo esto se cuenta en la nota con estimación y dependencia. Nada de esto vuelve a aparecer como
requisito en un prompt ni en la definición de listo.

### 2.4 Cambios respecto de 00–08 (leer sí o sí)

| Antes decía | Ahora | Por qué |
|---|---|---|
| Alta manual "sí si alcanza" (05) / obligatoria (00, prompt C4) | **Opcional 1** | era la contradicción más cara del set |
| «Voy en camino» recortable (05 §4) pero exigido en "definición de listo" (05 §5) y prompt C3 | **Opcional 2**; la definición de listo ya no lo incluye | idem |
| Alembic "si alcanza" | **Fuera** | 15–20 min que no compran nada en local; se explica en la nota |
| `POST /leave` desde cualquier estado | **Solo desde `waiting`** | desde `called` la acción correcta es «No vino» |
| Casilla de consentimiento obligatoria | **Aviso visible + consentimiento por acción**, con `consent_at` | un toque más en la puerta es lo que mató la lista de El Libro |
| TanStack Query "o hook propio" | **Hook propio (~40 líneas)** | una decisión menos a mitad de build, y una dependencia menos que mantener |
| ETA fuera del corte (recomendación de auditoría I2) | **Se queda**, etiquetado como aproximado y no calibrado | el encargo lo pide de forma explícita; quitarlo sería incumplir un requisito |
| `active_key = "{loc}:{phone}"` | **`"{loc}:{service_date}:{phone}"`** | si no, el turno del viernes bloquea al mismo teléfono el sábado |
| Cola = todos los `waiting`/`called` | **+ filtro por `service_date`** | si no, los pendientes de ayer aparecen hoy |

### 2.5 Enmienda del 18/09/2026 — recuperar el turno con el teléfono

Primera decisión reabierta después del congelamiento, tomada **antes** de escribir código y al responder
las tres preguntas al diseñador (07 § 3.1 P3). Queda aquí y no en "Deuda conocida" porque cambia el
alcance obligatorio, no lo aplaza.

| Antes decía | Ahora | Por qué |
|---|---|---|
| O3 y 08 § 4b: nunca revelar el token a quien solo conoce el teléfono; la recuperación la hace el anfitrión | **`POST /api/public/locations/{code}/lookup`**: con el teléfono se devuelve el turno activo del día **con su token**, y el comensal vuelve a su página | perder el link (cerrar la pestaña, incógnito, otro navegador) es un hecho diario; mandar a esa persona de vuelta a la puerta es justo el problema que el producto dice resolver |

Lo que se acepta a cambio, dicho sin adornos: **el teléfono pasa a ser la credencial.** Quien conozca un
número y el código del QR —que está pegado en la puerta y es público— puede abrir ese turno y cancelarlo.
El riesgo asumido es que adivinar un móvil completo y válido de alguien que además está en la cola de ese
local hoy no es un ataque realista; el costo de no tener salida sí es seguro y diario.

Lo que cuesta en el corte: **≈ 15 min**. El endpoint reutiliza la consulta que ya existe para `active_key`,
la pantalla es un enlace y un campo dentro de `JoinPage` —no una ruta nueva— y el test es el séptimo de
§ 7.1. Sale del bloque 3 de § 8.4 y, si aprieta, se paga con los opcionales de § 2.2, que ya estaban fuera
del "listo".

Mitigación fuera del corte, no olvidada: **OTP** (código al teléfono, token solo contra el código). Es la
versión segura de esto mismo, depende del canal real de WhatsApp o SMS y suma fricción en la puerta; queda
en § 9 punto 10. Lo que sí entra gratis: normalizar a E.164 con la región del local antes de buscar,
considerar solo `waiting`/`called` del `service_date` actual, y responder 404 sin decir nunca si ese
teléfono existe.

---

## 2.6 Enmienda del 18/09/2026 — implementación de backend y MySQL local

Solicitud del autor: implementar solo backend; añadir Docker para la base de datos y considerar MySQL
por el futuro uso de Aiven, conservando la facilidad de arranque local. Toda propuesta nueva o cambio
obliga a revisar contrato de API y estructura de carpetas documentada.

- SQLite sigue predeterminado para ejecutar el reto con Python. Se incorpora **MySQL 8.4 mediante
  `mesa247-api/compose.yaml`**, volumen y healthcheck. Docker de la BD deja de estar fuera del corte.
- Se implementa el backend obligatorio, incluido remove y lookup. Frontend, alta manual y on-my-way
  siguen pendientes de esta etapa. Los requisitos de pantallas O1/O4/O5/O9 se validan aquí solo vía API.
- `/readyz` comprueba la BD; `/healthz` sigue comprobando el proceso. No se despliega Aiven ni la API.
- Se precisa concurrencia: UPDATE compara el estado leído por la petición. Call y seat que leyeron
  waiting compiten; uno gana y el otro devuelve 409. Si seat lee called después del llamado, sentar
  es válido. No hay versión enviada desde la pantalla, así que no se detectan lecturas antiguas del cliente.
- Se mantienen siete grupos de tests obligatorios y se añaden pruebas reales con dos conexiones,
  tanto SQLite como MySQL local. No hace falta CI para ejecutar estas pruebas.
- Contrato implementado: [../api/README.md](../api/README.md) y [../api/openapi.json](../api/openapi.json).
  Estructura final: `03_arquitectura_y_decisiones.md` § 3 y README de la API.
- El README se valida en un directorio limpio con entorno nuevo. Esto verifica el arranque de backend;
  no equivale a completar todavía la definición fullstack de § 8.6.

---

## 2.7 Enmienda del 18/09/2026 — frontend, rutas y ventana de espera

Solicitud del autor al revisar el frontend implementado. Cambia tres cosas de este documento, y por
eso queda aquí y no en "Deuda conocida".

| Antes decía | Ahora | Por qué |
|---|---|---|
| § 2.5: «la pantalla es un enlace y un campo dentro de `JoinPage` — no una ruta nueva» | **`/q/{code}/mi-turno`, pantalla propia** con retorno al registro | el panel desplegable dejaba poco sitio para explicar y para el caso de «ya estás en la lista»; el campo y el mensaje de error se siguen compartiendo |
| `/` mostraba el código del local y hablaba del seed | **`/` es producto** («escanea el QR») más un atajo de prueba para elegir local; **`/admin` es solo la tablet** | la raíz la puede abrir un comensal: no puede hablarle de tokens ni de seeds. Y entrar a la lista **no es una acción de administración**: la hace el comensal al escanear, así que el atajo que la simula vive en `/`, no en el back office. `/admin` queda documentado en el README |
| § 3: el teléfono queda bloqueado todo el `service_date` | **Ventana de espera**: un turno deja de bloquear el teléfono cuando vence | quien perdió su llamado a las 20:10 no podía volver a anotarse hasta el cierre, que es justo cuando querría volver a la cola |
| 409 `already_in_queue` era el final del camino | **Aviso con dos salidas**: «ver mi turno» o «registrarme de nuevo» | el 409 seco no le dice a esa persona qué hacer |

**El atajo de la prueba.** `/` lleva un selector con los tres locales del piloto —La Terraza Azul y
Cuatro Vientos en Lima, Casa Mediterránea en Santiago— con las dos puertas que abre ese QR: unirse y
volver al turno con el teléfono. La pantalla no manda a nadie a escanear otra vez: el QR está fijo en
la puerta, y decirle a quien ya espera que vuelva allí es el problema que el producto resuelve. Existe porque en
una demo no hay cámara ni papel pegado en la puerta, y porque lo que el piloto tiene que enseñar es
cómo llega el comensal a la lista. Comprueba cada código contra la API: un local sin sembrar o cerrado
sale como «no disponible» en vez de llevar a una pantalla muerta. Es lo único del frontend que asume
qué hay en el seed, y vive en un archivo aparte (`lib/demo.ts`) para que se borre de una pieza.

**La regla de la ventana, exacta.** Un turno deja de bloquear su teléfono cuando:

- está `called` y pasó `called_at + call_grace_minutes` (los 10 minutos del llamado), o
- está `waiting` y pasó `joined_at + waiting_ttl_minutes` (nuevo, por defecto 120).

En ese caso el alta lo pasa a `expired` —con su evento y el invariante de § 3.1— y crea el turno nuevo.
La caducidad, el evento `expired`, el turno nuevo y su evento `joined` forman **una sola transacción**:
si cualquier parte falla, el turno anterior conserva su estado y su `active_key`.
Mientras el turno sigue vivo, el 409 se mantiene: dos turnos activos con el mismo número siguen sin existir.

- **`locations.waiting_ttl_minutes`** es columna nueva, con el mismo criterio que el resto de los
  ajustes del local: no hay un 120 escrito en el código.
- **`expire` ya se dispara desde `waiting` y desde `called`.** Sigue sin tener ruta HTTP: solo lo
  provoca un alta nueva. El cierre del día automático sigue fuera (§ 9 punto 1).
- **Métrica de `expired`:** sin `called_at` cuenta como «se fue sin sentarse»; con `called_at` cuenta
  como «no vino al ser llamado». Así, caducar un llamado vencido no cambia el significado del reporte.
- **«Registrarme de nuevo» no es atómico.** El front hace `lookup` → `cancel` → alta, porque no hay un
  alta que reemplace en una sola llamada. Entre las dos llamadas el teléfono queda libre; si la segunda
  falla, esa persona se quedó sin turno y tiene que volver a anotarse. La versión correcta es un
  `replace` en el alta y queda anotada en § 9 punto 11.
- **Lo que cuesta de verdad:** quien se registra de nuevo **pierde su puesto** y vuelve al final de la
  cola. La pantalla lo dice antes de confirmar, no después.

---

## 3. Modelo de datos — deltas sobre `04_modelo_de_datos.md`

Cuatro tablas: `locations`, `host_devices`, `tickets`, `ticket_events`. Sin cambios de estructura salvo:

- **`active_key` = `"{location_id}:{service_date}:{phone_e164}"`**, `NULL` si no hay teléfono y `NULL`
  en cuanto el turno llega a estado terminal. Único. `VARCHAR(64)`.
- **`client_request_id`** ya no es solo de la tablet: **el alta pública también lo manda** (uuid v4 generado
  en el navegador y guardado en `localStorage` *antes* de enviar). Único por `(location_id, client_request_id)`.
- **Desempate de orden**: en todas partes se ordena y se cuenta por **`(sort_key, id)`**, nunca por `sort_key` solo.
  Dos altas pueden caer en el mismo milisegundo (y con reloj congelado en los tests, caen siempre).
- **`day_cutoff_hour` se lee de la fila del local.** No hay un `5` escrito en el código.
- **`waiting_ttl_minutes`** (por defecto 120) define, junto con `call_grace_minutes`, cuándo un turno
  deja de bloquear su teléfono y el alta lo caduca. Ver § 2.7.
- **Tamaño de grupo**: `CHECK (party_size BETWEEN 1 AND 50)` es el techo absoluto del dato;
  `locations.max_party_size` (por defecto 20) es el límite de negocio que valida Pydantic. Son dos cosas distintas.
- **`public_token` y `token_hash` con colación binaria** en MySQL (`utf8mb4_bin`): son credenciales opacas,
  no texto. Por defecto MySQL compara sin distinguir mayúsculas.
- **Toda marca de tiempo de negocio la escribe la aplicación en UTC explícito.** No se usa
  `CURRENT_TIMESTAMP` para `joined_at`, `called_at`, `seated_at` ni `closed_at`: `DATETIME` en MySQL no
  lleva zona y el `DEFAULT` sigue la zona de la sesión.

### 3.1 Invariante único (esto es lo que hay que saber de memoria)

> **Toda transición a estado terminal** (`seated`, `cancelled`, `no_show`, `removed`, `expired`) fija,
> en el **mismo UPDATE**: `status`, `closed_at = now`, `active_key = NULL`.
> El `ticket_event` se inserta en la **misma transacción**. Si el evento falla, la transición no ocurre.

Un test parametrizado cubre los cinco estados. Es el test más importante del repo.

---

## 4. Matriz de acciones (única fuente de verdad de estados)

| Acción | Ruta | Actor | Origen permitido | Destino | Efectos además del invariante | Si se repite |
|---|---|---|---|---|---|---|
| Unirse | `POST /api/public/locations/{code}/tickets` | comensal | — | `waiting` | `joined_at`, `sort_key`, `service_date`, `active_key`, `quoted_wait_min`, `position_at_join`, `consent_at`, evento `joined` | mismo `request_id` → 200 con el mismo turno; teléfono repetido con otro `request_id` → 409 sin token |
| Alta manual | `POST /api/host/tickets` | anfitrión | — | `waiting` | igual, `source='host'`, teléfono opcional | mismo `request_id` → 200 con el mismo turno |
| Llamar | `POST /api/host/tickets/{id}/call` | anfitrión | `waiting` | `called` | `called_at`, `call_count+1`, evento `called`, dispara el aviso | ya `called` → 200 sin efectos **y sin aviso nuevo** |
| Sentar | `POST /api/host/tickets/{id}/seat` | anfitrión | `waiting`, `called` | `seated` | `seated_at`, evento `seated` | ya `seated` → 200 sin efectos |
| No vino | `POST /api/host/tickets/{id}/no-show` | anfitrión | `called` | `no_show` | evento `no_show` | ya `no_show` → 200 |
| Se fue | `POST /api/host/tickets/{id}/leave` | anfitrión | `waiting` | `cancelled` | evento `left` | ya `cancelled` → 200 |
| Borrar | `POST /api/host/tickets/{id}/remove` | anfitrión | `waiting`, `called` | `removed` | evento `removed`; no cuenta en el reporte | ya `removed` → 200 |
| Ya no voy | `POST /api/public/tickets/{token}/cancel` | comensal | `waiting`, `called` | `cancelled` | evento `cancelled` | ya `cancelled`/`no_show` → 200; desde `seated` → 409 |
| Voy en camino | `POST /api/public/tickets/{token}/on-my-way` | comensal | `called` | `called` (no cambia) | `on_the_way_at` **solo si es `NULL`**; evento `on_the_way` solo la primera vez | siempre 200 |

Reglas transversales:
- Cualquier otro origen → **409** con `{"error":"invalid_transition"}`.
- Turno de otro local, o token/id inexistente → **404**, nunca 403: no se revela que existe.
- Toda transición es `UPDATE … WHERE id=:id AND location_id=:loc AND status=:estado_observado`.
  `rowcount = 1` → gané. `rowcount = 0` → releo: ¿ya está en el destino? 200 sin efectos. ¿Otro? 409.
- **`Llamar` y `Sentar` que leyeron simultáneamente el mismo turno `waiting`**: uno gana, el otro relee, ve un
  estado distinto del observado y del destino → 409 → la tablet refresca y muestra "Otro anfitrión ya lo atendió".
  Si Sentar lee called después del commit de Llamar, puede sentar (§ 2.6).
- El evento `notification_sent` / `notification_failed` se escribe **después** del commit de la transición,
  en su propia transacción. No bloquea ni revierte el llamado.

> El diagrama `04c_diagrama_estados.png` se generó antes de congelar esta matriz: le falta la flecha
> `called → removed`. La fuente válida es el Mermaid de `04_modelo_de_datos.md` § 3 y esta tabla.

---

## 5. Contrato de API vigente

Esquema exacto implementado: [OpenAPI](../api/openapi.json). Precisiones de esta etapa: [contrato](../api/README.md).

Errores siempre: `{"error": "<slug>", "message": "<texto en español, para mostrar tal cual>"}`.
Sin trazas. 422 lo genera Pydantic y el front lo traduce a un mensaje por campo.

### 5.1 Público (sin autenticación)

```
GET /api/public/locations/{code}
200 {"code","name","country","phone_prefix","max_party_size"}
404 si no existe o is_active = false

POST /api/public/locations/{code}/tickets
body {"request_id": uuid4, "name": str(1..40, trim), "phone": str, "party_size": int}
201 TicketPublic (con token)     <- alta nueva
200 TicketPublic (con token)     <- mismo request_id: es un reintento, devuelvo lo mismo
409 {"error":"already_in_queue",
     "message":"Ya tienes un turno activo en este local. Usa 'Ya estoy en la lista de
                espera' para volver a el."}     <- SIN token; el token se recupera
                                                   por /lookup, no por el alta
422 validacion   -   404 local inexistente o inactivo

POST /api/public/locations/{code}/lookup
body {"phone": str}
200 TicketPublic (con token)     <- espera activa de hoy en este local
404 {"error":"not_found",
     "message":"No encontramos una espera activa con ese numero en este local hoy.
                Si acabas de anotarte revisa el numero; si no, vuelve a unirte."}
422 validacion   -   404 local inexistente o inactivo
Solo mira status IN (waiting, called) AND service_date = <dia de servicio actual>.

GET  /api/public/tickets/{token}            -> 200 TicketPublic - 404
POST /api/public/tickets/{token}/cancel     -> 200 TicketPublic - 409 - 404
POST /api/public/tickets/{token}/on-my-way  -> 200 TicketPublic - 409 - 404   [opcional 2]
```

```
TicketPublic = {
  "token":         "hV3...",         # solo en las respuestas del propio turno
  "location_name": "La Terraza Azul",
  "name":          "Carla",
  "party_size":    4,
  "status":        "waiting|called|seated|cancelled|no_show|removed|expired",
  "groups_ahead":  6,                # null si no esta en waiting
  "eta_min":       30,               # null si no esta en waiting
  "joined_at":     "2026-09-18T21:00:00Z",
  "called_at":     null,
  "deadline_at":   null,             # called_at + call_grace_minutes, solo si status = called
  "server_now":    "2026-09-18T21:05:00Z"
}
```

Nunca incluye `phone`, ni el `id` interno, ni nada de otros comensales. `server_now` existe para que
la cuenta regresiva no dependa del reloj del celular.

### 5.2 Anfitrión (`Authorization: Bearer <token de dispositivo>`; el local sale del token, jamás del body)

```
GET  /api/host/queue
200 {
  "location":      {"name","timezone"},
  "service_date":  "2026-09-18",
  "waiting_count": 12,
  "avg_wait_min":  34,        # null si hoy no hay sentados - "sin datos" != 0
  "server_now":    "...",
  "rows": [{
     "id":41, "name":"Carla", "party_size":4, "status":"waiting",
     "waiting_min":34,                  # calculado en el servidor
     "called_at":null, "deadline_at":null,
     "on_the_way":false, "overdue":false,
     "notify_state":"none|sent|failed"
  }]
}
rows = status IN (waiting, called) AND service_date = <dia de servicio actual>, ORDER BY sort_key, id

POST /api/host/tickets                      [opcional 1]
POST /api/host/tickets/{id}/call | seat | no-show | leave | remove
   -> 200 {row}   -   409 invalid_transition   -   404 (otro local / no existe)   -   401 sin token
```

### 5.3 Fórmulas

- `groups_ahead` = nº de turnos `waiting` del mismo local y `service_date` con `(sort_key, id)` menor.
  Los `called` **no** cuentan: ya no están delante. (En la tablet sí se ven, en su posición de llegada.)
- `eta_min` = `max(5, ceil_a_5((groups_ahead + 1) × location.minutes_per_party))`, con `minutes_per_party = 4`.
  **Es una heurística sin calibrar.** Se guarda `quoted_wait_min` y `position_at_join` para comparar
  después contra `seated_at − joined_at`. En pantalla se muestra como "≈ 30 min" con la frase
  "es aproximado: depende de las mesas que se vayan liberando".
- `avg_wait_min` = promedio de `seated_at − joined_at` de los sentados de hoy, calculado **en Python**
  (`TIMESTAMPDIFF` no existe en SQLite). `null` si no hay ninguno.
- `service_date` = fecha local de `(instante en la zona del local − day_cutoff_hour horas)`.
- `overdue` = `status == 'called' and server_now > called_at + call_grace_minutes`.

---

## 6. Decisiones de stack congeladas

| Tema | Decisión | Una línea de defensa |
|---|---|---|
| Backend | FastAPI + SQLAlchemy 2 **síncrono** + Pydantic v2 | la carga es baja; FastAPI corre los `def` en threadpool; el código se lee sin `async` |
| BD local | SQLite predeterminado; alternativa MySQL 8.4 con Compose. SQLite archivo, con `journal_mode=WAL`, `busy_timeout=5000`, `check_same_thread=False` | sin WAL, dos tablets escribiendo dan "database is locked" en la demo |
| Migraciones | `create_all()` en local. **Sin Alembic.** | en producción va como Cloud Run Job antes de mover tráfico; en 4 h no compra nada |
| Frontend | Vite + React + TypeScript + `react-router-dom`. Nada más. | tres rutas; cualquier otra dependencia hay que saber defenderla |
| Datos del servidor | **hook propio `usePolling` (~40 líneas)** | tres pantallas no pagan una dependencia de datos con su propia API que mantener |
| Estilos | un `app.css`. Sin Tailwind, sin UI kit. | no se evalúa pixel a pixel; botones grandes para la tablet |
| Local↔local | proxy de Vite `/api → :8000`. **El backend no sirve el build.** | mismo origen en producción; en local, un paso menos en el README |
| Intervalos | comensal 15 s (10 s si `groups_ahead ≤ 3`); tablet 5 s; pausa con pestaña oculta; refresco al volver; backoff hasta 60 s | ~8 req/s en el piloto |
| Polling terminal | al llegar a estado final, **se detiene el polling** | batería y datos del comensal |
| Secretos | `.env.example`, ningún token real en el repo | — |

---

## 7. Tests

### 7.1 No negociables (estos siete no se cortan por nada)

| # | Test | Qué se rompe sin él |
|---|---|---|
| 1 | `test_join_retry_same_request_id_returns_same_ticket` **y** `test_join_same_phone_other_request_id_returns_409_without_token` | señal mala → turnos duplicados; y el mismo teléfono con dos turnos activos rompe `active_key` y el reporte |
| 2 | `test_call_twice_sends_one_notification` (2.º = 200 sin efecto) | dos anfitriones → dos WhatsApp cobrados |
| 3 | `test_invalid_transitions_return_409` (sentar un cancelado, no-show de uno en espera, cancelar un sentado) | la cola se corrompe sola |
| 4 | `test_host_cannot_touch_other_location` (token de A sobre turno de B → 404) | fuga entre locales |
| 5 | `test_terminal_states_release_active_key` — **parametrizado** sobre seated/cancelled/no_show/removed | el teléfono queda bloqueado y no puede volver a la cola |
| 6 | `test_phone_normalization` (`"987 654 321"`+PE → `+51987654321`; `"9 8765 4321"`+CL → `+56987654321`; basura → 422) | no hay a quién avisar, ni deduplicación |
| 7 | `test_lookup_returns_active_ticket_of_today` **y** `test_lookup_404_when_none` (turno ya terminal → 404; turno de otro local → 404; turno de ayer → 404) | la única salida de quien perdió el link; y el endpoint que reparte tokens no puede filtrar turnos ajenos ni de ayer |

El test 1 conserva su segundo caso (mismo teléfono y otro `request_id` al unirse → 409 **sin** token):
sigue siendo la respuesta correcta del alta. Lo que cambió con la enmienda § 2.5 es su *razón*: ya no
protege el turno —para eso ahora está `/lookup`—, evita el duplicado y empuja a la pantalla correcta.
La enmienda § 2.7 añade al mismo grupo las pruebas de vigencia, reemplazo tras vencer y rollback completo
si falla el alta nueva. Con dos reemplazos simultáneos, uno crea el turno y el otro recibe 409.

### 7.2 Si alcanza (baratos, en este orden)

8. `test_public_ticket_does_not_leak_data` (ni `phone` ni otros nombres en la respuesta; token inventado → 404).
9. `test_notifier_failure_keeps_ticket_called` (+ evento `notification_failed`).
10. `test_position_ignores_called_and_closed` **y empate**: dos altas con el mismo `sort_key` → posiciones distintas y estables.
11. `test_service_date` — unitario, sin HTTP: sábado 00:30 Lima → viernes; el mismo instante en Santiago → sábado.
12. Test integrado del camino feliz: unirse → aparece en la cola → llamar → el público ve `called`.

Herramientas: `pytest` + `TestClient`, SQLite temporal por test, notificador fake inyectado con
`dependency_overrides`, **reloj inyectable** (`now()` como dependencia).

Validación actualizada (§ 2.6): el test 2 sigue probando el doble llamado secuencial.
`tests/test_concurrency.py` añade dos conexiones simultáneas para doble llamado, call contra seat
y alta con el mismo request_id. La suite corre en SQLite y con `scripts/test_mysql.py` en MySQL local.

No se testea: que la página renderiza, CRUD triviales, getters, snapshots, porcentaje de cobertura.

---

## 8. Orden de implementación

### 8.1 Backend (chat B) — en este orden exacto

1. `config.py` · `db.py` (engine + `get_session`, con los PRAGMA de SQLite) · `main.py` con `/healthz`.
2. `models.py` — las 4 tablas. **`create_all` al arrancar en local.**
3. `domain/time.py` — `now()` inyectable, `service_date(location, instante)`.
4. `domain/phones.py` — normalización E.164 con `phonenumbers` y la región del local.
5. `domain/queue.py` — diccionario de transiciones, `apply_transition()` con el UPDATE condicional y el
   invariante de §3.1, `groups_ahead()`, `eta()`, `avg_wait_min()`.
6. `auth.py` — `Depends` que resuelve Bearer → `host_device` → `location`, y toca `last_seen_at`.
7. `notifier.py` — interfaz + `FakeNotifier` (log con **solo los últimos 3 dígitos** del teléfono).
8. `routers/public.py` → `routers/host.py`.
9. `seed.py` — 3 locales + un token por local, imprime los dos links por local.
10. `tests/` — los siete de §7.1, en ese orden.

**Punto de control (≈ 1:50):** `pytest` en verde y `curl` de unirse → cola → llamar funcionando.
Si no está, se cortan los opcionales del frontend antes de empezarlo.

### 8.2 Frontend (chat C) — en este orden exacto

1. `api.ts` (fetch tipado + traducción de errores a mensajes en español) y `usePolling.ts`.
2. `JoinPage` `/q/:code` — incluido el `request_id` en `localStorage` **antes** del primer envío.
3. `TicketPage` `/t/:token` — el más importante: es la pantalla que ve el comensal mientras espera.
4. `HostPage` `/host` — token desde `?token=`, a `localStorage`, y se limpia de la URL.
5. «Ya estoy en la lista de espera» (O13): en `JoinPage`, un enlace que despliega un campo de teléfono y
   redirige a `/t/:token` con lo que devuelva `/lookup`. Reutiliza el mismo input y el mismo mensaje de
   error del alta; no es una ruta nueva.
6. Solo entonces: opcionales de §2.2.

### 8.3 Cierre

README (bash **y** PowerShell) → clon limpio cronometrado → nota técnica.

### 8.4 Reparto de las 4 horas

| Bloque | Min | Qué |
|---|---|---|
| 0–1 | 30 | chat A: huecos, 3 preguntas, supuestos, corte, contrato (se pega de aquí) |
| 2 | 80 | backend completo hasta el punto de control |
| 3 | 75 | frontend, tres pantallas |
| 4 | 15 | README + clon limpio cronometrado |
| 5 | 40 | nota técnica (1–2 páginas) |

Son 4:00 justos y **sin margen**. Lo realista es 4:30–5:00; conviene anotar el tiempo real por bloque
para que la estimación del piloto parta de datos y no de intuición.

### 8.5 Si vas atrasado, corta en este orden

1. Los cuatro opcionales de §2.2 (ya están fuera del "listo").
2. Los tests 8–12 de §7.2 (nunca los siete de §7.1).
3. `POST /remove` (endpoint incluido).
4. `avg_wait_min` del encabezado de la tablet (deja `waiting_count`).
5. El chunk aparte de `/host` (deja todo en un bundle).

**Nunca se corta:** los siete tests, el README probado, el aislamiento entre locales y la nota.

### 8.6 Definición de listo

- Clon limpio → README → back y front arriba en ≤ 5 min (anota el tiempo real).
- Vista móvil: unirse con un teléfono PE válido → grupos delante y tiempo aproximado.
- Recargar y volver a enviar el mismo formulario → el mismo turno, no uno nuevo.
- Otro navegador, mismo teléfono → mensaje "ya tienes un turno activo", **sin** token en esa respuesta.
- Ese mismo navegador → «Ya estoy en la lista de espera» con ese teléfono → vuelve a su turno.
- «Ya estoy en la lista de espera» con un teléfono que no está en la cola, o con el de un turno ya
  cerrado → mensaje de "no encontramos una espera activa", nunca un turno ajeno ni uno de ayer.
- Tablet: aparece la fila → Llamar → el celular muestra "¡Tu mesa está lista!" y la hora límite.
- Dos pestañas de tablet → Llamar en ambas → **un solo** "WhatsApp simulado" en el log.
- Token de tablet inválido o de otro local → no se ve nada.
- Bajar el backend 30 s → el celular dice "sin conexión" y se recupera solo sin perder el dato.
- `pytest` en verde.

Nada más. Lo que falte va a la nota con su estimación.

---

## 9. Deuda conocida (va en la nota; no se arregla en el corte de 4 horas)

1. **El cierre del día no está implementado.** La cola filtra por `service_date`, así que un pendiente de
   ayer no ensucia hoy, pero queda abierto para siempre. En el piloto lo resuelve Cloud Scheduler a las
   05:00 de cada zona; en la primera semana, a mano.
2. **El notificador falso no prueba entrega.** No hay reintentos, ni confirmación, ni teléfono bloqueado.
3. **Sin rate limiting.** Cualquiera con el código del QR puede llenar la cola. En el piloto: límite por IP
   y por teléfono, y «Borrar» en la tablet.
4. **No se puede cambiar el tamaño de un grupo.** Llegan 4, resultan 6 → hoy es borrar y volver a agregar.
   Va a pasar en el piloto la primera semana.
5. **Un teléfono = un turno activo a la vez.** Quien reserva para dos familias con el mismo número no
   puede hacerlo a la vez; desde § 2.7 el bloqueo dura lo que dura la espera, no todo el día.
   Lo cubre el alta manual sin teléfono.
6. **Consentimiento por acción, no por casilla.** Decisión tomada para no sumar fricción en la puerta;
   hay que validarla con legal antes del piloto (Perú pide consentimiento "expreso").
7. **Sin atribución por persona**: se sabe qué tablet actuó, no quién la tocaba.
8. **SQLite ≠ MySQL.** Colación, `TIMESTAMPDIFF`, bloqueo de escritura y zona horaria difieren.
   La suite ya se ejecuta también en MySQL local; antes del piloto validar el servicio remoto y TLS.
9. **El token de la tablet viaja en la URL del seed.** Cómodo en local, inaceptable en producción
   (Cloud Run registra la query string): en el piloto va por emparejamiento, no por link fijo.
10. **`/lookup` sin OTP: el teléfono es la credencial.** Decisión consciente de la enmienda § 2.5, no un
    descuido. Quien conozca un número y el código público del QR puede abrir y cancelar ese turno.
    Antes del piloto: código de verificación por WhatsApp o SMS (~0,5 d sobre el canal real, que son
    3 d y 1 d en 05 § 2) y, mientras tanto, límite por IP y por teléfono en ese endpoint — que hoy
    tampoco existe (punto 3).
11. **«Registrarme de nuevo» son dos llamadas, no una.** El front cancela el turno anterior y crea el
    nuevo; entre las dos el teléfono queda libre y un fallo deja a esa persona sin turno. La versión
    correcta es un `replace` en el alta, que cancela y crea en la misma transacción (≈ 0,2 d).
12. **La ventana de espera no cierra turnos por sí sola.** Un turno vencido solo caduca si esa misma
    persona vuelve a anotarse; si no, sigue abierto hasta el cierre del día, que tampoco existe
    (punto 1). Para el reporte, ambos son el mismo agujero.

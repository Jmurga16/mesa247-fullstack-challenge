# 03 · Arquitectura y decisiones

Principio rector: lo más simple que aguante producción con 3 locales y que no cierre el camino a 150.
Todo lo que no protege al piloto se difiere, y se dice por qué.

## 1. Vista de producción (lo que describes en la nota)

    [QR impreso] ──► https://fila.mesa247.pe/q/{codigo}     (código corto → local, resuelto en BD)
          │
    [Celular del comensal]            [Tablet del anfitrión (token de dispositivo)]
          │   HTTPS + JSON (polling)          │
          ▼                                   ▼
    ┌──────────────────────────────────────────────────────────┐
    │ Cloud Run · servicio "waitlist" (FastAPI)                 │
    │  /api/public/...     comensal (sin login)                 │
    │  /api/host/...       anfitrión (Bearer de dispositivo)    │
    │  /webhooks/whatsapp  Meta (firma HMAC)                    │
    │  /internal/...       Cloud Tasks / Scheduler (OIDC, ver D23)│
    │  + sirve el build de React (mismo origen, sin CORS)       │
    └───────┬───────────────────────┬──────────────────────────┘
            │                       │
      Cloud SQL (MySQL 8)     Cloud Tasks (reintentos) ──► WhatsApp Cloud API / proveedor SMS
            ▲                                                   │
            │                                    webhook: botones y estados de entrega
      Cloud Scheduler (05:00 por zona horaria) ──► cierre del día ──► reporte ──► correo
      Transversal: Secret Manager · Cloud Logging/Monitoring · Error Reporting · Uptime checks
      Región sugerida: southamerica-west1 (Santiago): cerca de Lima y de Santiago.

## 2. Vista local (lo que se construye en el corte de 4 horas)

    React (Vite, :5173) ──proxy /api──► FastAPI (:8000) ──► SQLite (archivo, WAL)
    Notificador falso: escribe "WhatsApp simulado" en el log y registra el evento.
    Seed: 3 locales + un token de tablet por local; imprime los links en consola.

Diferencias deliberadas con producción, que hay que saber nombrar:
- **El backend no sirve el build de React** en local (en producción sí, para tener mismo origen): en local
  el proxy de Vite quita un paso del README, y el README tiene que levantar el proyecto en 5 minutos.
- **SQLite con `journal_mode=WAL` y `busy_timeout=5000`.** Sin eso, dos pestañas de tablet escribiendo
  a la vez dan "database is locked" justo en la demo.
- **Sin Alembic**: `create_all()` al arrancar. En producción, Alembic como Cloud Run Job antes de mover
  tráfico (nunca al arrancar la app: varias instancias migrando a la vez).

## 3. Estructura de repo implementada — backend, 18/09/2026

```text
Mesa247/
├── README.md
├── mesa247-api/
│   ├── app/
│   │   ├── main.py · config.py · db.py · models.py · schemas.py
│   │   ├── auth.py · notifier.py · errors.py
│   │   ├── domain/ time.py · phones.py · queue.py
│   │   └── routers/ public.py · host.py
│   ├── scripts/ export_openapi.py · test_mysql.py
│   ├── tests/ conftest.py · test_join.py · test_transitions.py
│   │          test_isolation_lookup.py · test_queue_time.py · test_concurrency.py
│   │          test_seed_health_contract.py
│   ├── seed.py · compose.yaml
│   └── README.md · requirements.txt · requirements-dev.txt · .env.example
├── mesa247-web/                 Frontend en una sesión separada
└── mesa247-docs/
    ├── api/ README.md · openapi.json
    ├── analisis/
    ├── auditoria/
    ├── entregables/
    └── conversaciones/
```

SQLite es predeterminado. `compose.yaml` añade MySQL 8.4 local; ambos usan los mismos modelos y suite.
MySQL remoto permite `DATABASE_SSL_CA`. No se añade Docker de API ni Alembic.
Los detalles ejecutables están en [README API](../../mesa247-api/README.md).
Cualquier cambio de alcance exige revisar este árbol, 09 y el [contrato implementado](../api/README.md).

## 4. Contrato de API v1
Las formas exactas de petición y respuesta están congeladas en `09_alcance_y_plan_de_implementacion.md` § 5.
Aquí va el mapa y el porqué de cada regla.

| Método | Ruta | Quién | Qué hace | Notas |
|---|---|---|---|---|
| GET | /api/public/locations/{code} | comensal | nombre del local, país, límites | 404 si no existe o está inactivo |
| POST | /api/public/locations/{code}/tickets | comensal | unirse | body lleva `request_id` (uuid del navegador). 201 nuevo · 200 mismo `request_id` (reintento) · **409 sin token** si ese teléfono ya tiene turno activo |
| POST | /api/public/locations/{code}/lookup | comensal | recuperar turno activo del día con teléfono | devuelve token según 09 § 2.5 |
| GET | /api/public/tickets/{token} | comensal | estado, grupos delante, ETA, hora límite si fue llamado | sin teléfono ni datos de otros |
| POST | /api/public/tickets/{token}/cancel | comensal | «Ya no voy» | desde waiting o called; desde seated → 409 |
| POST | /api/public/tickets/{token}/on-my-way | comensal | «Voy en camino» | solo si está llamado; marca la hora solo la 1.ª vez — **opcional** |
| GET | /api/host/queue | anfitrión | cola activa del día + indicadores | el local sale del token; filtra por service_date |
| POST | /api/host/tickets | anfitrión | alta manual | teléfono opcional; `request_id` para reintentos — **opcional** |
| POST | /api/host/tickets/{id}/call | anfitrión | llamar (dispara el aviso) | segundo intento = 200 sin efecto y sin aviso nuevo |
| POST | /api/host/tickets/{id}/seat | anfitrión | sentar | desde "en espera" o "llamado" |
| POST | /api/host/tickets/{id}/no-show | anfitrión | no vino | solo desde "llamado" |
| POST | /api/host/tickets/{id}/leave | anfitrión | se fue (avisó en persona) | **solo desde "en espera"**; cuenta como "se fue sin sentarse" |
| POST | /api/host/tickets/{id}/remove | anfitrión | borrar por error o duplicado | desde "en espera" o "llamado"; no cuenta en el reporte |
| POST | /api/host/tickets/{id}/recall · /undo-call | anfitrión | re-llamar / deshacer llamado | fase 2 |
| GET | /api/host/report?date= | anfitrión/gerente | reporte del día | **implementado** (09 § 2.8); sin `date`, el día en curso |
| GET/POST | /webhooks/whatsapp | Meta | verificación y eventos (botones, estados) | firma X-Hub-Signature-256, idempotente; fase 2 |
| POST | /internal/close-day | Scheduler | cierre por zona horaria | IAM; fase 2 |
| GET | /healthz · /readyz | monitoreo | vida · base de datos | |

Reglas HTTP:
- 409 si la transición es inválida (sentar a alguien que canceló).
- 200 sin efectos si ya está en el estado destino (reintento o doble toque).
- 404, no 403, para tokens o ids de otro local: no revelar que existen.
- 422 para validación. Mensajes de error en español, sin trazas.
- Repetir request_id devuelve el mismo turno; otro UUID con teléfono activo devuelve 409 sin token.
  La recuperación por teléfono la implementa `/lookup`, que devuelve el token del turno activo del día
  según la enmienda 09 § 2.5. OTP sigue diferido.
- Endpoints de acción (POST /call) en vez de PATCH {status}: cada transición tiene reglas y permisos propios,
  se lee clara en logs y es más difícil de usar mal.

## 5. Decisiones (con alternativa descartada y por qué)

D1. Servicio nuevo, separado de El Libro
- Decisión: servicio FastAPI con base propia; cada local guarda external_ref (su id en El Libro).
- Descartado: extender el PHP o leer/escribir directo en la base de El Libro.
- Por qué: el stack objetivo es FastAPI en Cloud Run; no heredar el acoplamiento; despliegue independiente;
  la lista vieja fracasó por experiencia de uso, no por falta de datos.
- Costo: maestro de locales duplicado (en v1, carga manual). Reversibilidad: media.

D2. Monolito modular: un servicio y un deploy (API + estáticos del front)
- Descartado: microservicios (cola, notificaciones, reportes) y front en CDN aparte desde el día 1.
- Por qué: una persona, 3 semanas; mismo origen = sin CORS; menos piezas que fallen un viernes. Reversible.

D3. Polling en vez de WebSocket o SSE
- Comensal cada 15 s (10 s si faltan 3 o menos), pausado con la pestaña oculta, refresco al volver, al recuperar la
  conexión y con backoff ante errores. Anfitrión cada 5 s y refresco inmediato después de cada acción.
- Números: piloto = 3 locales × 40 personas / 15 s ≈ 8 req/s. A 150 locales, el peor caso teórico
  (6.000 comensales a la vez) ≈ 400 req/s de consultas indexadas con respuestas de ~1 KB: pocas instancias de Cloud Run.
  Si hiciera falta: ETag/304 y caché de 1–2 s por local.
- Por qué no WebSocket: red móvil inestable (reconexiones, estado perdido); en Cloud Run, con varias instancias,
  hace falta *alguna* forma de repartir eventos entre ellas (Google documenta varias opciones; Redis es una, no
  la única), la conexión está sujeta al timeout de request y la instancia se factura como activa mientras dura;
  más código y más modos de falla para colas de 40 personas.
- La defensa suficiente, sin exagerar: para esta cola una demora de segundos es aceptable, y el polling la
  consigue con mucho menos que construir y operar. No hace falta que WebSocket sea imposible; basta con que
  no compense.
- Cuándo cambiaría: si el anfitrión necesita latencia menor a 1 s o el polling domina el costo → primero SSE.
- Reversible: sí; cambia el transporte, no el dominio.

D4. Posición y tiempo estimado se calculan al leer (no se guardan)
- Grupos delante = turnos "en espera" del mismo local y día de servicio con (sort_key, id) menor. Los llamados
  no cuentan. El texto público es "Hay N grupos antes que ti", no "Estás en el puesto N": con llamados fuera
  de orden, "puesto" promete una secuencia de atención que el local no cumple.
- Por qué: no hay que reescribir 40 filas en cada cambio y siempre es consistente. Reversible.

D5. Orden por sort_key (entero en milisegundos de llegada), con desempate por id
- **Se ordena y se cuenta siempre por (sort_key, id)**, nunca por sort_key solo: dos altas pueden caer en el
  mismo milisegundo, y con el reloj congelado de los tests caen siempre. Sin desempate, dos comensales ven
  el mismo número y el orden de la lista no es estable entre consultas.
- Por qué la columna y no ORDER BY id a secas: reordenar es un requisito **explícito del diseñador**, solo
  aplazado, no rechazado. Tener el hueco desde el día 1 permite contestar "cómo lo harías" con un cambio
  chico. El argumento de "evita una migración" es flojo por sí solo (agregar una columna después es fácil);
  el bueno es que la funcionalidad está prometida.
- Límite honesto: insertar enteros entre vecinos no escala indefinidamente (se agotan los huecos y hay que
  renumerar). Para un local con 40 filas al día, no es un problema real. Reversible.

D6. Máquina de estados explícita con transiciones atómicas
- UPDATE tickets SET status='called', called_at=… WHERE id=:id AND location_id=:loc AND status='waiting'
  → si rowcount = 0, releer: si ya está en el destino, 200 sin efectos; si no, 409.
- Por qué: dos anfitriones a la vez; funciona igual en SQLite (local) y MySQL (prod) sin SELECT … FOR UPDATE
  (que SQLite no soporta); evita WhatsApp duplicados.
- Sin librería de máquina de estados: un diccionario de transiciones permitidas basta.
- La reposición de un turno vencido también es atómica: `expired`, su evento, el turno nuevo y `joined`
  comparten commit. Si crear el reemplazo falla, el turno anterior conserva estado y `active_key`.

D7. Bitácora de eventos (ticket_events) además del estado actual
- De ahí salen el reporte, la auditoría ("¿quién llamó a Carla?"), la calibración del estimador y las disputas.
- Lo que no se registra desde el día 1 no se recupera para evaluar el piloto.
- No es event sourcing: el estado vive en tickets; los eventos son bitácora.

D8. Link del comensal con token aleatorio, nunca con el id
- /t/{token} con secrets.token_urlsafe(16). Respuesta mínima. Cabecera Referrer-Policy: no-referrer.
  El token deja de servir cuando el turno se cierra y pasa el día.
- Por qué: con ids secuenciales cualquiera cancela turnos ajenos (IDOR).
- Corolario que es fácil olvidar: **un token impredecible no sirve de nada si otro endpoint lo entrega.**
  Por eso el alta pública devuelve 409 sin token cuando el teléfono ya tiene turno (ver § 4).

D9. Teléfono normalizado a E.164 con la librería phonenumbers
- Región por defecto = país del local; acepta extranjeros si vienen con +prefijo. Opcional en el alta manual.
- Por qué: deduplicación, envío por WhatsApp/SMS y, más adelante, "frecuente".

D10. Tiempo: UTC en base de datos + zona IANA por local + service_date (corte 05:00 local)
- Por qué: Santiago con horario de verano, servicio que cruza medianoche, reportes por "día" correctos.
  Guardar UTC permite recalcular si cambia la definición.

D11. Multi-local desde el día 1
- location_id en todas las tablas y consultas; el local lo determina el token del anfitrión, nunca un location_id
  enviado por el cliente.

D12. Autenticación del anfitrión con token de dispositivo por local
- Prototipo: token fijo por local generado en el seed (guardado con hash), enviado como Authorization: Bearer.
- Producción: link o código de emparejamiento que crea un token largo, guardado con hash, revocable y con
  last_seen_at (que además alimenta la alarma de "tablet desconectada").
- Por qué no login por persona: la lista de El Libro murió por login + 4 pantallas; la tablet es compartida.
- Costo: no se sabe qué persona hizo cada acción (se registra el dispositivo; opcional elegir nombre al iniciar turno).

D13. Notificador como interfaz con adaptadores
- notify_table_ready(ticket). Adaptadores: Fake (local y tests), WhatsApp Cloud API, SMS.
- Producción: patrón outbox (fila en notifications dentro de la misma transacción del llamado) + Cloud Tasks
  (reintentos idempotentes por id de notificación).
- Backend implementado: Fake síncrono después del commit del llamado, en la misma petición;
  el evento de aviso tiene su propia transacción. BackgroundTasks no es necesario para un log local.
- Si el envío falla: el turno sigue "llamado", se registra notification_failed y la tablet muestra "aviso no
  entregado" para que el anfitrión llame por voz. El estado del negocio no depende de que Meta responda.
- **Lo que esto NO garantiza** (decirlo antes de que lo pregunten): el UPDATE condicional asegura una sola
  *transición*, no un solo *envío*. Si el proceso muere entre el commit y el BackgroundTask, no sale aviso.
  Si el proveedor acepta el mensaje y se pierde la respuesta, reintentar puede duplicarlo. Cloud Tasks
  documenta ejecuciones duplicadas, así que el consumidor tiene que tolerarlas. La promesa defendible es
  **"al menos una vez, con deduplicación por attempt_key y resultado a veces incierto"**, no "exactamente
  una vez". Lo que sí se garantiza siempre: el anfitrión ve en la tablet si el aviso salió o no.

D14. Canales: WhatsApp (principal) + página del turno (siempre) + SMS (respaldo)
- WhatsApp: plantilla utility con dos botones de respuesta rápida; el payload de cada botón lleva el token del turno,
  así el webhook sabe qué turno actualizar. Funciona con mala señal (WhatsApp es liviano).
- Página del turno: muestra "¡Tu mesa está lista!" con los mismos botones (gratis y sin plantilla).
- SMS: sin botones, con link a la página del turno (sin WhatsApp, o si la plantilla no está aprobada a tiempo).
- Borrador de plantilla (neutral, sin promociones, sin variable al inicio ni al final, hora absoluta):
    "Hola {{1}}, tu mesa en {{2}} está lista. Te esperamos en la entrada hasta las {{3}}."
    Botones: «Voy en camino» · «Ya no voy»

D15. Política de mensajes: uno por grupo
- Solo se envía al llamar (re-llamar con límite). No se envía "te uniste a la cola": la página ya lo muestra.
- Por qué: costo por mensaje (sube el 1/10/2026) y reputación del número compartido.

D16. Frontend: una SPA (Vite + React + TypeScript) con rutas separadas y carga diferida
- /q/:code (unirse), /t/:token (mi turno), /host (tablet). El código del anfitrión en un chunk aparte para que el
  comensal descargue lo mínimo (objetivo: menos de 100 KB gzip).
- Estado del servidor: **hook propio de polling (~40 líneas)**, no TanStack Query. Para tres pantallas, la
  dependencia no se paga sola: todo lo que entra hay que poder explicarlo y mantenerlo.
  Sin Redux, sin UI kit, sin librería de arrastrar en v1.
- Estilos: un CSS simple, sin Tailwind (configurarlo cuesta más que el CSS que hace falta y no se busca
  fidelidad pixel a pixel); botones grandes para la tablet.

D17. SQLAlchemy 2 síncrono; SQLite en local, MySQL 8 en producción; Alembic solo en producción
- Por qué síncrono: más simple de leer y defender; FastAPI ejecuta endpoints síncronos en un threadpool; la carga es baja.
- En el corte local: create_all al arrancar. En producción: Alembic como Cloud Run Job antes de mover tráfico,
  con migraciones compatibles hacia atrás (primero agregar, después quitar) para poder revertir el código
  sin tocar la base. Lo que no se hace nunca es create_all con varias instancias arrancando a la vez.
- Cuidado: solo SQL portable en el código compartido (TIMESTAMPDIFF no existe en SQLite: calcula promedios en Python
  o por dialecto) y probar contra MySQL en CI antes de producción.

D18. Validación siempre en el backend (Pydantic)
- Nombre 1–40 caracteres (sin espacios sobrantes), teléfono válido, `request_id` presente.
- Tamaño de grupo: 1 a `location.max_party_size` (20 por defecto). El CHECK 1–50 del DDL es el techo
  absoluto del dato, no el límite de negocio: son dos cosas distintas a propósito.
- **Consentimiento sin casilla**: un aviso visible encima del botón ("Al unirte aceptas que usemos tu
  teléfono solo para avisarte cuando tu mesa esté lista") y se guarda `consent_at` al unirse. La casilla
  obligatoria es un toque más en la puerta, que es exactamente lo que mató la lista de El Libro.
  Tensión reconocida: Perú exige consentimiento "expreso", y un abogado puede pedir la casilla. Va como
  pregunta a legal antes del piloto, no como supuesto técnico.
- El front valida para la experiencia, no para la seguridad.

D19. Cierre del día idempotente por zona horaria (fase 2)
- Cloud Scheduler (acepta zona horaria) a las 05:00 de cada zona → por local: "en espera" → expirado,
  "llamado" → no vino; genera daily_reports (único por local + fecha) y envía el correo una sola vez.

D20. Límites en lo público
- Rate limit por IP y por teléfono en el alta; un turno activo por teléfono y local; tope de cola opcional.
- En Cloud Run un rate limit en memoria es por instancia: suficiente para el piloto; a escala, Cloud Armor.

D21. Datos personales
- Aviso breve + consentimiento en la pantalla 1 ("Usaremos tu teléfono solo para avisarte cuando tu mesa esté lista").
- No loguear teléfonos ni tokens completos; anonimizar el teléfono a los 30 días.

D22. Separar "Se fue" de "Borrar", y "Se fue" solo desde "en espera"
- Si el anfitrión usa "Quitar" para los que se fueron, el reporte miente. "Se fue" cuenta en el reporte;
  "Borrar (error/duplicado)" no, y va en un menú secundario.
- **"Se fue" no existe en una fila ya llamada**: ahí la acción correcta es "No vino", que es lo que el
  reporte cuenta como "no vino al ser llamado". Dos caminos al mismo hecho hacen el reporte ininterpretable.
  Cada fila muestra solo los botones válidos para su estado, así el anfitrión no puede equivocarse.

D23. /internal/* no queda protegido por el hecho de llamarse "internal" (fase 2)
- El servicio de Cloud Run es público porque la página del comensal lo es, y **el permiso de invocación es
  por servicio, no por ruta**: no existe "IAM solo para /internal". Poner el prefijo y suponer que basta es
  un error que se paga con un endpoint de cierre del día abierto a internet.
- Decisión: la aplicación **verifica el token OIDC** que envían Cloud Tasks y Scheduler (emisor, audiencia y
  la cuenta de servicio esperada). Separar un segundo servicio privado es una alternativa válida, no una
  obligación. En el corte de 4 horas no se implementa: no hay endpoints internos.

## 6. Qué tan reversible es cada decisión (para la nota)

"Irreversible" se usa demasiado. Son tres cosas distintas y conviene decirlas separadas, porque cada nivel
se mitiga distinto:

**Nivel 1 — Realmente no se recupera** (no hay dinero ni tiempo que lo arregle):
1. **Los datos que no capturaste.** Si el día 1 no registras el evento, ese hecho no existe nunca. Por eso la
   bitácora entra desde el primer día aunque el reporte sea de la semana 3.
2. **El consentimiento que no pediste.** Borrar después se puede; consentir hacia atrás, no.

**Nivel 2 — Se puede cambiar, pero el costo es externo y no lo controlas tú**:
3. **La URL del QR impreso.** Pegado en 150 puertas: cambiarla es reimprimir y recorrer locales.
   Mitigación desde el día 1: dominio propio + código corto con indirección en BD (nunca *.run.app ni un id
   interno). Así el QR sobrevive a cualquier cambio de infraestructura.
4. **La plantilla y el remitente de WhatsApp.** Cambiar la plantilla implica nueva aprobación de Meta (que
   puede rechazarla); el número compartido acumula reputación —buena o mala— para los 150 locales a la vez.
5. **Los mensajes ya enviados.** Un WhatsApp no se des-envía. Por eso "Llamar" no tiene deshacer real.

**Nivel 3 — Interno y reversible, pero caro o ruidoso**:
6. **La normalización a E.164.** Reprocesar teléfonos mal guardados sale mal siempre. Ojo: E.164 normaliza el
   *contacto*, no es una identidad estable de persona (dos familias comparten número, la gente cambia de número).
7. **Las definiciones de las métricas y el modelo de tiempo.** Cambiar a mitad del piloto no rompe nada
   técnico: rompe la comparabilidad, que es justamente lo que el piloto tiene que demostrar.
8. **location_id en todas las tablas** y quién es dueño del maestro de locales (El Libro).
9. **El formato de los links vivos**: si cambia, se rompen los del día. Impacto acotado a unas horas.

Se pueden cambiar (decidir rápido):
polling vs SSE, intervalos, fórmula del tiempo estimado, librerías del front, estructura de carpetas, síncrono vs
asíncrono, reordenamiento, textos de pantalla (salvo la plantilla), proveedor de correo, implementación del rate limit,
servir el front desde Cloud Run o desde un CDN.

## 6.1 Las que no se deberían cambiar después (decisión del 18/09/2026)

§ 6 es el catálogo en tres niveles. **Esto es lo que va en la nota**: cuatro decisiones propias más una
que sale del catálogo y no debería faltar. Cada una dice también *qué se rompe si se cambia tarde*, que
es lo que convierte la lista en un argumento y no en un inventario.

1. **Cada espera tiene su propio identificador; el teléfono no es la identidad.** `tickets.id` para uso
   interno y `public_token` opaco en el link del comensal. El teléfono es una **llave de búsqueda**
   —`active_key` y la pantalla «Ya estoy en la lista de espera»—, nunca la identidad de la espera.
   Si se cambia tarde: E.164 normaliza el *contacto*, no a la persona; dos familias comparten número y la
   gente cambia de número, así que una identidad basada en el teléfono se corrompe sola (§ 6 punto 6).

2. **Los estados, definidos desde el día 1**: `waiting`, `called`, `seated`, `cancelled`, `no_show` —y en
   el modelo también `removed` (alta por error) y `expired`, que conviene tener aunque no se usen aún.
   Lo difícil de deshacer no es el enum, es **la definición de la métrica**: qué cuenta como "se fue sin
   sentarse", si «Ya no voy» después del llamado es abandono o no-show, y desde dónde se mide la espera
   media (llegada → sentado). Cambiarlo a mitad del piloto no rompe nada técnico: rompe la comparabilidad,
   que es exactamente lo que el piloto tiene que demostrar (§ 6 punto 7).

3. **Cada espera pertenece a un local.** `location_id` en todas las tablas y en **toda** consulta, y el
   local sale del token del anfitrión, jamás del body. Si se cambia tarde: un local viendo la cola de otro
   no es un bug que se parchea, es una fuga de datos entre clientes; por eso tiene un test no negociable
   propio (09 § 7.1, test 4).

4. **El modelo de tiempo.** UTC en la base, escrito siempre por la aplicación; zona IANA por local; día de
   servicio con hora de corte configurable por local. El piloto cruza dos husos —Santiago va 2 horas
   adelante de Lima— y un viernes que termina a las 00:30 sigue siendo viernes. Si se cambia tarde:
   reprocesar fechas mal guardadas sale mal siempre, y todo el reporte se recalcula con otro significado.

5. **La URL del QR impreso** (esta sale de § 6, nivel 2, y es la más cara de todas). Está pegada en la
   puerta; a 150 locales, cambiarla es reimprimir y recorrer locales uno por uno. Mitigación desde el día 1:
   dominio propio y código corto con indirección en base — nunca un `*.run.app` ni un id interno. Así el QR
   sobrevive a cualquier cambio de infraestructura.

Y el recordatorio que enmarca la lista: lo único **verdaderamente** irrecuperable es el nivel 1 de § 6 —el
evento que no registraste y el consentimiento que no pediste—. Por eso la bitácora entra desde el primer
día aunque el reporte sea de la semana 3.

## 7. Lo que la IA te va a proponer y conviene rechazar (con argumento)
| Propuesta típica | Respuesta |
|---|---|
| WebSocket / Socket.IO | No: red móvil mala; Cloud Run con varias instancias necesita Redis; 40 personas por cola. Polling. |
| Redis, Celery, RabbitMQ | No en v1: BackgroundTasks en local; en producción, Cloud Tasks (administrado). |
| Repositorio genérico + Unit of Work + CQRS + hexagonal completo | No: tres entidades; un módulo de dominio con transiciones basta. |
| Microservicios | No: una persona, un deploy. |
| Event sourcing | No: estado + bitácora de eventos. |
| JWT con refresh, OAuth, roles | No: token de dispositivo por local. |
| Redux, Zustand, MUI | No: estado del servidor con polling; CSS simple; bundle chico. |
| dnd-kit / librería de arrastrar | No en v1: sin arrastrar. |
| Docker + Kubernetes + Terraform | No en el corte de 4 h: se documenta (Cloud Run + Cloud SQL + GitHub Actions con OIDC). docker-compose solo si sobra tiempo. |
| PWA offline con sincronización | No: conflictos; banner de sin conexión y reintentos. |
| Estimación con ML | No: fórmula simple + guardar prometido vs real para calibrar con datos del piloto. |
| Snapshots o 80 % de cobertura | No: tests de fallos. |
| Framework de i18n | No: español; textos centralizados. |
| create_all() en producción | No: Alembic como job antes de mover tráfico. (En local, create_all y se documenta.) |
| Alembic dentro del corte de 4 h | No: 15–20 min que no compran nada en local. Se documenta cómo sería en producción. |
| TanStack Query / SWR para 3 pantallas | No: un hook de ~40 líneas, sin una dependencia más que mantener. |
| Tailwind / shadcn "porque es rápido" | No: la configuración cuesta más que el CSS que hace falta y no se busca fidelidad pixel a pixel. |
| SQLAlchemy async "por rendimiento" | No hace falta: carga baja, código más simple. |
| SELECT … FOR UPDATE | No: UPDATE condicional; portable y suficiente. |

## 8. Mapa .NET/Azure → Python/GCP (equivalencias de referencia)
| Tú conoces | Aquí es |
|---|---|
| Controller / Minimal API | APIRouter + funciones con @router.get / @router.post |
| Inyección de dependencias (IServiceCollection) | Depends() |
| DTO + DataAnnotations / FluentValidation | Modelos Pydantic v2 |
| DbContext (EF Core) | Session de SQLAlchemy |
| EF Migrations | Alembic |
| IOptions / appsettings.json | pydantic-settings (.env) |
| Middleware | Middleware de Starlette |
| xUnit + WebApplicationFactory | pytest + TestClient + app.dependency_overrides |
| IHostedService / Hangfire | BackgroundTasks (simple) / Cloud Tasks (producción) |
| RxJS interval + HttpClient (Angular) | useEffect + setTimeout, o TanStack Query con refetchInterval |
| Azure Container Apps / App Service | Cloud Run |
| Azure Database for MySQL / Azure SQL | Cloud SQL |
| Key Vault | Secret Manager |
| Application Insights / Azure Monitor | Cloud Logging + Cloud Monitoring + Error Reporting |
| Azure Functions (timer) / Logic Apps | Cloud Scheduler |
| Service Bus / Storage Queue | Cloud Tasks / Pub/Sub |
| GitHub Actions con OIDC hacia Azure | GitHub Actions con Workload Identity Federation hacia GCP |

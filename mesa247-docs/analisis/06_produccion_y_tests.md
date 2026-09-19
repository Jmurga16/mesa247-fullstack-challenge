# 06 · Producción, operación y tests que importan

## 0. La respuesta corta (lo que va en la nota, decisión del 18/09/2026)

**Despliegue.** Google Cloud: contenedor → Artifact Registry → **Cloud Run** en southamerica-west1, cerca
de los tres locales. Base: **Cloud SQL MySQL 8 en el piloto**, por los backups automáticos, la recuperación
a un punto en el tiempo y la IP privada; **Aiven (tier gratuito) para la demo y el entorno de prueba**,
que es donde el coste importa y el dato no. Secretos en Secret Manager, despliegue con rollback de tráfico
en un comando.

**Cómo me entero de que falla.** Cloud Monitoring, con aviso **por correo y al celular**. Cuatro alarmas,
no una: uptime externo (la caída obvia), 5xx (el deploy malo), **silencio del negocio** —cero altas en un
local en horario normal— y avisos fallidos. Las dos primeras las ve cualquier health check; **la tercera es
la que importa un viernes a las 9**, porque la API puede responder 200 mientras el QR está roto o la página
no carga en móviles, y ahí nadie se entera hasta que el anfitrión llama.

**Qué hago cuando pasa.** Los logs tienen que servir para arreglarlo sin adivinar: JSON con `request_id`,
`location_id`, `ticket_id` y actor, con teléfonos enmascarados y sin tokens, más Error Reporting para las
excepciones. Con eso, quien esté de guardia —o cualquier otro desarrollador— ubica el caso concreto. El
primer movimiento casi siempre es el mismo: si hubo deploy, devolver el tráfico a la revisión anterior; y
la operación no se detiene, porque la tablet conserva la última cola conocida y el local tiene plan B en
papel.

Detalle en § 1 (despliegue), § 3 (alarmas) y § 4 (el viernes a las 9).

## 1. Despliegue
- Un contenedor (FastAPI + build de React) → Artifact Registry → Cloud Run en southamerica-west1 (Santiago),
  cerca de los tres locales del piloto.
- Cloud SQL MySQL 8: conector de Cloud SQL o IP privada, backups automáticos + recuperación a un punto en el tiempo,
  usuario con mínimos privilegios.
- **Demo y staging: MySQL gestionado en Aiven, tier gratuito.** Sirve para que cualquiera levante el proyecto
  sin una cuenta de GCP y para probar contra MySQL real (los tests del corte corren en SQLite, y la deuda 8 de
  09 § 9 pide exactamente esto). No se usa en el piloto, y conviene decir por qué en la nota: los planes
  gratuitos no traen backups ni recuperación a un punto en el tiempo, el endpoint es público con TLS —no hay
  conector ni IP privada— y si la región no coincide con southamerica-west1 cada consulta paga latencia entre
  nubes justo el viernes a las 9.
- Migraciones con Alembic como Cloud Run Job ANTES de mover tráfico (no al arrancar la app: varias instancias
  migrando a la vez). Migraciones compatibles hacia atrás (primero agregar, después quitar) para poder hacer rollback
  del código sin tocar la base.
- Secretos en Secret Manager (token de WhatsApp, app secret de Meta, credenciales SMS, pepper de tokens).
- CI/CD: GitHub Actions → tests → build → deploy con Workload Identity Federation (sin llaves JSON) → nueva revisión
  con tag y sin tráfico → smoke test → 100 % del tráfico. Rollback = devolver el tráfico a la revisión anterior
  (un comando, segundos).
- min-instances = 1 durante el horario de servicio: el primer comensal del viernes no espera un arranque en frío.
- Dominio propio con certificado administrado; el QR apunta a fila.mesa247.pe/q/{codigo} (indirección en BD).
- Flags por local: is_active, whatsapp_enabled, sms_enabled, canal preferido. Interruptor global para apagar envíos
  (costo o problema de calidad).
- Congelamiento: no desplegar viernes ni sábado desde las 17:00 del local más temprano.
- Docker y CI quedan fuera del corte de 4 horas: se documentan en 3 líneas en la nota, no se implementan.

## 2. Observabilidad
- Logs JSON con request_id, location_id, ticket_id y actor. Nunca teléfonos completos ni tokens (enmascarar).
- Error Reporting (o Sentry) para excepciones.
- Métricas (log-based o OpenTelemetry): altas por minuto por local, llamados, avisos enviados/entregados/fallidos,
  latencia p95, tasa de 5xx, largo de la cola, llamados sin respuesta.
- Cada host_device actualiza last_seen_at con su polling.

## 3. Alarmas
**Cuatro son prioritarias; el resto es catálogo.** Las cuatro: uptime externo (la caída obvia),
errores 5xx (el deploy malo), **silencio del negocio** (lo que un health check nunca ve) y **avisos
fallidos** (el producto roto aunque la API responda 200). Son las que van en la nota de 1–2 páginas;
la tabla completa queda aquí como referencia de operación.

| Alarma | Condición | Qué detecta |
|---|---|---|
| Uptime externo | /healthz falla 2 veces seguidas (chequeo cada minuto desde varias regiones) | caída total, DNS, certificado |
| Base de datos | /readyz falla o Cloud SQL con CPU, conexiones o disco > 80 % | base caída o saturada |
| Errores | 5xx > 2 % en 5 min | deploy malo, bug |
| Latencia | p95 > 1,5 s en 5 min | base lenta, instancias al límite |
| **Avisos fallidos** | > 5 % en 10 min, o 3 seguidos en un local | Meta caído, plantilla pausada, token vencido, saldo |
| **Silencio del negocio** | local piloto con 0 altas en 30 min dentro del horario en que normalmente hay | QR roto, página rota en móviles, algo que los chequeos técnicos no ven |
| Tablet desconectada | ningún host_device del local visto en 10 min, en horario de servicio | wifi de la puerta, tablet apagada o sin batería |
| Llamados sin respuesta | > 50 % de los llamados sin «Voy en camino», Sentar ni No vino en 15 min | los avisos no llegan aunque la API diga "enviado" |
| Webhook | firmas inválidas o errores en /webhooks/whatsapp | secreto rotado, ataque |
| Costo | presupuesto de GCP y gasto diario de WhatsApp sobre el umbral | bucle de reenvíos |

Destino: Cloud Monitoring → notificación al celular de guardia (app de Google Cloud, PagerDuty u Opsgenie) + correo.
En el piloto la guardia eres tú: defínela por escrito (viernes y sábado, 19:00–00:30 hora de cada local).

Dos límites que conviene admitir antes de que los señalen:
- Las alarmas **porcentuales necesitan volumen mínimo** (un 5 % sobre 3 mensajes no significa nada) y un
  horario: si no, suenan a las 4 de la mañana de un martes y en dos semanas nadie las mira.
- "Cero altas en 30 minutos" **no prueba una caída** sin línea base. Con 3 locales, la línea base se saca
  de las dos primeras semanas del piloto; antes de eso, la alarma se configura ancha y se afina después.
  Una alarma que nadie atiende es peor que no tenerla.

## 4. "Se cae un viernes a las 9 de la noche": cómo me entero y qué hago
Cómo me entero (en orden de velocidad):
1. El uptime check y la alarma de 5xx llegan al celular en 1–2 minutos.
2. Si la API "está bien" pero algo falla para el público: la alarma de silencio del negocio o la de tablet desconectada.
3. Último recurso, pero previsto: el encargado del local tiene un número al que escribir (el tuyo) y lo sabe desde la
   capacitación.
Qué hago (runbook corto):
0. La operación primero: la tablet muestra la última cola conocida con un aviso de "sin conexión" y el anfitrión
   pasa al plan B en papel (hoja de contingencia) y llama por voz. Esto se practica en la capacitación.
1. ¿Hubo deploy? → rollback de tráfico a la revisión anterior.
2. ¿Es la base? → estado de Cloud SQL; reinicio o failover; restaurar desde backup si hay corrupción.
3. ¿Es WhatsApp? → estado de Meta y errores de la API; pasar el local a SMS con el flag; avisar a los anfitriones.
4. ¿Es un solo local? → wifi, tablet o QR; llamar al encargado.
5. Comunicar: mensaje al grupo de encargados (qué pasa, qué hacer, cuándo vuelve).
6. Después: cargar lo que faltó si hace falta para el reporte, postmortem sin culpables y un test que lo cubra.

## 5. Capacidad y costos (con números y de qué dependen)
Carga
- Piloto: 3 locales × hasta 40 turnos activos, polling cada 15 s → ~8 req/s en el pico. Una instancia sobra.
- 150 locales: **escenario, no medición**. Peor caso teórico 6.000 comensales a la vez → ~400 req/s de
  consultas por índice sobre ~40 filas. Pocas instancias. El número omite las tablets y los intervalos
  acelerados, así que es un piso, no un techo: antes de afirmar capacidad hay que medirlo con una prueba
  de carga. Vigilar conexiones: instancias × tamaño del pool ≤ máximo de Cloud SQL.
- Depende de: intervalo de polling, horas pico simultáneas entre países, uso real de la tablet.
WhatsApp (depende del volumen real, del % de llamados, de la mezcla de países y de las tarifas vigentes de Meta)
- Supuesto de piloto: ~2.500 altas al mes por local (viernes y sábado ~140; otros días ~60), **~78 % llamados
  y un solo mensaje por llamado** → ~1.950 mensajes al mes por local.
  El 78 % es un supuesto, no un dato: sale de 111/142 del reporte del prototipo, y eso **asume que todo el
  que se sentó fue llamado antes**, cosa que el propio diseño desmiente (se puede sentar a alguien que ya
  está en el mostrador). Es un techo razonable para presupuestar; preséntalo así.
- Lima, 2 locales: ~3.900 mensajes × ~US$0,03 ≈ US$117 al mes.
- Santiago, 1 local: ~1.950 mensajes × ~US$0,02 ≈ US$39 al mes.
- Piloto ≈ US$150–160 al mes.
- 150 locales con un promedio de 1.000 altas al mes → ~117.000 mensajes → ~US$2.300–3.500 al mes.
  Un mensaje extra de "te uniste" lo duplicaría: por eso, uno por grupo.
- Tarifas de referencia tomadas de avisos de BSP sobre el cambio del 1/10/2026. **No están confirmadas en el
  rate card oficial de Meta**: si las citas, cítalas como "según avisos de proveedores, a confirmar", nunca
  como dato verificado. El argumento de diseño (un mensaje por grupo) se sostiene igual sin la cifra exacta.
  Colombia es mucho más barato (~US$0,0008), así que la mezcla de países mueve mucho el total.
  Ojo adicional: Meta cobra por **mercado del destinatario**, no por país del restaurante — un turista con
  número extranjero en Santiago se cobra a su tarifa, no a la chilena.
Infraestructura
- Cloud Run + Cloud SQL del piloto: del orden de decenas de dólares al mes (Cloud SQL es el costo fijo principal).
  Confirmar con la calculadora de GCP antes de dar una cifra.

## 6. Seguridad y datos personales (checklist)
[ ] Tokens aleatorios en links; 404 para lo ajeno; respuestas públicas sin teléfono ni datos de otros.
[ ] CORS cerrado (mismo origen), HTTPS, HSTS, Referrer-Policy: no-referrer.
[ ] Rate limit en el alta; límites de tamaño; validación en el backend.
[ ] Token de dispositivo guardado con hash y revocable.
[ ] Webhook: verificación del token de suscripción y de la firma X-Hub-Signature-256; idempotencia por id.
[ ] Endpoints internos: **el permiso de invocación de Cloud Run es por servicio, no por ruta**. Como el
    servicio es público (la página del comensal lo es), /internal/* no queda protegido por llamarse así:
    la aplicación verifica el token OIDC de Cloud Tasks / Scheduler (emisor, audiencia y cuenta de servicio).
[ ] Aviso y consentimiento en la pantalla 1; retención de 30 días para el teléfono; borrar por teléfono a pedido.
[ ] Logs sin datos personales, **y eso incluye los que no escribe tu código**: Cloud Run registra la URL
    completa con su query string, así que un token en `?token=` queda guardado aunque la app no lo loguee
    y aunque JavaScript limpie la URL después (ya viajó en la primera petición). El link fijo del seed es
    una comodidad local; en el piloto la tablet se empareja, no recibe un link con el token dentro.
[ ] La retención no es solo `phone_e164`: el nombre, el JSON de `ticket_events`, los payloads del webhook,
    los logs y los respaldos también son datos personales. Política por tipo de dato, no por columna.
[ ] Perú: incidentes con datos personales se notifican en 48 horas (reglamento vigente desde 2025).

## 7. Tests que importan (orientados a fallos)
**La lista congelada del corte de 4 horas está en `09_alcance_y_plan_de_implementacion.md` § 7**: seis no negociables
(idempotencia y no-filtración del alta, doble llamado, transiciones inválidas, aislamiento entre locales,
liberación de `active_key` en todo estado terminal, normalización de teléfonos) y cinco que van si alcanza.
La tabla de abajo es el catálogo completo, incluidos los de fase 2.
| # | Test | Qué se rompería sin él |
|---|---|---|
| T1a | test_join_retry_same_request_id_returns_same_ticket | red mala o doble toque → turnos duplicados |
| T1b | test_join_same_phone_other_request_id_returns_409_without_token | un tercero que conoce el teléfono se queda con el turno ajeno |
| T1c | test_terminal_states_release_active_key (parametrizado) | un cierre olvida liberar la clave y ese teléfono no puede volver a la cola |
| T2 | test_same_phone_other_location_is_allowed | active_key mal armado bloquea a alguien en otro local |
| T3 | test_call_twice_sends_one_notification | dos anfitriones → dos WhatsApp; el 2.º debe ser 200 sin efecto |
| T4 | test_invalid_transitions_return_409 | sentar a un cancelado, no-show de uno en espera, cancelar a un sentado |
| T5 | test_position_ignores_called_and_closed + empate de sort_key | posiciones mal calculadas tras llamar, cancelar o sentar; dos altas en el mismo ms comparten número |
| T6 | test_host_cannot_touch_other_location | fuga entre locales (token de A sobre turno de B → 404) |
| T7 | test_public_ticket_does_not_leak_data | teléfono u otros nombres en la respuesta pública; token inventado → 404 |
| T8 | test_notifier_failure_keeps_ticket_called | Meta falla → se pierde el llamado o explota el endpoint |
| T9 | test_service_date_after_midnight_and_santiago | 00:30 del sábado cuenta como viernes; Santiago en UTC-3 |
| T10 | test_close_day_report_partition | se unieron ≠ sentados + se fueron + no vinieron |
| T11 | test_phone_normalization | "987 654 321" (PE) → +51987654321; "9 8765 4321" (CL) → +56987654321; inválido → 422 |
| T12 | test_whatsapp_webhook_is_idempotent_and_signed (fase 2) | Meta reintenta → doble transición; firma falsa aceptada |

Detalles prácticos
- Usa números de prueba válidos: phonenumbers valida rangos reales. "+56 9 1234 5678" sale inválido; "+56 9 8765 4321"
  es válido (verificado).
- Concurrencia real en SQLite es limitada: T3 prueba la condición del UPDATE de forma **secuencial**
  (segundo llamado = sin efecto y un solo aviso). **No demuestra concurrencia**, y dos pestañas de tablet
  tampoco garantizan simultaneidad: son dos toques rápidos. El límite se declara tal cual en la nota:
  atribuirle al test una garantía que no da es peor que reconocerlo. La versión con dos conexiones
  reales corre contra MySQL en CI.
- SQLite necesita `journal_mode=WAL` y `busy_timeout`: sin eso, dos escrituras a la vez dan
  "database is locked" en plena demo.
- Notificador en tests: un fake que cuenta llamadas o que lanza excepción, inyectado con dependency_overrides.
- Fechas en tests: reloj inyectable (función now()) para no depender de la hora real.

No testearía (y lo diría): que la página renderiza, CRUD triviales, getters, snapshots de UI, porcentaje de cobertura.

## 8. Prueba manual de punta a punta
[ ] Clon limpio → README → todo arriba en 5 minutos o menos (anota cuánto tardó).
[ ] Vista móvil del navegador: unirse con un teléfono PE válido → ver posición y ETA.
[ ] Unirse otra vez con el mismo teléfono → mismo turno.
[ ] Tablet: aparece la fila → Llamar → en el celular aparece "¡Tu mesa está lista!".
[ ] «Voy en camino» se ve en la tablet → Sentar.
[ ] Otro turno: Llamar → No vino. Otro: «Ya no voy» desde el celular → desaparece de la tablet.
[ ] Recargar la página de unirse y reenviar el formulario → el mismo turno, no uno nuevo.
[ ] Otro navegador, mismo teléfono → "ya tienes un turno activo", SIN llevarte al turno ajeno.
[ ] Dos pestañas de tablet: Llamar en ambas → un solo aviso en el log.
[ ] Cortar el backend 30 s → el celular muestra "sin conexión" y se recupera solo.
[ ] Token de tablet inválido → no se ve nada.

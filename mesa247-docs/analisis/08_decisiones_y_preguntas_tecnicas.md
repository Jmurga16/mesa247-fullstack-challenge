# 08 · Decisiones y preguntas técnicas frecuentes

Catálogo de las preguntas que este diseño provoca y de la respuesta corta a cada una. Sirve para
revisar una decisión sin releer el documento entero y para que cualquiera que retome el proyecto
entienda por qué está hecho así.

Donde una respuesta contradiga a `09_alcance_y_plan_de_implementacion.md`, manda el 09.

## 1. Preguntas sobre el diseño

1. ¿Por qué este corte y no otro?
   → El piloto necesita reemplazar el cuaderno sin dejar a nadie fuera y medir el abandono. Lo demás mejora la
     experiencia pero no bloquea. Estimaciones: 14–15 días de 15; por eso quedan fuera arrastrar y frecuente.
2. ¿Por qué no WebSocket? ¿Cuándo sí?
   → Wifi malo y datos móviles; en Cloud Run con varias instancias necesita pub/sub externo, hay timeout y la
     instancia se factura activa. Con 40 personas, polling de 15 s son ~8 req/s. SSE si el anfitrión necesita < 1 s.
3. Dos anfitriones tocan "Llamar" a la vez, ¿qué pasa?
   → UPDATE condicional por estado; la base serializa; uno obtiene rowcount 1 y envía; el otro obtiene 0, relee,
     ve "llamado" y responde 200 sin enviar. Un solo WhatsApp.
4. El comensal pierde la señal al unirse y reintenta, ¿qué pasa?
   → El navegador genera un request_id antes de enviar: el reintento trae el mismo id y devuelve el mismo
     turno (idempotencia), incluso si el turno ya terminó. Aparte, active_key (local + día + teléfono)
     impide dos turnos activos con el mismo número (deduplicación). Son dos cosas distintas a propósito.
4b. ¿Y si alguien se une con el teléfono de otra persona?
   → Recibe 409 "ya tienes un turno activo" y **nunca el token**. Conocer un teléfono no acredita posesión;
     si el alta devolviera el turno existente, cualquiera que vea el QR de la puerta —que es público— podría
     cancelar turnos ajenos. La recuperación desde otro teléfono la hace el anfitrión en la tablet: meter
     un OTP aquí sería reinventar el login que mató a la lista de El Libro.
4c. La cola no filtraba por día. ¿Qué pasa el sábado con un pendiente del viernes?
   → Por eso service_date entra en active_key y en la consulta de la cola: el pendiente de ayer no aparece
     hoy ni bloquea a ese teléfono. Queda abierto hasta el cierre diario, que en el piloto corre a las 05:00
     de cada zona y en el corte de 4 horas no está implementado (deuda declarada).
5. ¿Cómo se calculan posición y tiempo? ¿Qué tan precisos son?
   → Grupos delante = los waiting del mismo local y día con (sort_key, id) menor; los llamados no cuentan.
     Tiempo = (grupos delante + 1) × minutos por grupo, redondeado hacia arriba, mínimo 5.
     Es una heurística **sin calibrar** y así se dice en pantalla ("≈ 28 min, depende de las mesas que se
     liberen"): si no se libera ninguna mesa, falla por mucho. Se guardan quoted_wait_min y position_at_join
     para medir el error desde el día 1. El desempate por id existe porque dos altas pueden caer en el
     mismo milisegundo y, sin él, dos personas ven el mismo número.
6. ¿Qué es irreversible y por qué el QR?
   → Está impreso en la puerta; a 150 locales no se reimprime. Por eso dominio propio + código con indirección.
     Además: identidad por teléfono, plantilla/remitente, definiciones de métricas, modelo de tiempo, eventos,
     consentimiento. El detalle, en tres niveles, está en `03_arquitectura_y_decisiones.md` § 6.
7. ¿Cómo se detecta una caída un viernes a las 9 pm y qué se hace?
   → Uptime + 5xx al celular; alarma de silencio del negocio y de tablet desconectada; runbook: plan B en papel,
     rollback, base, WhatsApp→SMS, comunicar. Detalle en `06_produccion_y_tests.md` § 4.
8. ¿Cuánto cuesta WhatsApp? ¿Y si Meta rechaza la plantilla?
   → Fórmula con supuestos (piloto ~US$150–160 al mes; 150 locales ~US$2.300–3.500). Los supuestos importan más
     que el total: ~2.500 altas/mes/local y ~78 % llamados — y ese 78 % sale de 111/142 del prototipo asumiendo
     que todo el que se sentó fue llamado, cosa que el diseño no garantiza. **Sobre el cambio de tarifas del
     1/10/2026: "según avisos de BSP, a confirmar en el rate card de Meta"**, no como dato verificado; el
     argumento (un mensaje por grupo) se sostiene igual sin la cifra. Meta cobra por mercado del destinatario,
     no por país del local: un turista se cobra a su tarifa.
     Si rechaza la plantilla: variantes enviadas el día 1, SMS con link y la página del turno.
9. ¿Qué se rompe primero al pasar a 150 locales?
   → Primero la operación (alta de locales, QRs, tablets, soporte, reputación del número compartido), después el
     costo de mensajes; lo técnico (polling, conexiones a la base) se resuelve con índices, ETag y ajustes.
10. ¿Por qué SQLite en local si producción es MySQL?
    → Levanta en 5 minutos sin instalar nada. Riesgo: diferencias de SQL (TIMESTAMPDIFF, bloqueos) → SQL
      portable y, en CI, los tests contra MySQL.
11. ¿Zonas horarias?
    → UTC en base, zona IANA por local, service_date con corte 05:00. Santiago está en UTC-3 desde el 6/09.
12. ¿Qué se expone al público?
    → Link con token aleatorio; la respuesta solo trae estado, posición y tiempo; nada de teléfonos; 404 para lo ajeno;
      rate limit; aviso y consentimiento; retención de 30 días.
13. ¿Y El Libro?
    → Fuente de verdad de locales; v1 sin integración (external_ref); después, apagar su lista vieja en los locales
      piloto para no tener dos listas; frecuente e integración de mesas en fases siguientes.
14. ¿Cómo se probaría el webhook de WhatsApp?
    → Payloads grabados de Meta en tests, verificación de firma con un secreto de prueba, idempotencia por id.
15. ¿Por qué SQLAlchemy síncrono? ¿Qué hace FastAPI con un endpoint def?
    → Lo ejecuta en un threadpool; para esta carga es suficiente y el código es más simple.
16. Si el diseñador insiste en arrastrar, ¿cómo se haría?
    → sort_key entre vecinos, versión de la cola para detectar conflictos, evento "moved", y la vista del comensal
      sin animar subidas.
17. El test de doble llamado no prueba concurrencia real.
    → Correcto. Prueba la condición del UPDATE de forma secuencial; dos pestañas tampoco son simultaneidad.
      La versión con dos conexiones reales corre contra MySQL en CI. El límite queda declarado, no disimulado.
18. Si "Llamar" y "Sentar" llegan a la vez sobre la misma fila, ¿qué gana?
    → Ambos filtran por status='waiting'; uno gana, el otro relee, ve un estado que no es su destino y
      recibe 409. La tablet refresca y muestra "Otro anfitrión ya lo atendió". Sin el 409 el segundo
      anfitrión creería que su acción se aplicó.
19. ¿Por qué no hay casilla de consentimiento?
    → Un toque más en la puerta es exactamente lo que mató la lista de El Libro. Aviso visible sobre el
      botón y consent_at guardado al unirse. Tensión reconocida: Perú pide consentimiento "expreso", así
      que va como pregunta a legal antes del piloto, no como supuesto técnico.
20. ¿Por qué no se usa Alembic?
    → Porque en local no compra nada y cuesta 15–20 minutos del corte de 4 horas. En producción va como Cloud Run
      Job antes de mover tráfico, con migraciones compatibles hacia atrás para poder hacer rollback del
      código sin tocar la base. Lo que no se hace nunca es create_all al arrancar con varias instancias.
21. Llegan 4 personas y resultan 6. ¿Qué hace el anfitrión?
    → Hoy: borrar y volver a agregar. Es deuda declarada y va a pasar la primera semana del piloto.
22. El comensal tiene el teléfono bloqueado cuando lo llaman. ¿Se entera?
    → Por la página, no: el polling se pausa con la pestaña oculta y no despierta un teléfono bloqueado.
      Por eso WhatsApp no es "un canal más": es el único que alcanza a alguien que se alejó. Si Meta
      rechaza la plantilla, la regla del piloto pasa a ser "quédate cerca" + llamado por voz.
23. ¿Por qué el id interno en la API del anfitrión y un token en la pública?
    → La del anfitrión está autenticada y el token de dispositivo ya acota el local; el id se lee mejor en
      logs. La pública no tiene sesión, así que el identificador tiene que ser impredecible o es un IDOR.
24. ¿Qué se haría distinto con más tiempo?
    → La lista está en `09_alcance_y_plan_de_implementacion.md` § 9 (deuda conocida): cierre del día,
      entrega verificable de avisos, rate limiting, cambiar el tamaño de un grupo, atribución por persona
      y tests contra MySQL.

## 2. Conceptos del código que conviene dominar

FastAPI: path operations y routers; modelos Pydantic (validación y respuesta); Depends (sesión y autenticación);
HTTPException y códigos; BackgroundTasks; cómo se ejecutan def vs async def; TestClient y dependency_overrides.

SQLAlchemy 2: engine, Session, select(), commit/rollback, update() con where y rowcount; qué hace create_all vs Alembic.

React: useEffect y su limpieza (polling con setTimeout + AbortController), pausar con document.visibilityState,
estados de carga/error, evitar el doble envío, lazy + Suspense para separar el código de la tablet, proxy de Vite.

Conceptos transversales: idempotencia, compare-and-set, outbox, IDOR, E.164, service_date, rollback de tráfico,
expand/contract.

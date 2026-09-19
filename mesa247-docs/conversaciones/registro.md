# Registro de prompts y decisiones

Este archivo se actualiza durante el desarrollo. Cada entrada registra una solicitud relevante y la decisión resultante, sin reemplazar la exportación completa de la conversación.

## 2026-09-18 — Análisis previo

**Prompt o solicitud**

Analizar el enunciado y el prototipo antes de programar, proponer el alcance, la arquitectura y el orden de implementación, y auditar después la propuesta con un segundo modelo.

**Decisión**

Usar dos puntos de vista antes de iniciar: Claude Opus Extra para el análisis inicial y GPT Astra High para la auditoría. Los prompts consolidados están en [`prompt_inicial.md`](prompt_inicial.md).

**Resultado**

Se generaron los documentos de `../analisis/`, la revisión de `../auditoria/` y el alcance final de implementación.

**Correcciones o rechazos**

La auditoría detectó contradicciones y riesgos; su resolución está documentada en [`../auditoria/02_resolucion_de_hallazgos.md`](../auditoria/02_resolucion_de_hallazgos.md).

## 2026-09-18 — Entregable 1: preguntas al diseñador, enmienda del alcance y cierre de la nota

**Parte del proyecto:** nota.

**Prompt o solicitud**

Cerrar las tres preguntas al diseñador que pide el enunciado, respondidas por el autor, y dejarlas
registradas de forma trazable porque forman parte del entregable 1. Las tres planteadas: si la posición
que ve el comensal debe subir cuando el anfitrión reordena; si la lista debe contemplar zonas o ambientes;
y si el comensal debe poder recuperar su turno con el teléfono tras cerrar la página. Después, cerrar los
demás puntos de la nota con las respuestas del autor: qué se le devuelve al diseñador, qué decisiones no se
deberían cambiar más adelante y cómo se lleva a producción.

**Decisión**

1. Las tres preguntas que van en la nota son las del autor, no las tres que proponía el análisis previo
   (07 § 3). Quedan en [`../analisis/07_disenador_preguntas_y_devolucion.md`](../analisis/07_disenador_preguntas_y_devolucion.md) § 3.1,
   que manda sobre § 3; las candidatas se conservan como registro del análisis.
2. El número visible al comensal nunca sube: se muestra el menor entre el valor calculado y el último ya
   mostrado. En el corte de 4 horas el caso no se da (reordenar está fuera), así que la regla no cuesta
   nada ahora y evita rehacer la pantalla cuando entre reordenar.
3. Sin zonas ni ambientes en esta versión: una sola lista por local. Una cola por zona son N colas y
   cambiaría posición, ETA, deduplicación por teléfono y reporte.
4. Sí se puede recuperar el turno con el teléfono desde «Ya estoy en la lista de espera». Esto reabre una
   decisión congelada (09 § 2.1 O3 y 08 § 4b, que prohibían revelar el token a quien solo conoce el
   teléfono). Motivo: perder el link es un hecho diario y no tener salida devuelve al comensal a la puerta.
   Se asume el riesgo —con el código público del QR y un número se puede abrir y cancelar ese turno— y se
   declara; el OTP queda como mitigación fuera del corte.
5. **Devolución al diseñador**: dos prioridades, no cinco. La posición al reordenar (que el comensal no vea
   que retrocedió) y aplazar WhatsApp para validar antes registro, cola y llamado. Se aclaró el alcance del
   aplazamiento: WhatsApp queda fuera del corte de 4 horas (notificador falso), **pero sigue dentro del
   piloto de 3 semanas**; no se reescribe el plan de 05 § 2.
6. **Decisiones difíciles de cambiar**: las cuatro del autor —id propio de la espera y el teléfono como
   llave de búsqueda, no como identidad; los estados y sobre todo la definición de las métricas; cada
   espera atada a un local; el modelo de tiempo con Lima y Santiago— más la URL del QR impreso, que se
   añadió por ser la más cara de todas y no estaba en la lista inicial.
7. Los seis puntos se redactan en un documento aparte —`entregables/01_nota_tecnica.md`— en vez de dejarlos
   repartidos por `analisis/`. Motivo: el entregable es la nota, y el análisis es lo que la respalda; tenerlos
   mezclados obligaba a reconstruirla al final. Restricción dura: 1–2 páginas.
8. **Producción**: Cloud Run y Cloud Monitoring con aviso por correo y al celular, logs JSON con
   `request_id`, `location_id`, `ticket_id` y teléfonos enmascarados para que cualquiera pueda
   diagnosticar. Base: **Aiven (tier gratuito) para demo y staging, Cloud SQL para el piloto**, decidido
   así por los backups, la recuperación a un punto en el tiempo y la región. Se mantienen las cuatro
   alarmas de 06 § 3 y no solo la de caída: un uptime check no ve el QR roto ni la página que no carga.

**Resultado**

- `../analisis/07_disenador_preguntas_y_devolucion.md`: nueva § 3.1 con las tres preguntas, su respuesta
  asumida y el impacto de cada una en el corte; el borrador del mensaje al diseñador (§ 6) cierra ahora con
  estas tres y con los tres supuestos, y se deja constancia de que salieron de mirar el prototipo.
- `../analisis/05_alcance_estimaciones_y_orden.md`: filas nuevas en la tabla de alcance —«Ya estoy en la
  lista de espera» (0,1 d, dentro del corte), OTP (0,5 d, fuera) y zonas o ambientes (1–1,5 d, fuera)— y
  `displayed_ahead` sumado a la estimación de reordenar.
- `../analisis/04_modelo_de_datos.md`: sin cambios de estructura. Se anota que `/lookup` reutiliza el índice
  único de `active_key`, y que `zone` y `displayed_ahead` quedan explícitamente sin escribir.
- `../analisis/03_arquitectura_y_decisiones.md`: nueva § 6.1 con las cinco decisiones difíciles de cambiar
  que van en la nota.
- `../analisis/06_produccion_y_tests.md`: nueva § 0 con la respuesta corta de producción, y Aiven añadido
  a § 1 como base de demo y staging, con sus límites declarados.
- `../entregables/01_nota_tecnica.md`: **nuevo**. La nota técnica escrita, con los seis puntos que pide el
  enunciado. Es el documento que se envía; `analisis/` queda como el material que lo sostiene.
- `../entrega_y_uso_de_ia.md` y `../README.md`: apuntan al entregable escrito, y la tabla de secciones a
  07 § 3.1, 07 § 4.1, 03 § 6.1 y 06 § 0.
- `../analisis/09_alcance_y_plan_de_implementacion.md`: nueva § 2.5 (enmienda posterior al congelamiento),
  O3 reescrito, nuevo O13, endpoint `POST /api/public/locations/{code}/lookup` en § 5.1, séptimo test no
  negociable y renumeración de § 7.2, paso 5 del frontend, definición de listo y punto 10 de deuda conocida.
- `../analisis/08_decisiones_y_preguntas_tecnicas.md`: 4b corregido y nuevos 4d (zonas) y 4e (reordenar).

**Correcciones o rechazos**

La IA propuso que la consulta por teléfono devolviera solo lectura (grupos delante, tiempo y estado) sin el
token ni «Ya no voy», para no tocar O3. Se rechazó: adivinar un móvil completo y válido de alguien que
además está en la cola de ese local hoy no se considera un ataque realista, y media recuperación no resuelve
el caso. El OTP se acepta como propuesta de seguridad posterior, no alcanzable en este corte.

## 2026-09-18 — Entregable 2: estructura inicial ejecutable

**Parte del proyecto:** backend y frontend.

**Prompt o solicitud**

Crear la estructura de carpetas de FastAPI y React, con README breves y actualizables. En esta etapa solo se requiere que ambos proyectos levanten, sin funcionalidades de negocio.

**Decisión**

Mantener `mesa247-api` y `mesa247-web` conforme al plan: FastAPI con `/healthz` y configuración mediante Pydantic Settings; React + TypeScript + Vite + React Router con una página inicial y `app.css`. Preparar carpetas de dominio, rutas, tests, páginas y componentes. Posponer base de datos y flujos de negocio al desarrollo posterior. Configurar el proxy local de Vite hacia el backend y ejemplos de entorno opcionales.

**Resultado**

- Creados los puntos de entrada, configuración y dependencias de ambos proyectos, con versiones directas fijas y `package-lock.json` en la web.
- Añadidos README de raíz, API y web, con arranque en PowerShell y Bash; `.gitignore` excluye entornos, dependencias, builds y datos locales.
- Validado en Windows con Python 3.11.9 y Node.js 24.19.0: instalación de dependencias, `pip check`, `npm ci`, comprobación de tipos y build. Ambos servidores arrancaron; `/healthz`, `/docs`, el HTML y el módulo de entrada de React respondieron por HTTP, y `/healthz` funcionó a través del proxy de Vite.
- Esta validación cubre el arranque inicial; todavía no corresponde al corte funcional completo ni a sus tests de negocio. Los comandos de Bash quedan documentados, sin ejecución en Linux/macOS en esta etapa.

## 2026-09-18 — Backend funcional y base de datos local

**Parte del proyecto:** backend.

**Prompt o solicitud**

Implementar solo backend; revisar contrato de API y estructura documentada ante propuestas nuevas o
cambios del plan. Añadir Docker para la BD, considerando MySQL por Aiven y SQLite por facilidad local.

**Decisión**

- SQLite predeterminado para levantar con Python; MySQL 8.4 alternativo con Compose, volumen y
  healthcheck. Mismos modelos SQLAlchemy y tests; soporte de CA para MySQL remoto. Sin desplegar Aiven.
- Implementar endpoints obligatorios, seed, autenticación por dispositivo y aviso falso. Alta manual,
  on-my-way y frontend quedan fuera de esta implementación de backend.
- Resolver la contradicción call/seat: comparar el estado observado por la petición en el UPDATE.
  Dos acciones que leyeron waiting compiten; si seat lee called después del commit, sentar es válido.
  Evento y estado comparten transacción; aviso y su evento ocurren después.

**Resultado**

- `mesa247-api/`: modelo de cuatro tablas, dominio, rutas, schemas, auth, notificador, seed, Compose,
  pruebas y scripts para exportar OpenAPI y probar MySQL en una base temporal aislada.
- Contrato generado en `../api/openapi.json` y explicado en `../api/README.md`; actualizados alcance 09,
  arquitectura/estructura 03, modelo 04, nota técnica e instrucciones de arranque.
- 46 tests en SQLite y los mismos 46 en MySQL 8.4 local: siete grupos obligatorios, carreras con dos
  conexiones, rollback del evento, fallos del aviso, privacidad, fecha de servicio y rotación del seed.
  `pip check` y validación de Compose correctos. Dos avisos de deprecación de dependencias de TestClient.
- Copia limpia del backend y entorno virtual nuevo en Windows: instalación, seed, arranque Uvicorn y
  flujo HTTP alta → reintento → cola → llamado → consulta → recuperación en 35 s, con caché de pip.
  No es un clon remoto ni una validación de Bash, frontend, Aiven o despliegue.

## 2026-09-18 — Entregable 2: frontend y flujo punta a punta

**Parte del proyecto:** frontend.

**Prompt o solicitud**

Implementar el frontend en React sobre la estructura de carpetas existente, puliéndola donde haga
falta, teniendo presente el diseño del enunciado y las decisiones ya tomadas —entre ellas «Ya estoy
en la lista de espera»—, y dejar el flujo punta a punta funcionando para seguir puliendo con los
fallos o mejoras que aparezcan.

**Decisión**

- Tres pantallas y nada más: `/q/:code`, `/t/:token` y `/host`, con `/` como atajo para abrir un local
  por su código y una pantalla de ruta inexistente. `/host` se carga en su propio chunk.
- `src/` se organiza en `lib/` (cliente de API, tipos del contrato, formatos, almacenamiento),
  `hooks/`, `components/` y `pages/`, en lugar de dejar `api.ts` y `usePolling.ts` sueltos en la raíz.
- Consulta periódica con hook propio: pausa con la pestaña oculta, reanuda al volver o al recuperar la
  red, backoff hasta 60 s, conserva el último dato al caer la conexión y se detiene en estado terminal.
  Un error de negocio (404, 401) no se reintenta.
- El `request_id` se guarda antes del primer envío. Si el guardado apunta a un turno ya cerrado, se
  rota y se reenvía: si no, quien cancela queda atrapado en su propio turno cancelado.
- El 409 del alta abre «Ya estoy en la lista de espera» con el teléfono ya escrito, reutilizando el
  mismo campo y el mismo mensaje de error del alta, según 09 § 2.5 y 07 § 3.1 P3.
- Los 422 de Pydantic se traducen a un mensaje por campo en el cliente; los errores de negocio llegan
  redactados del backend y se muestran tal cual. Nunca se enseña un error técnico.
- Cuando no queda nadie delante se muestra «Eres el siguiente» en vez de un «0» gigante, y el número
  solo se anima al bajar.

**Resultado**

- `mesa247-web/src/`: cliente de API, tipos, formatos, almacenamiento, `usePolling`, tres campos
  compartidos, cinco páginas, rutas y `app.css` completo con modo claro y oscuro. README reescrito.
- Validación en navegador real (Edge headless por CDP) contra la API y el proxy de Vite: alta desde el
  formulario, reintento con el mismo `request_id`, 409 con el mismo teléfono desde otro navegador,
  recuperación por teléfono al mismo turno, teléfono ausente y teléfono inválido; en la tablet, token
  tomado de la URL y limpiado de la barra, Llamar → fila llamada con hora límite y aviso enviado,
  Sentar → sale de la cola, y un solo «WhatsApp simulado» por llamado.
- Corte de red emulado: aparece «sin conexión», se conserva el número y el tiempo, y se recupera sola
  al volver la red. La pausa con pestaña oculta se confirmó como comportamiento, no como fallo.
- `npm run build` y `npm run typecheck` en verde; la tablet queda en un chunk aparte de 4,8 kB.

**Correcciones**

- Dos sesiones trabajaron el mismo repositorio a la vez. Al escribir `app/auth.py` y `app/notifier.py`
  se sobrescribieron las versiones que la sesión de backend acababa de crear. Se reconstruyeron contra
  la interfaz que usan `routers/host.py`, `seed.py` y los tests (`hash_token`, `HostContext`,
  `get_host`, `Notifier`, `get_notifier`, `notify_called`) y la suite volvió a verde, pero esos dos
  archivos son una reconstrucción, no el original. Conviene revisarlos en la lectura final.

**Revisión del frontend (mismo día)**

Cuatro observaciones del autor sobre lo implementado, con su decisión:

1. La pantalla de inicio hablaba de códigos y del seed: lenguaje de back office en una ruta que puede
   abrir un comensal. `/` pasa a ser entrada de producto («escanea el QR») y todo lo operativo se muda
   a `/admin`, documentada en el README. La cola del anfitrión sigue en `/host`, como fija 09 § 2.1.
2. «Ya no voy» se mantiene como está. Se añade una «×» en la pantalla del turno que vuelve a la lista
   del local sin cancelar nada: hacía falta para encadenar registros al probar, y también le sirve a
   quien quiere volver al formulario.
3. «Ya estoy en la lista de espera» deja de ser un panel desplegable y pasa a pantalla propia
   (`/q/{code}/mi-turno`) con retorno al registro. Contradice la letra de 09 § 2.5 —«no es una ruta
   nueva»— y por eso queda recogido en la enmienda § 2.7.
4. El bloqueo por teléfono duraba todo el día de servicio. Pasa a durar lo que dura la espera: un turno
   `called` deja de bloquear al vencer sus 10 minutos, y uno `waiting` al pasar `waiting_ttl_minutes`
   (columna nueva, 120 por defecto). El alta lo caduca (`expired`, evento con
   `reason = "stale_on_rejoin"`) y crea el nuevo. Mientras el turno sigue vivo, el 409 se mantiene y la
   pantalla ofrece dos salidas: volver al turno o registrarse de nuevo cancelando el anterior.

**Resultado de la revisión**

- Backend: `waiting_ttl_minutes` en `locations`, `is_stale`/`release_if_stale` en el dominio, `expire`
  admitido también desde `called` y eventos de transición con datos. Después de la revisión final, la
  caducidad anterior, su evento, el turno reemplazante y `joined` comparten transacción: un fallo conserva
  el turno anterior. Se añadieron pruebas de rollback y dos reemplazos simultáneos.
- Frontend: `HomePage` reescrita, `AdminPage`, `RecoverPage`, `AlreadyInQueueNotice`, `useLocationInfo`
  y la «×» del turno. Validado en navegador: las dos salidas del aviso, el reemplazo real del turno
  anterior y el retorno entre registro y recuperación.
- Documentación: enmienda 09 § 2.7, deudas 11 y 12, contrato de API, README de raíz y de la web.
  El modelo 04 y el DDL MySQL se actualizaron con la columna y con la clasificación de `expired` según
  exista `called_at`. La base MySQL local existente se migró sin borrar datos: sus tres locales quedaron
  con `waiting_ttl_minutes = 120`. Validación final: 51 tests en SQLite y los mismos 51 en MySQL 8.4;
  incluye rollback total ante fallo y carrera de dos reemplazos simultáneos.

**Límite declarado**

«Registrarme de nuevo» son dos llamadas (`lookup` → `cancel` → alta) porque no existe un alta que
reemplace en una transacción. Si la segunda falla, esa persona se queda sin turno. Queda como deuda 11,
no como detalle de implementación.

**Segunda revisión del frontend (mismo día)**

1. Entrar a la lista de espera no es una acción de administración: la hace el comensal al escanear el
   QR, y es justo lo que el piloto tiene que enseñar. El selector de local sale de `/admin` y pasa a
   `/` como atajo de la prueba —«elige un local y entra como si hubieras escaneado su QR»—; `/admin`
   se queda solo con la tablet del anfitrión.
2. El atajo comprueba cada código contra la API: un local cerrado o sin sembrar aparece como «no
   disponible» en lugar de llevar a una pantalla muerta. Es lo único del frontend que asume el
   contenido del seed, y está aislado en `lib/demo.ts` para poder quitarlo de una pieza.
3. Los locales del seed pasan a ser los del enunciado: La Terraza Azul y Cuatro Vientos en Lima, Casa
   Mediterránea en Santiago (antes «El Patio de Lima» y «La Casa de Santiago», que no salían de ningún
   lado). El seed ahora también actualiza nombre, país y zona de un local que ya existe, para que
   renombrar no obligue a borrar la base. Una base sembrada antes conserva la fila `patio-lima`, que
   ya no aparece en ninguna pantalla; borrar `mesa247.db` la deja limpia.
4. Efecto colateral verificado: con el local de Santiago el prefijo del formulario pasa a +56, que es
   el camino que ejercita la normalización por región del local.

51 tests en verde tras renombrar el código del segundo local en los tests de aislamiento.
5. Corrección de la entrada: decía «vuelve a escanear el QR» para recuperar el turno. Es un error de
   producto, no de redacción — el QR está fijo en la puerta y esa frase manda de vuelta al local justo
   a quien el producto promete no hacer volver (07 § 3.1 P3). El atajo pasa a ofrecer las dos puertas
   que abre ese QR, «Unirme a la lista» y «Ya estoy en la lista», y el texto ya no manda a la puerta.
6. Dos fallos encontrados por el autor probando el alta en el navegador, ambos del frontend:
   - Solo se registraba la primera persona. El `request_id` de idempotencia se guardaba en
     `localStorage` por local, así que el segundo alta desde la misma pantalla reenviaba la llave del
     primero; el servidor respondía 200 con el turno ya creado —lo correcto para un reintento— y la
     pantalla llevaba al turno ajeno. La llave identifica un envío, no un dispositivo: pasa a memoria,
     atada a nombre, teléfono y tamaño del grupo, y se descarta al terminar el alta. Sobrevive al
     reintento por mala señal, que es lo único que tenía que sobrevivir.
   - El formulario mostraba `+51` como etiqueta fija y solo dejaba escribir la parte nacional: un
     número extranjero no tenía forma de entrar. El código de país pasa a ser parte del campo, con el
     prefijo del local como valor inicial y editable. El backend no cambia: `normalize_phone` ya
     resolvía cualquier E.164 por encima de la región del local, comprobado con números de ES, US y CL.
7. El campo comprueba en local que haya entre 8 y 15 dígitos antes de enviar, para no gastar una
   petición en un número a medio escribir. La validez real la sigue decidiendo el servidor.
8. Abrir la tablet exigía copiar un token de la consola. Para una demo eso es una barrera y además un
   mal reparto de credenciales: no se le deja un token a quien prueba la aplicación esperando que
   sepa qué hacer con él. `/admin` pasa a listar los locales y abrir la tablet de cualquiera con un
   clic; elegir otro local cambia de tablet, que es lo que faltaba para enseñar dos colas desde un
   mismo equipo. Detrás está `POST /api/demo/locations/{code}/tablet`, que emite la sesión y revoca la
   anterior de ese local sin tocar la que imprime el seed. Es una fábrica de credenciales sin
   autenticación, así que vive detrás de `DEMO_MODE`: encendido por defecto para que un clon limpio
   funcione sin configurar nada (O11), apagado en cualquier despliegue real, donde las rutas responden
   404 y la tablet vuelve a abrirse solo con su enlace. Queda en la enmienda 09 § 2.7 como andamiaje,
   no como el panel de administración ni el emparejamiento de producción, que siguen fuera (§ 2.3).
9. El selector de `/` mostraba un local como «no disponible» y se leyó como un estado del negocio
   —«ese local no ha abierto»— cuando solo significaba que el código no estaba en la base. La lista
   pasa a salir de `GET /api/demo/locations`, con los locales activos que existen de verdad: sin
   códigos fijos en el frontend y sin entradas muertas que interpretar.

## 2026-09-19 — Reporte del día: de fuera del corte a implementado

**Parte del proyecto:** backend y frontend.

**Prompt o solicitud**

El autor señala, sobre el mockup del punto 5 del enunciado, que faltó implementar el reporte del día o
al menos un botón para llegar a él.

**Decisión**

Implementarlo completo. Estaba en § 2.3 («fuera, ni una línea») como exclusión defendida, pero sus
definiciones ya estaban escritas en 04 § 6 con su SQL de referencia y su nota de portabilidad: lo que
faltaba era conectarlas, no decidirlas. El correo del cierre **sigue fuera**, porque depende del cierre
del día automático, que no existe (§ 9 punto 1). La enmienda queda en 09 § 2.8.

Tres decisiones dentro de la pantalla, las tres tomadas de los límites que 04 § 6 pedía declarar antes
de que los pregunten: los conteos son de **grupos** y se publica aparte el total de personas
(`joined_guests`, `seated_guests`); mientras haya turnos sin resolver el día **no ha cerrado**, así que
`pending` se publica y la pantalla avisa de que la suma todavía no cuadra; y el cierre administrativo
(`expired`) va en su propio campo, separado del desenlace que marcó una persona. La agregación se
calcula en Python sobre los turnos del día y no en SQL: `TIMESTAMPDIFF` no existe en SQLite.

**Resultado**

`GET /api/host/report?date=` en `app/routers/host.py`, con `day_report` en `app/domain/queue.py` y el
esquema `HostReport`; `avg_wait_min` pasa a compartir el cálculo del promedio con el reporte. Pantalla
`/host/reporte` con selector de día, más el botón «Reporte del día» en la cola; va en su propio chunk,
como el resto de la operación. Cuatro tests nuevos en `tests/test_report.py`, incluido el invariante
contable que 04 § 6 pedía: 60 tests en verde en SQLite. Documentación actualizada: 09 § 2.3, § 2.8,
§ 5.2, § 5.3 y § 9 punto 12; 03 § 3 (la ruta dejaba de ser «fase 2»); contrato de API y `openapi.json`
regenerado; READMEs de API y web.

**Correcciones o rechazos**

Antes de escribir código se advirtió que el reporte era una exclusión deliberada del corte y se ofreció
dejarlo fuera reforzando dónde se explica. El autor eligió implementarlo completo.

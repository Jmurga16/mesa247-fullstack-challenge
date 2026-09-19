# Pruebas funcionales integradas — 19/09/2026

**Resultado: validación funcional completa aprobada.**
La primera ejecución dejó doce escenarios aprobados y cinco fallidos, todos de recuperación, sesión
e idempotencia en el frontend. Se corrigieron los cinco. Después, la prueba manual del autor destapó
un sexto fallo en el campo del teléfono que ninguno de los 17 escenarios podía ver, y la batería creció
a 19: pasa entera. El contrato de API, el modelo de datos y el alcance funcional no cambian.

## Entorno y resultados

Windows, Python 3.11.9, Node.js 24.19.0, Chromium 153 con Playwright 1.63.0.
Frontend Vite y backend FastAPI reales, con SQLite temporal y puertos asignados para cada ejecución.
Vistas de comensal de 390 × 844 y tablet de 1024 × 768, zona America/Lima.
Se conservaron los servidores, datos y sesiones de desarrollo que ya estaban activos.

| Validación | Primera ejecución | Tras la corrección |
|---|---|---|
| Backend: `python -m pytest -q`, SQLite temporal | 60 aprobados, 8,48 s | 60 aprobados, 5,56 s |
| Backend: `python scripts/test_mysql.py`, MySQL 8.4 local | 60 aprobados, 13,29 s | 60 aprobados, 8,47 s |
| Frontend: `npm run build` (TypeScript y Vite) | Aprobado | Aprobado |
| Navegador con front y back integrados | 12 aprobados, 5 fallidos | 19 aprobados, 189,96 s |
| Instalación en copia limpia y ambos servidores disponibles | 66,03 s | no se repitió |
| Copia limpia, incluyendo alta → tablet → llamado → celular → asiento y fin del polling | 109,83 s | no se repitió |

La copia limpia usó archivos versionados, un virtualenv nuevo y `node_modules` nuevo; se ejecutaron
las instalaciones de los READMEs y el build. Los puertos y la base se aislaron para convivir con los
servidores abiertos. Había cachés de pip/npm y Chromium instalado: el tiempo no representa una descarga
sin caché ni la descarga del repositorio. No se verificó Bash. Los dos tiempos de copia limpia son los
de la primera ejecución: la corrección no toca las dependencias ni los pasos de instalación, y el
`build`, que sí los usa, volvió a pasar.

Ambas suites del backend emiten dos avisos de deprecación de Starlette/httpx y AnyIO, sin fallos.
La suite de MySQL crea y elimina su propia base temporal.

## Escenarios de navegador

Los números corresponden a los métodos de [functional.py](../../mesa247-web/tests/functional.py).
La última columna deja ver qué caso destapó cada fallo.

| Caso | Comprobación | Resultado | Primera ejecución |
|---|---|---|---|
| 01 | Selector de tres locales, alta, fila por polling, llamar, aviso simulado, llamado y límite en el celular, sentar y detener polling terminal | Aprobado | Aprobado |
| 02 | Dos altas distintas desde el mismo navegador reciben turnos distintos y posición correcta | Aprobado | Aprobado |
| 03 | Mismo teléfono desde otro contexto: 409 sin token; «Ver mi turno» y recuperación por teléfono abren el turno original | Aprobado | Aprobado |
| 04 | Nombre vacío, teléfono incompleto y límites de 1 a 20 personas | Aprobado | Aprobado |
| 05 | Local de Santiago con prefijo +56 y número extranjero +34 en Lima | Aprobado | Aprobado |
| 06 | Desistir de cancelar, confirmar cancelación, lookup de turno cerrado y alta nueva con el mismo teléfono | Aprobado | Aprobado |
| 07 | Registrarse de nuevo advierte la pérdida de posición, cancela el anterior y crea otro turno | Aprobado | Aprobado |
| 08 | Se fue, No vino, Borrar con confirmación; conteos del reporte frente a API, pendientes, día pasado y vuelta a hoy | Aprobado | Aprobado |
| 09 | Cola aislada por local, acción cruzada 404, sesión inválida, limpieza de token de URL, turno y local inexistentes | Aprobado | Aprobado |
| 10 | Alta confirmada por API cuya respuesta se pierde: reintentar sin recargar conserva request_id y crea un solo turno | Aprobado | Aprobado |
| 11 | El mismo reintento después de recargar conserva request_id y recupera automáticamente el turno | Aprobado | Fallido, F03 |
| 12 | Sesión revocada mientras el reporte está abierto muestra la pantalla de sesión inválida | Aprobado | Fallido, F01 |
| 13 | La cuenta regresiva sigue avanzando aunque no lleguen respuestas nuevas | Aprobado | Fallido, F04 |
| 14 | Cortar la red del navegador conserva el dato, avisa y se recupera al reconectar | Aprobado | Aprobado |
| 15 | Detener realmente la API 30 s conserva el dato, avisa y recupera el polling tras reiniciar | Aprobado | Fallido, F02 |
| 16 | Fallo de red en la primera consulta del turno informa de desconexión | Aprobado | Fallido, F05 |
| 17 | Dos tablets llaman la misma fila antes de refrescar: un evento called y un notification_sent | Aprobado | Aprobado |
| 18 | El teléfono **tecleado**, no rellenado de golpe: el número entero sobre el prefijo no duplica el país, y el código repetido a mano se nombra | Aprobado | no existía |
| 19 | El conmutador de la demo cambia de comensal a anfitrión y al revés, sin desbordar la tablet | Aprobado | no existía |

Las capturas del llamado y del reporte se revisaron; las vistas comprobadas no tienen desbordamiento
horizontal. El doble llamado del caso 17 prueba dos interfaces con una fila antigua; las carreras
simultáneas entre dos conexiones se verifican en la suite del backend.

Ningún escenario se relajó para que pasara: las expectativas son las mismas que tenían cuando fallaban.
Los casos 18 y 19 se añadieron después, con los hallazgos de la prueba manual.

## Fallos corregidos

Los cinco eran de frontend. No se tocó el backend, el contrato ni los datos.

### F01 · Alta · El reporte quedaba en blanco al invalidarse la sesión

1. Abrir una tablet desde `/admin` y entrar en «Reporte del día».
2. Abrir otra tablet demo del mismo local desde otro navegador: eso revoca la sesión demo anterior.
3. Actualizar el primer reporte o esperar su consulta periódica.

**Esperado:** aviso «Esta tablet no tiene sesión» y enlace para volver a abrirla.
**Observado:** pantalla en blanco; React lanzaba `Rendered fewer hooks than expected`.

En [ReportPage.tsx](../../mesa247-web/src/pages/ReportPage.tsx) el retorno por 401 precedía al
`useEffect` que guarda el día, así que pasar de sesión válida a inválida cambiaba el número de hooks
ejecutados.

**Corrección:** ese efecto se movió delante del retorno condicional, con un comentario que explica por
qué el orden importa. La pantalla de sesión inválida es la misma que ya usaba la cola.

### F02 · Alta · Una caída del backend detenía las actualizaciones

1. Mantener abiertos un turno y la tablet con datos cargados.
2. Detener el proceso de API durante 30 segundos, conservando Vite.
3. Reiniciar la API sin recargar ni cambiar de pestaña.

**Esperado:** último dato más aviso de desconexión; consultas que se recuperan solas.
**Observado:** el proxy devolvía HTTP 500; el comensal conservaba una pantalla desactualizada sin
aviso de desconexión y dejaba de consultar. La tablet mostraba un error genérico. Al reiniciar la API,
el polling no se recuperaba.

[api.ts](../../mesa247-web/src/lib/api.ts) convierte ese HTTP 500 en `ApiError`, y
[usePolling.ts](../../mesa247-web/src/hooks/usePolling.ts) detenía el ciclo ante **cualquier**
`ApiError`, aunque el comentario solo mencionaba 401/404. El caso 14 sí pasaba porque desconectar la
red del navegador produce un error de transporte y sigue otra rama: probar solo el modo offline no
bastaba.

**Corrección:** el hook distingue la respuesta del corte. Un 5xx, un 408 o un 429 se tratan como falta
de conexión —se conserva el último dato, se avisa y se reintenta con backoff hasta 60 s—; solo las
respuestas que no cambian por insistir, como 401 y 404, detienen el ciclo. La pantalla del turno,
además, ya muestra `polling.error` cuando el dato está cargado, en lugar de callarlo.

La primera comprobación observó 17 segundos tras el reinicio; la prueba se amplió a 65 segundos para
superar el máximo de backoff documentado, y con esa espera el caso 15 pasa: el polling vuelve solo.

### F03 · Media · El reintento no sobrevivía a la recarga

1. Enviar un alta y descartar la respuesta después de que la API haya creado el turno.
2. Recargar el formulario, introducir los mismos datos y enviar de nuevo.

**Esperado según 09 § 8.6:** el mismo identificador de envío y el mismo turno.
**Observado:** cambiaba el `request_id`, la API devolvía 409 y aparecía «Ya estás en la lista». No se
duplicaba el turno ni se perdía —«Ver mi turno» lo recuperaba—, pero el reintento no era automático y
el README prometía otra cosa.

[JoinPage.tsx](../../mesa247-web/src/pages/JoinPage.tsx) conservaba el identificador solo en `useRef`.
Guardarlo por local había sido un error anterior: el segundo comensal de la misma pantalla reenviaba la
llave del primero y recibía el turno ajeno.

**Corrección:** se persiste únicamente el **envío pendiente**, no una llave por dispositivo. En
`localStorage` queda `{key, id, at}`, donde `key` es la huella de los datos del formulario —nombre,
teléfono y tamaño del grupo—. Al enviar, la llave se reutiliza solo si la huella coincide; si no, se
genera otra. Se borra al abrir el turno y caduca a los 30 minutos, porque pasado ese rato ya no es un
reintento sino un alta nueva. El comportamiento defectuoso no vuelve: dos comensales distintos tienen
huellas distintas, y el caso 02 lo comprueba.

### F04 · Media · La cuenta regresiva se congelaba sin respuestas nuevas

1. Llamar al comensal y comprobar «Quedan 10 min».
2. Interrumpir las respuestas y adelantar 61 segundos el reloj del navegador.

**Esperado:** «Quedan 9 min» manteniendo el desfase respecto al servidor.
**Observado:** seguía diciendo «Quedan 10 min».

[TicketPage.tsx](../../mesa247-web/src/pages/TicketPage.tsx) recalculaba `clockSkewMs` en cada render:
en [format.ts](../../mesa247-web/src/lib/format.ts), sumar ese desfase a `Date.now()` devolvía otra vez
el `server_now` de la última respuesta, así que el contador solo avanzaba al recibir un dato nuevo.

**Corrección:** el desfase se mide **al recibir** el dato y se conserva mientras `server_now` no cambie.
El intervalo de un segundo ya mueve la cuenta y la referencia sigue siendo la hora del servidor, no la
del celular. La regla quedó escrita en el comentario de `clockSkewMs`, que además estaba colocado sobre
la función equivocada.

### F05 · Media · El primer fallo de red quedaba oculto tras el indicador de carga

1. Abrir el enlace de un turno existente.
2. Hacer fallar su primera consulta HTTP, dejando que cargue el frontend.

**Esperado:** informar de que no hay conexión mientras se reintenta.
**Observado:** solo «Cargando tu turno…»; ningún aviso de red.

El hook registraba `offline`, pero el retorno `if (!ticket)` de `TicketPage.tsx` ocurría antes de
renderizar `ConnectionBanner`.

**Corrección:** esa pantalla de carga también muestra el aviso, de modo que el estado de desconexión
está disponible desde la primera consulta y no solo cuando ya hay dato.

## Prueba manual del autor

Con los 17 escenarios en verde, el autor usó la aplicación a mano y encontró dos cosas que la batería
no miraba.

### F06 · Alta · El número entero escrito sobre el prefijo duplicaba el código de país

El campo del teléfono llega con el prefijo del local (`+51 `, con un espacio). Quien lee la pista
—«con el código de país»— teclea su número **completo** encima. El saneado del campo borraba ese
segundo `+` pero conservaba sus dígitos, así que quedaba `+51 51987654322`: un número corrompido en
silencio, rechazado por el servidor con el mensaje genérico de teléfono inválido. Se vive como «la
aplicación no me deja pasar mi número».

**Corrección**, en [phone.ts](../../mesa247-web/src/lib/phone.ts): un `+` escrito después del principio
**empieza un número nuevo**, que es lo que significa teclear el tuyo entero sobre el prefijo. Además el
prefijo ya no llega con el espacio detrás, que era un carácter invisible que no aportaba nada.

Queda un caso que no se puede adivinar: escribir `51987654325` —el código repetido, pero sin `+`—
sobre el prefijo. Colapsarlo corrompería un fijo legítimo de otra zona, así que no se toca; lo que
cambia es el aviso, que ahora dice «El código de país +51 está dos veces» en vez del mensaje general.
Ese mensaje solo sustituye a uno que el servidor ya había rechazado, así que no bloquea a nadie.

**Por qué la batería no lo vio:** los 17 escenarios rellenaban el campo con `fill()`, que escribe el
valor de una vez y nunca ejerce el saneado. El caso 18 **teclea**.

### Conmutador de papel para probar las dos mitades

No es un fallo: probar comensal y anfitrión obligaba a escribir rutas a mano. Se añadió un conmutador
«Comensal / Anfitrión» fijo en la parte superior, detrás de `DEMO_MODE` como el resto del andamiaje
(09 § 2.7). Primero se colocó abajo a la derecha, donde pasaba desapercibido, y se subió tras probarlo.
El caso 19 lo cubre, incluida la comprobación de que no desborda la tablet.

## Reproducción y evidencia

Comandos y funcionamiento del runner: [tests/README.md](../../mesa247-web/tests/README.md).
La batería termina con código 0 cuando los 19 escenarios pasan.

Evidencia local generada, excluida de Git:

- `.artifacts/functional/results.json`: resultados de los 19 escenarios.
- `.artifacts/functional/*.png`: capturas de flujos y, de la primera ejecución, de los cinco fallos;
  `api.log` y `vite.log` contienen logs de prueba.
- `.artifacts/clean-start/results.json`: tiempos y resultado de la instalación limpia.
- `.artifacts/outage-confirmation/results.json`: comprobación ampliada tras reiniciar la API, hecha al
  diagnosticar F02 y hoy cubierta por el caso 15.

Los tests de navegador usan SQLite; MySQL se probó con la suite de API, no con la interfaz.
No se validaron dispositivos físicos, Safari/Firefox, red móvil real, despliegue remoto ni envío real
de WhatsApp/SMS. La pausa al ocultar una pestaña no tiene una comprobación dedicada en esta batería.

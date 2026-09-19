# Pruebas funcionales integradas — 19/09/2026

**Resultado: el flujo principal funciona, pero la validación funcional completa no está aprobada.**
La suite del backend y el build pasan; el navegador reproduce cinco problemas de recuperación,
sesión e idempotencia. Esta tarea añade pruebas y documenta resultados; no modifica el código del producto.

## Entorno y resultados

Windows, Python 3.11.9, Node.js 24.19.0, Chromium 153 con Playwright 1.63.0.
Frontend Vite y backend FastAPI reales, con SQLite temporal y puertos asignados para cada ejecución.
Vistas de comensal de 390 × 844 y tablet de 1024 × 768, zona America/Lima.
Se conservaron los servidores, datos y sesiones de desarrollo que ya estaban activos.

| Validación | Resultado |
|---|---|
| Backend: `python -m pytest -q`, SQLite temporal | 60 aprobados, 8,48 s |
| Backend: `python scripts/test_mysql.py`, MySQL 8.4 local | 60 aprobados, 13,29 s |
| Frontend: `npm run build` (TypeScript y Vite) | Aprobado |
| Navegador con front y back integrados | 12 escenarios aprobados, 5 fallidos |
| Instalación en copia limpia y ambos servidores disponibles | 66,03 s |
| Copia limpia, incluyendo alta → tablet → llamado → celular → asiento y fin del polling | 109,83 s |

La copia limpia usó archivos versionados, un virtualenv nuevo y `node_modules` nuevo; se ejecutaron
las instalaciones de los READMEs y el build. Los puertos y la base se aislaron para convivir con los
servidores abiertos. Había cachés de pip/npm y Chromium instalado: el tiempo no representa una descarga
sin caché ni la descarga del repositorio. No se verificó Bash.

Ambas suites del backend emiten dos avisos de deprecación de Starlette/httpx y AnyIO, sin fallos.
La suite de MySQL crea y elimina su propia base temporal.

## Escenarios de navegador

Los números corresponden a los métodos de [functional.py](../../mesa247-web/tests/functional.py).

| Caso | Comprobación | Resultado |
|---|---|---|
| 01 | Selector de tres locales, alta, fila por polling, llamar, aviso simulado, llamado y límite en el celular, sentar y detener polling terminal | Aprobado |
| 02 | Dos altas distintas desde el mismo navegador reciben turnos distintos y posición correcta | Aprobado |
| 03 | Mismo teléfono desde otro contexto: 409 sin token; «Ver mi turno» y recuperación por teléfono abren el turno original | Aprobado |
| 04 | Nombre vacío, teléfono incompleto y límites de 1 a 20 personas | Aprobado |
| 05 | Local de Santiago con prefijo +56 y número extranjero +34 en Lima | Aprobado |
| 06 | Desistir de cancelar, confirmar cancelación, lookup de turno cerrado y alta nueva con el mismo teléfono | Aprobado |
| 07 | Registrarse de nuevo advierte la pérdida de posición, cancela el anterior y crea otro turno | Aprobado |
| 08 | Se fue, No vino, Borrar con confirmación; conteos del reporte frente a API, pendientes, día pasado y vuelta a hoy | Aprobado |
| 09 | Cola aislada por local, acción cruzada 404, sesión inválida, limpieza de token de URL, turno y local inexistentes | Aprobado |
| 10 | Alta confirmada por API cuya respuesta se pierde: reintentar sin recargar conserva request_id y crea un solo turno | Aprobado |
| 11 | El mismo reintento después de recargar conserva request_id y recupera automáticamente el turno | Fallido, F03 |
| 12 | Sesión revocada mientras el reporte está abierto muestra la pantalla de sesión inválida | Fallido, F01 |
| 13 | La cuenta regresiva sigue avanzando aunque no lleguen respuestas nuevas | Fallido, F04 |
| 14 | Cortar la red del navegador conserva el dato, avisa y se recupera al reconectar | Aprobado |
| 15 | Detener realmente la API 30 s conserva el dato, avisa y recupera el polling tras reiniciar | Fallido, F02 |
| 16 | Fallo de red en la primera consulta del turno informa de desconexión | Fallido, F05 |
| 17 | Dos tablets llaman la misma fila antes de refrescar: un evento called y un notification_sent | Aprobado |

Las capturas del llamado y del reporte se revisaron; las vistas comprobadas no tienen desbordamiento
horizontal. El doble llamado del caso 17 prueba dos interfaces con una fila antigua; las carreras
simultáneas entre dos conexiones se verifican en la suite del backend.

## Fallos abiertos

### F01 · Alta · El reporte queda en blanco al invalidarse la sesión

1. Abrir una tablet desde `/admin` y entrar en «Reporte del día».
2. Abrir otra tablet demo del mismo local desde otro navegador: eso revoca la sesión demo anterior.
3. Actualizar el primer reporte o esperar su consulta periódica.

**Esperado:** aviso «Esta tablet no tiene sesión» y enlace para volver a abrirla.
**Observado:** pantalla en blanco; React lanza `Rendered fewer hooks than expected`.

En [ReportPage.tsx](../../mesa247-web/src/pages/ReportPage.tsx), el retorno por 401 precede al
`useEffect` que guarda el día. Pasar de sesión válida a inválida cambia el número de hooks ejecutados.
La corrección debe mantener los hooks antes de cualquier retorno condicional.

### F02 · Alta · Una caída del backend detiene las actualizaciones

1. Mantener abiertos un turno y la tablet con datos cargados.
2. Detener el proceso de API durante 30 segundos, conservando Vite.
3. Reiniciar la API sin recargar ni cambiar de pestaña.

**Esperado:** último dato más aviso de desconexión; consultas que se recuperan solas.
**Observado:** el proxy devuelve HTTP 500; el comensal conserva una pantalla desactualizada sin
aviso de desconexión y deja de consultar. La tablet muestra un error genérico. Al reiniciar la API,
el polling no se recupera automáticamente.

[api.ts](../../mesa247-web/src/lib/api.ts) convierte ese HTTP 500 en `ApiError`;
[usePolling.ts](../../mesa247-web/src/hooks/usePolling.ts) detiene el ciclo ante **cualquier**
`ApiError`, aunque el comentario solo menciona 401/404. Además, la pantalla del turno con datos ya
cargados no muestra `polling.error`. El caso 14 sí pasa: desconectar la red del navegador provoca un
error de transporte y sigue una rama diferente. No basta con probar únicamente el modo offline.

La primera comprobación observó 17 segundos tras el reinicio; se amplió la prueba a 65 segundos
para superar el máximo de backoff de 60 segundos documentado. Deben reintentarse los fallos transitorios
de servicio y mostrarse su estado conservando el dato anterior.

### F03 · Media · El reintento no sobrevive a la recarga

1. Enviar un alta y descartar la respuesta después de que la API haya creado el turno.
2. Recargar el formulario, introducir los mismos datos y enviar de nuevo.

**Esperado según 09 § 8.6:** el mismo identificador de envío y el mismo turno.
**Observado:** cambia `request_id`; la API devuelve 409 y aparece «Ya estás en la lista».
No se duplica el turno ni se pierde: «Ver mi turno» permite recuperarlo. El fallo está en la
continuidad automática del reintento y en la discrepancia con lo que promete el README.

[JoinPage.tsx](../../mesa247-web/src/pages/JoinPage.tsx) conserva el identificador exclusivamente en
`useRef`. El registro del frontend explica que se eligió memoria para corregir el reuso de una llave
entre comensales; no debe restaurarse ese comportamiento defectuoso. Si se mantiene el requisito de
recarga, persistir solo el envío pendiente, asociado a sus datos, y descartarlo al completar el alta.

### F04 · Media · La cuenta regresiva se congela sin respuestas nuevas

1. Llamar al comensal y comprobar «Quedan 10 min».
2. Interrumpir las respuestas y adelantar 61 segundos el reloj del navegador.

**Esperado:** «Quedan 9 min» manteniendo el desfase respecto al servidor.
**Observado:** sigue diciendo «Quedan 10 min».

[TicketPage.tsx](../../mesa247-web/src/pages/TicketPage.tsx) recalcula `clockSkewMs` en cada render.
En [format.ts](../../mesa247-web/src/lib/format.ts), sumar ese desfase a `Date.now()` vuelve a dar el
`server_now` de la última respuesta. El contador depende de recibir un nuevo dato y el intervalo de
un segundo no lo hace avanzar por sí solo. Debe conservarse la referencia temporal al recibir el dato.

### F05 · Media · El primer fallo de red queda oculto tras el indicador de carga

1. Abrir el enlace de un turno existente.
2. Hacer fallar su primera consulta HTTP, dejando que cargue el frontend.

**Esperado:** informar de que no hay conexión mientras se reintenta.
**Observado:** solo «Cargando tu turno…»; no hay aviso de red.

El hook registra `offline`, pero el retorno `if (!ticket)` en
[TicketPage.tsx](../../mesa247-web/src/pages/TicketPage.tsx) ocurre antes de renderizar
`ConnectionBanner`. El estado de desconexión debe estar disponible también durante la primera carga.

## Reproducción y evidencia

Comandos y funcionamiento del runner: [tests/README.md](../../mesa247-web/tests/README.md).
Los cinco casos fallidos conservan las expectativas correctas y hacen que el runner termine con
código 1; no se han ocultado como fallos esperados.

Evidencia local generada, excluida de Git:

- `.artifacts/functional/results.json`: resultados de los 17 escenarios.
- `.artifacts/functional/*.png`: capturas de flujos y fallos; `api.log` y `vite.log` contienen logs de prueba.
- `.artifacts/clean-start/results.json`: tiempos y resultado de la instalación limpia.
- `.artifacts/outage-confirmation/results.json`: comprobación ampliada tras reiniciar la API.

Los tests de navegador usan SQLite; MySQL se probó con la suite de API, no con la interfaz.
No se validaron dispositivos físicos, Safari/Firefox, red móvil real, despliegue remoto ni envío real
de WhatsApp/SMS. La pausa al ocultar una pestaña no tiene una comprobación dedicada en esta batería.
El contrato y el alcance funcional no se modifican por esta ejecución.

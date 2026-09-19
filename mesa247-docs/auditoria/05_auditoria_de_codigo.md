# Auditoría de código y funcionalidad — 19/09/2026

**Resultado: el código implementado coincide con el contrato y con el alcance congelado.**
No apareció ningún fallo funcional nuevo. Sí apareció un defecto menor de interfaz, ya corregido,
código muerto, comentarios en dos idiomas y una salida de consola desactualizada. La limpieza no
cambia el comportamiento: las tres baterías siguen en verde.

Esta revisión es de implementación. La del análisis previo está en
[01](01_informe_de_auditoria.md) y [02](02_resolucion_de_hallazgos.md); las pruebas de navegador,
en [04](04_pruebas_funcionales_integradas.md).

## Qué se revisó

Todo el código de producto, leído entero: `mesa247-api/app/` con `seed.py` (unas 800 líneas) y
`mesa247-web/src/` (unas 2.100, sin contar `app.css`). Tres contrastes:

1. **Rutas implementadas contra el contrato** de [api/README.md](../api/README.md) y 09 § 5.
2. **Reglas de negocio contra 09 § 2.7** (transiciones, caducidad, llave activa, reporte).
3. **Código contra sí mismo**: símbolos sin uso, duplicación, comentarios obsoletos o que repiten
   lo que ya dice la línea de al lado.

Las rutas coinciden una a una con el contrato, incluidos los dos opcionales que el documento declara
no implementados (`POST /api/host/tickets` y `/on-my-way`). No hay endpoints sin documentar ni
documentados sin existir.

## Lo que se corrigió

| Dónde | Qué | Por qué |
|---|---|---|
| [usePolling.ts](../../mesa247-web/src/hooks/usePolling.ts) | El aviso «sin conexión» no se borraba al cambiar de turno, de local o de día | Es el único defecto de comportamiento encontrado: el ciclo reinicia `data`, `error` y `loading`, pero no `offline`, así que el aviso sobrevivía hasta la siguiente respuesta buena |
| [api.ts](../../mesa247-web/src/lib/api.ts) | Fuera la opción `onStatus` | Declarada, desestructurada e invocada; ninguna llamada la usaba |
| [seed.py](../../mesa247-api/seed.py) | «QR (frontend pendiente)» → «QR» | El frontend existe; era lo primero que leía quien levantaba el proyecto |
| [auth.py](../../mesa247-api/app/auth.py), [queue.py](../../mesa247-api/app/domain/queue.py) | Cuatro comentarios traducidos al español | El resto del código de producto está en español; eran los únicos en inglés |
| [main.py](../../mesa247-api/app/main.py) | Un `logger` de módulo en vez de tres `getLogger` y traza completa en el fallo inesperado | El 500 se registraba solo con el nombre de la excepción: en el log no quedaba dónde se había roto. La respuesta al cliente no cambia |

### Duplicación retirada

Dos bloques de JSX estaban copiados entre la cola y el reporte, y uno de ellos contiene el texto que
las pruebas usan para reconocer la pantalla:

- [NoHostSession.tsx](../../mesa247-web/src/components/NoHostSession.tsx): la salida «Esta tablet no
  tiene sesión». Cada pantalla conserva su propio texto explicativo, que es distinto a propósito, y
  solo la cola ofrece descartar el token guardado.
- [ErrorBanner.tsx](../../mesa247-web/src/components/ErrorBanner.tsx): el aviso de error del servidor
  con su «Reintentar», que ahora comparten la cola, el reporte y la pantalla del turno. El turno lo
  usa sin botón, porque ahí el ciclo se reintenta solo.

Son 30 líneas menos y, sobre todo, un solo sitio donde cambia el texto de la sesión caducada.

## Lo que se dejó como está

- **Los comentarios largos se quedan.** El código explica decisiones, no mecánica: por qué el
  `request_id` vive atado a los datos del formulario, por qué la caducidad mira la hora y no la
  fecha, por qué el reporte se calcula en Python. Eso no es ruido; quitarlo empobrece el entregable.
  Lo que se retiró fue lo que había dejado de ser cierto.
- **El campo `on_the_way`** sigue publicado en el contrato, en el modelo y como distintivo en la
  tablet, aunque hoy no pueda activarse nadie: quitarlo obligaría a cambiar el contrato y la tabla
  para volver a ponerlos con el opcional 2. Queda anotado como deuda (09 § 9 punto 13).
- **`mismo origen` sin CORS.** Hoy lo garantiza el proxy de Vite; en el piloto lo garantizará FastAPI
  sirviendo el build (03 § 2), que está fuera del corte. No hay nada que arreglar todavía.
- **El cambio de ritmo del polling** (15 s → 10 s cerca del turno) reinicia el ciclo y gasta una
  consulta de más. Es una consulta por comensal y por turno: no justifica complicar el hook.
- **`/` no distingue la API caída del modo demo apagado**, y dice siempre «Levanta la API». La tablet
  sí lo distingue. Afecta solo a los atajos de la demo, que no son producto.

## Deuda técnica detectada

Tres puntos nuevos, añadidos a la lista de 09 § 9 para que vivan donde vive el resto:

- **13 · `on_the_way` no lo activa nadie.** El contrato lo publica siempre en `false`.
- **14 · Una consulta por fila para el estado del aviso.** `host_row` pregunta por los eventos de
  notificación fila a fila. Con una cola de puerta son decenas de consultas cortas; con un local
  grande y un día entero, ya no.
- **15 · Ningún linter ni formateador.** No hay `ruff` ni `eslint` configurados, así que la
  consistencia depende de la revisión a mano — que es justo lo que encontró los comentarios en dos
  idiomas y el código muerto.

Lo demás de la lista de 09 § 9 sigue vigente y esta revisión no lo cambia.

## Verificación

Después de la limpieza, sin relajar ninguna prueba:

| Validación | Resultado |
|---|---|
| Backend `python -m pytest -q`, SQLite temporal | 60 aprobados, 8,87 s |
| Frontend `npm run build` (TypeScript estricto y Vite) | Aprobado |
| Navegador, los 17 escenarios integrados | 17 aprobados, 191,28 s |

`noUnusedLocals` y `noUnusedParameters` están activos en `tsconfig.json`, así que el build habría
fallado si la extracción de componentes hubiera dejado un import huérfano.

## Límites de esta revisión

Se leyó el código de producto, no `app.css` línea a línea ni las suites de prueba como código. No se
midió rendimiento ni se perfiló ninguna consulta: el punto 14 sale de leer el SQL que se emite, no de
una medición. No se revisó la accesibilidad más allá de lo que ya comprueban las pruebas de navegador,
ni se auditaron las dependencias (no hay `npm audit` ni equivalente en esta pasada).

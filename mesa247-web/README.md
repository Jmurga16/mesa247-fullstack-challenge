# Mesa247 Web

Frontend con React, TypeScript, Vite y React Router. Cubre las tres pantallas del corte —unirse desde el QR, la página del turno y la cola del anfitrión— más el reporte del día de la tablet. Sin librería de datos ni de estilos: un hook propio de consulta periódica y un único `app.css`.

## Arranque

Requiere **Node.js 22.12+** y npm. El backend debe estar levantado (ver [README de la API](../mesa247-api/README.md)); Vite reenvía `/api` y `/healthz` a `http://127.0.0.1:8000`.

### PowerShell

```powershell
cd mesa247-web
npm.cmd ci
npm.cmd run dev
```

### Bash (Linux / macOS)

```bash
cd mesa247-web
npm ci
npm run dev
```

Abre <http://127.0.0.1:5173>. Con el modo demo encendido (`DEMO_MODE=true`, el valor por defecto de la API) no hace falta copiar nada: `/` ofrece los locales para entrar como comensal y `/admin` abre la tablet de cualquiera con un clic. Los enlaces reales —el del QR y el de la tablet, con su token— los sigue imprimiendo el seed del backend (`python seed.py`).

## Rutas

| Ruta | Quién la usa | Qué hace |
|---|---|---|
| `/` | comensal | entrada del producto, más el atajo de la prueba: elegir local y entrar a unirse o a recuperar el turno |
| `/q/:code` | comensal | alta con nombre, teléfono y tamaño de grupo |
| `/q/:code/mi-turno` | comensal | «Ya estoy en la lista de espera»: vuelve a su turno con el teléfono |
| `/t/:token` | comensal | su turno: grupos delante, tiempo aproximado, llamado con hora límite y «Ya no voy» |
| `/admin` | operación | entrar a la tablet del anfitrión, y cambiar de local sin tocar tokens |
| `/host` | anfitrión | la cola del local: Llamar, Sentar, No vino, Se fue y Borrar |
| `/host/reporte` | anfitrión/gerente | el reporte del día del local, con selector de día |

`/` no habla de tokens ni del seed: la puede abrir un comensal. Lleva un **selector con los tres locales del piloto** que sustituye a la cámara y al papel pegado en la puerta, con **las dos puertas que abre ese QR**: unirse a la lista o volver al turno con el teléfono. Nunca dice «vuelve a escanear»: quien ya está esperando no tiene por qué volver a la puerta del local, que es el problema que el producto resuelve. Los locales los da la API (`GET /api/demo/locations`, solo los activos), así que el selector nunca ofrece una puerta muerta. Los atajos viven en [`src/lib/demo.ts`](src/lib/demo.ts), para poder borrarlos de una pieza.

**`/admin` es solo la tablet.** Abrir la lista de un local no es una acción de administración: la hace el comensal al escanear. Lo que sí hace `/admin` es abrir la tablet de un local con un clic (`POST /api/demo/locations/{code}/tablet`), porque quien prueba la aplicación no tiene por qué manejar credenciales; elegir otro local cambia de tablet, que es como se enseñan dos colas desde un mismo equipo. Esas rutas son andamiaje: con `DEMO_MODE=false` responden 404, `/admin` lo dice en pantalla y la tablet vuelve a abrirse solo con su enlace `/host?token=…`.

`/host` lee el token de `?token=`, lo guarda en la tablet y lo borra de la barra de direcciones. `/host/reporte` usa esa misma sesión y se abre desde el botón «Reporte del día» de la cola. `/admin`, `/host` y `/host/reporte` van en chunks aparte: nadie los carga desde el celular.

## Estructura

```text
src/
├── main.tsx        Entrada de React y BrowserRouter
├── App.tsx         Rutas; /admin y /host se cargan aparte
├── app.css         Estilos compartidos, claro y oscuro
├── lib/
│   ├── api.ts      Cliente tipado y traducción de errores al español
│   ├── types.ts    El contrato de la API, en tipos
│   ├── demo.ts     Los locales del piloto para el atajo de `/` (solo prueba)
│   ├── format.ts   Horas, esperas y textos de posición
│   └── storage.ts  localStorage tolerante a fallos y uuid del request_id
├── hooks/
│   ├── usePolling.ts      Consulta periódica: pausa, reintento y backoff
│   └── useLocationInfo.ts Datos públicos del local, compartidos por dos pantallas
├── components/     Campos y avisos compartidos entre pantallas
└── pages/          Una pantalla por archivo
```

## Decisiones que se ven en el código

- **El reintento no duplica el turno.** `JoinPage` genera un `request_id` y lo guarda en `localStorage` antes del primer envío: reenviar el formulario devuelve el mismo turno. Si ese identificador quedó apuntando a un turno ya cerrado, se rota y se vuelve a enviar.
- **Perder el link tiene salida.** «Ya estoy en la lista de espera» es una pantalla propia que pide el teléfono y devuelve el turno activo ([09 § 2.5 y § 2.7](../mesa247-docs/analisis/09_alcance_y_plan_de_implementacion.md)).
- **Volver a registrarse no es un callejón sin salida.** Si el teléfono ya está esperando, el alta muestra dos salidas: volver al turno que ya existe, o empezar uno nuevo — avisando antes de confirmar que el nuevo cancela el anterior y deja al final de la cola. Son dos llamadas (`lookup` → `cancel` → alta), no una transacción: está anotado en 09 § 9.
- **Un turno vencido no bloquea el teléfono.** Pasados los 10 minutos del llamado, volver a anotarse crea un turno nuevo sin pedir permiso a nadie; la regla vive en el backend (09 § 2.7).
- **Sin conexión no es un error en pantalla.** `usePolling` conserva el último dato, muestra «sin conexión» y reintenta con backoff hasta 60 s. Pausa con la pestaña oculta y reanuda al volver o al recuperar la red.
- **Se deja de consultar al llegar a un estado final.** Batería y datos del comensal.
- **La cuenta regresiva usa `server_now`,** no el reloj del celular.
- **La pantalla del turno tiene salida.** La «×» vuelve a la lista del local sin cancelar nada; «Ya no voy» sigue siendo una acción aparte y con confirmación.
- **El número solo se anima cuando baja.** Que suba se lee como que alguien pasó por delante ([07 § 4](../mesa247-docs/analisis/07_disenador_preguntas_y_devolucion.md)).
- **El reporte dice lo que el mockup del enunciado calla.** Los conteos son de **grupos** y la pantalla lo
  aclara con el total de personas al lado; mientras queden turnos sin resolver avisa de que el día no ha
  cerrado y la suma no cuadra; y separa lo que cerró el sistema al caducar de lo que marcó una persona
  ([09 § 2.8](../mesa247-docs/analisis/09_alcance_y_plan_de_implementacion.md), definiciones de
  [04 § 6](../mesa247-docs/analisis/04_modelo_de_datos.md)). Se refresca cada 30 s, no cada 5: no es la cola.
- **Los errores 422 se traducen por campo**; los de negocio llegan ya redactados del backend y se muestran tal cual.

## Comandos y configuración

| Comando | Uso |
|---|---|
| `npm run dev` | Desarrollo con recarga automática, puerto 5173 |
| `npm run typecheck` | Comprobar tipos sin generar archivos |
| `npm run build` | Comprobar tipos y generar el build en `dist/` |
| `npm run preview` | Revisar el build generado, puerto 4173 |

Para apuntar a otro backend, copia `.env.example` a `.env` y ajusta `API_PROXY_TARGET`; reinicia Vite. Esa variable configura el servidor local y no llega al navegador.

## Pruebas funcionales integradas

Las [pruebas de navegador](tests/README.md) ejecutan los flujos de comensal y anfitrión contra una API
real y datos temporales. Incluyen recuperación del turno, reporte, dos tablets y cortes de conexión.
Resultados de la ejecución y fallos abiertos: [informe del 19/09/2026](../mesa247-docs/auditoria/04_pruebas_funcionales_integradas.md).

## Fuera de esta versión

«Voy en camino» y el alta manual desde la tablet son opcionales del plan y su endpoint todavía no existe en la API ([contrato implementado](../mesa247-docs/api/README.md)). Tampoco hay reordenar ni re-llamar. El reporte del día sí está ([09 § 2.8](../mesa247-docs/analisis/09_alcance_y_plan_de_implementacion.md)), pero no su envío por correo al cierre: sin cierre del día automático no hay a qué engancharlo. El alcance y sus motivos están en el [plan de implementación](../mesa247-docs/analisis/09_alcance_y_plan_de_implementacion.md).

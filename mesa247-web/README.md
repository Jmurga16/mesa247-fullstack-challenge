# Mesa247 Web

Frontend con React, TypeScript, Vite y React Router. Incluye una página de bienvenida en `/` y un único `app.css`; las pantallas de comensal y anfitrión se implementarán después.

## Arranque

Requiere **Node.js 22.12+** y npm. Ejecuta desde la raíz del repositorio.

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

Abre <http://127.0.0.1:5173>. En los siguientes arranques basta con `npm run dev` desde `mesa247-web/` (usa `npm.cmd` en PowerShell).

## Estructura

```text
src/
├── main.tsx       Entrada de React y BrowserRouter
├── App.tsx        Rutas de la aplicación
├── app.css        Estilos compartidos
├── pages/         Pantallas; por ahora HomePage
└── components/    Reservado para componentes reutilizables
public/           Reservado para archivos estáticos
vite.config.ts    Servidor de desarrollo y proxy local
```

## Comandos y configuración

| Comando | Uso |
|---|---|
| `npm run dev` | Desarrollo con recarga automática, puerto 5173 |
| `npm run typecheck` | Comprobar tipos sin generar archivos |
| `npm run build` | Comprobar tipos y generar el build en `dist/` |
| `npm run preview` | Revisar el build generado, puerto 4173 |

Vite reenvía `/api` y `/healthz` al backend en `http://127.0.0.1:8000` durante el desarrollo. Con ambos servidores iniciados, <http://127.0.0.1:5173/healthz> debe devolver `{"status":"ok"}`. Las rutas de negocio bajo `/api` todavía no existen.

Para cambiar el destino, copia `.env.example` a `.env` y ajusta `API_PROXY_TARGET`; reinicia Vite. Esta variable configura el servidor local y no se incluye en el código del navegador. La pantalla inicial puede abrirse sin iniciar la API.

Referencia: [guía de Vite](https://vite.dev/guide/). El alcance funcional está en el [plan de implementación](../mesa247-docs/analisis/09_alcance_y_plan_de_implementacion.md).

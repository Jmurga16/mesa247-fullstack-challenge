# Mesa247 API

Backend de la lista de espera: alta y recuperación por teléfono, consulta del turno, cola autenticada,
llamar/sentar/no vino/se fue/borrar, cancelación pública, eventos transaccionales y notificador falso.
Este README cubre el backend. Puedes recorrer la API desde Swagger en `/docs`.

## Arranque rápido con SQLite

Requiere Python 3.11+. Desde la raíz del repositorio, PowerShell:

```powershell
cd mesa247-api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe seed.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

Bash (Linux/macOS):

```bash
cd mesa247-api
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python seed.py
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

No necesitas `.env` ni Docker. Se crea `mesa247.db` en el directorio actual; ejecuta desde `mesa247-api`.
SQLite usa WAL, `busy_timeout=5000` y claves foráneas activas. `--no-access-log` evita guardar los tokens
públicos incluidos en las rutas; los avisos falsos sí se ven en consola.

- API interactiva: <http://127.0.0.1:8000/docs>.
- Proceso: <http://127.0.0.1:8000/healthz>; conexión BD: <http://127.0.0.1:8000/readyz>.
- Seed: `terraza-lima`, `vientos-lima`, `casa-santiago`. Imprime un Bearer por local y links del frontend.
  Guarda los tokens iniciales: solo se almacena su hash. Repetir seed no duplica locales/dispositivos.
  `python seed.py --rotate-tokens` revoca y reemplaza los tokens demo si perdiste los originales.

## MySQL con Docker

Requiere Docker Desktop iniciado y Compose v2. Desde `mesa247-api`, PowerShell:

```powershell
docker compose up -d --wait
$env:DATABASE_URL = 'mysql+pymysql://mesa247:mesa247-local-only@127.0.0.1:3307/mesa247?charset=utf8mb4'
.\.venv\Scripts\python.exe seed.py
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

Bash:

```bash
docker compose up -d --wait
export DATABASE_URL='mysql+pymysql://mesa247:mesa247-local-only@127.0.0.1:3307/mesa247?charset=utf8mb4'
.venv/bin/python seed.py
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log
```

Compose usa MySQL 8.4, puerto `127.0.0.1:3307`, healthcheck y volumen persistente. Las credenciales del
ejemplo son solo locales. `docker compose down` detiene la base conservando los datos.
Para volver a SQLite elimina `DATABASE_URL` del entorno (`Remove-Item Env:DATABASE_URL` / `unset DATABASE_URL`).
Cambiar de motor no migra datos: cada base es independiente y requiere su seed.

Si la base MySQL fue creada antes de incorporar la ventana de espera, actualízala una vez sin borrar datos:

```powershell
docker compose exec -T db mysql -uroot -proot-local-only mesa247 -e "ALTER TABLE locations ADD COLUMN waiting_ttl_minutes SMALLINT UNSIGNED NOT NULL DEFAULT 120 AFTER call_grace_minutes, ADD CONSTRAINT ck_locations_waiting_ttl CHECK (waiting_ttl_minutes > 0);"
```

Una base nueva ya incluye la columna mediante `create_all()`. El comando no es para repetirlo: MySQL
responderá que la columna ya existe. En el VPS o en producción esta alteración debe ejecutarse como migración
controlada antes de desplegar el código.

## Flujo sin frontend

1. Abre `/docs` y ejecuta `GET /api/public/locations/terraza-lima`.
2. Ejecuta `POST /api/public/locations/terraza-lima/tickets` con este body:

```json
{"request_id":"431c04c8-f738-4d90-871f-79a3cd12f555","name":"Carla","phone":"987654321","party_size":4}
```

3. Guarda el token; repetir ese body devuelve 200 con el mismo turno.
4. Pulsa **Authorize** e introduce solo el Bearer del seed para `terraza-lima`.
5. `GET /api/host/queue` devuelve el id; úsalo en `POST /api/host/tickets/{ticket_id}/call`.
6. `GET /api/public/tickets/{token}` muestra called y deadline_at; un segundo llamado no genera otro aviso.
7. `POST /api/public/locations/terraza-lima/lookup` con `{"phone":"987654321"}` recupera el turno activo.
8. `GET /api/host/report` resume el día del local; con `?date=AAAA-MM-DD` mira un día anterior.

El [contrato documentado](../mesa247-docs/api/README.md) precisa estados, errores y concurrencia.

## Tests

Desde `mesa247-api`, PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
docker compose up -d --wait
.\.venv\Scripts\python.exe scripts/test_mysql.py
```

Bash:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
docker compose up -d --wait
.venv/bin/python scripts/test_mysql.py
```

SQLite temporal por test. El runner MySQL crea una base temporal aleatoria, ejecuta la misma suite y
elimina solo esa base al terminar; ignora DATABASE_URL. Si personalizaste Compose, exporta MYSQL_PORT y
MYSQL_ROOT_PASSWORD antes del runner. Incluye dos conexiones simultáneas, rollback de eventos y los
siete grupos obligatorios del plan. Bash está documentado; la validación local se realizó en Windows.

Validación actual: 51 tests en SQLite y los mismos 51 en MySQL 8.4. La validación anterior en una copia
limpia del backend comprobó instalación, seed, Uvicorn y el flujo HTTP en 35 s (Windows, caché de pip);
se ejecutó antes de añadir los cinco casos de la ventana de espera. TestClient emite dos avisos de
deprecación de dependencias; no hay tests fallidos.

## Configuración y despliegue mínimo

Copia `.env.example` a `.env` si necesitas persistir configuración; el entorno prevalece sobre `.env`.

| Variable | Predeterminado | Uso |
|---|---|---|
| APP_NAME | Mesa247 API | título de Swagger |
| DATABASE_URL | sqlite:///./mesa247.db | SQLite o mysql+pymysql://... |
| DATABASE_SSL_CA | vacío | CA para MySQL remoto; verifica hostname |
| CREATE_TABLES | true | create_all al arrancar; no migra tablas existentes |
| WEB_BASE_URL | http://localhost:5173 | base de links del seed |
| DEMO_MODE | true | atajos de la demo en `/api/demo/*`; **false** en cualquier despliegue real |
| MYSQL_PORT | 3307 | puerto Compose |
| MYSQL_PASSWORD | mesa247-local-only | usuario local; ajustar también DATABASE_URL |
| MYSQL_ROOT_PASSWORD | root-local-only | root local para Compose/tests |

Para una demo remota, `DATABASE_URL` y `DATABASE_SSL_CA` apuntan la API a un MySQL fuera del proceso.
Eso es lo que se desplegó: **MySQL 8.4 en un VPS propio**, con TLS obligatorio y una CA
propia, en lugar del Aiven que preveía el análisis. El procedimiento vive en `deploy/`, que no se versiona
porque depende del servidor de cada cual; las decisiones están en la enmienda 09 § 2.9.
Escapa los caracteres especiales del usuario/contraseña en la URL. SQLite sobre disco efímero no conserva
datos entre reemplazos de instancia.
La creación/migración de tablas y el aprovisionamiento de dispositivos deben ejecutarse como tareas
controladas antes de escalar; CREATE_TABLES=false desactiva la creación al arrancar. El seed y sus links
son para demo, no el emparejamiento de producción.

**`DEMO_MODE`.** Viene encendido para que la prueba funcione desde un clon limpio sin repartir tokens:
`GET /api/demo/locations` lista los locales activos y `POST /api/demo/locations/{code}/tablet` **emite**
una sesión de tablet y la devuelve en claro, revocando la anterior de ese local (etiqueta
`Tablet demo (web)`; la que imprime el seed no se toca). Es una fábrica de credenciales sin
autenticación: en un despliegue real va `DEMO_MODE=false`, y entonces esas rutas responden 404 y la
tablet se abre solo con su enlace. El emparejamiento de producción está fuera de alcance
(09 § 2.3, «login por persona»).

## Estructura

```text
app/
├── main.py          Factoría de app, errores, salud y routers
├── config.py        Entorno y .env
├── db.py            Engine y sesiones
├── models.py        Cuatro tablas y tiempos UTC
├── schemas.py       Contrato Pydantic de entrada/salida
├── auth.py          Bearer → dispositivo/local
├── notifier.py      Aviso falso tras commit
├── domain/
│   ├── time.py      Reloj inyectable y fecha de servicio
│   ├── phones.py    E.164 y validación
│   └── queue.py     Alta, transiciones, posición, ETA y métricas
└── routers/
    ├── public.py
    └── host.py
scripts/
├── export_openapi.py
└── test_mysql.py
tests/              Negocio e integración
seed.py             Tres locales y dispositivos demo
compose.yaml        MySQL local
requirements.txt    Dependencias de ejecución
requirements-dev.txt
.env.example
```

Pendientes del backend: alta manual, Voy en camino, cierre automático, canal real de notificaciones,
OTP, migraciones formales y despliegue.

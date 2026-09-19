# Mesa247 API

Backend con FastAPI y configuración mediante Pydantic Settings. Por ahora solo incluye `GET /healthz`; la base de datos y los endpoints de negocio se incorporarán después.

## Arranque

Requiere **Python 3.11+**. Ejecuta desde la raíz del repositorio.

### PowerShell

```powershell
cd mesa247-api
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Bash (Linux / macOS)

```bash
cd mesa247-api
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

No es necesario activar el entorno virtual. En los siguientes arranques basta con ejecutar el último comando desde `mesa247-api/`.

- Salud: <http://127.0.0.1:8000/healthz> → `{"status":"ok"}`.
- Documentación interactiva: <http://127.0.0.1:8000/docs>.

## Estructura

```text
app/
├── main.py       Aplicación y endpoint de salud
├── config.py     Configuración y lectura de .env
├── domain/       Reservado para reglas de negocio
└── routers/      Reservado para rutas públicas y del anfitrión
tests/            Reservado para los tests del dominio
requirements.txt Dependencias con versiones fijas
```

## Configuración

Opcionalmente, copia `.env.example` a `.env` (`Copy-Item .env.example .env` en PowerShell; `cp .env.example .env` en Bash).

| Variable | Valor predeterminado | Uso |
|---|---|---|
| `APP_NAME` | `Mesa247 API` | Título de la documentación de la API |

Las variables de entorno prevalecen sobre `.env`. Todavía no se necesita una base de datos ni hay una suite de tests; en esta etapa se comprueba el arranque y la respuesta de `/healthz`.

Referencia: [primeros pasos de FastAPI](https://fastapi.tiangolo.com/tutorial/first-steps/). El alcance funcional está en el [plan de implementación](../mesa247-docs/analisis/09_alcance_y_plan_de_implementacion.md).

# Contrato de API implementado

Revisión backend: 18/09/2026. Alcance: [09 § 2.6 y § 5](../analisis/09_alcance_y_plan_de_implementacion.md).
Esquema completo: [openapi.json](openapi.json), generado desde FastAPI mediante
`python scripts/export_openapi.py` en `mesa247-api/`. En ejecución: `/docs` y `/openapi.json`.
Si cambia una ruta, campo, regla o plan, revisar este contrato, el plan y la estructura de
[03 § 3](../analisis/03_arquitectura_y_decisiones.md) antes de cerrar el cambio.

## Rutas disponibles

| Método | Ruta | Resultado |
|---|---|---|
| GET | `/healthz` | 200: proceso vivo |
| GET | `/readyz` | 200: BD accesible; 503 si falla |
| GET | `/api/public/locations/{code}` | configuración pública; 404 inexistente/inactivo |
| POST | `/api/public/locations/{code}/tickets` | 201 nuevo, 200 reintento, 409 teléfono activo |
| POST | `/api/public/locations/{code}/lookup` | 200 turno activo del día con token; 404 sin coincidencia |
| GET | `/api/public/tickets/{token}` | 200 turno propio; 404 token inexistente |
| POST | `/api/public/tickets/{token}/cancel` | 200 cancelado; 409 transición inválida |
| GET | `/api/host/queue` | cola del local y día de servicio, orden `(sort_key, id)` |
| POST | `/api/host/tickets/{ticket_id}/call` | llamar desde waiting |
| POST | `/api/host/tickets/{ticket_id}/seat` | sentar desde waiting/called |
| POST | `/api/host/tickets/{ticket_id}/no-show` | no vino desde called |
| POST | `/api/host/tickets/{ticket_id}/leave` | se fue desde waiting |
| POST | `/api/host/tickets/{ticket_id}/remove` | borrar desde waiting/called |

Host requiere `Authorization: Bearer <token>`. Falta, revocación, local inactivo o token inválido: 401.
El local se deriva del dispositivo; nunca se acepta en el body. Turno de otro local: 404.
Los opcionales `POST /api/host/tickets` y `/on-my-way` no están implementados.

## Precisiones de implementación

- Alta: `request_id` UUID v4, nombre recortado de 1–40 caracteres, teléfono válido normalizado a E.164,
  `party_size` entero estricto de 1–50 y máximo del local (20 por defecto); campos adicionales: 422.
  Repetir UUID devuelve su turno actual, incluso terminal; no actualiza los datos originales.
  Un UUID nuevo con teléfono **todavía en espera** devuelve 409 sin token.
- **Ventana de espera (09 § 2.7).** Antes de rechazar por teléfono repetido, el alta caduca el turno
  que ocupa esa llave si ya venció: `called` pasado `called_at + call_grace_minutes`, o `waiting`
  pasado `joined_at + waiting_ttl_minutes` (columna nueva de `locations`, 120 por defecto). Pasa a
  `expired` con su evento —`data.reason = "stale_on_rejoin"`— y libera `active_key`. `expire` no tiene
  ruta HTTP: solo lo dispara un alta nueva, y sigue sin haber cierre del día. Expiración, evento,
  turno reemplazante y evento `joined` se confirman juntos; un fallo conserva el turno anterior activo.
- Consulta pública: solo campos de `TicketPublic`, sin teléfono ni id. `/lookup` acepta teléfono como
  credencial según 09 § 2.5. Respuestas `/api/`: `Cache-Control: no-store`.
- ETA se redondea al múltiplo de cinco superior: seis grupos delante y 4 min/grupo dan **30 min**.
  `groups_ahead` y `eta_min` son null fuera de waiting; `deadline_at` solo existe estando called.
  `avg_wait_min` tiene un decimal y es null sin sentados del día.
- UPDATE compara id, local y **estado observado por esa petición**. Si cambia entre lectura y escritura,
  relee: 200 sin efectos si ya es destino; 409 en otro caso. Call y seat que leyeron waiting producen
  una transición y un conflicto. Si seat lee called después del commit de call, puede sentar.
  No se detecta una pantalla desactualizada: no hay versión en el body.
- Repetir destino: 200 sin evento nuevo. Cancelar un no_show es 200 conservando no_show.
  `expired` no tiene endpoint: lo escribe el alta al reemplazar un turno vencido.
- Evento de estado y UPDATE hacen commit juntos. Aviso y su evento ocurren después; si el proveedor
  falla se registra `notification_failed` y se mantiene called. Si falla guardar ese evento,
  el llamado también se conserva y el fallo queda en log. Sin outbox ni reintentos de entrega.
- Errores de negocio: `{"error":"slug","message":"texto en español"}`. Validación: 422 con
  `detail` de Pydantic; el futuro frontend traduce por campo. Error de BD: 503 `temporarily_unavailable`;
  inesperado: 500 `internal_error`, sin trazas en respuesta.

## Base de datos

SQLite archivo es el arranque predeterminado; MySQL 8.4 en Docker Compose es la alternativa local.
El modelo SQLAlchemy es común. `DATABASE_URL` selecciona el motor; `DATABASE_SSL_CA` permite verificar
certificado y hostname de MySQL remoto. Aiven no se conectó ni desplegó en esta etapa.
El DDL ejecutable es `app/models.py`; el SQL del análisis es referencia histórica.

Referencias: [SQLite en SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html),
[MySQL y TLS en SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/mysql.html),
[imagen oficial de MySQL](https://hub.docker.com/_/mysql).

# Mesa247

Lista de espera digital para restaurantes. Este repositorio reúne el backend, el frontend y la documentación del proyecto.

**Estado del backend:** API funcional de la lista de espera, SQLite por defecto y MySQL 8.4 con Docker Compose. Incluye seed y tests; instrucciones en el [README API](mesa247-api/README.md).

**Estado del frontend:** las tres pantallas del corte —unirse desde el QR, la página del turno y la cola del anfitrión— contra esa API, con recuperación del turno por teléfono y estados de red. Instrucciones en el [README de la web](mesa247-web/README.md).

Con ambos servidores arriba, los enlaces que imprime el seed del backend llevan al flujo completo: el comensal se une, ve su turno actualizarse solo, y el anfitrión lo llama y lo sienta desde la tablet. Si no tienes los enlaces a mano, <http://127.0.0.1:5173> lleva un selector con los tres locales del piloto que hace de QR; la tablet se abre en <http://127.0.0.1:5173/admin>.

## Estructura

```text
Mesa247/
├── mesa247-api/     FastAPI · Python
├── mesa247-web/     React · TypeScript · Vite
├── mesa247-docs/    Alcance, decisiones y registro de IA
└── deploy/          Despliegue en el VPS (no versionado: es de quien levanta el servidor)
```

## Arranque local

Requisitos: **Python 3.11+**, **Node.js 22.12+** y npm. Se verificó con Python 3.11 y Node.js 24.

Abre dos terminales desde la raíz del repositorio y sigue los pasos de cada proyecto:

| Proyecto | Instalación y ejecución | URL local |
|---|---|---|
| Backend | [README de la API](mesa247-api/README.md) | <http://127.0.0.1:8000/docs> |
| Frontend | [README de la web](mesa247-web/README.md) | <http://127.0.0.1:5173> |

Ambos arrancan con valores predeterminados; copiar los archivos `.env.example` es opcional. Detén cada servidor con `Ctrl+C`.

## Despliegue

La aplicación está publicada en <https://mesa247.devkora.com> sobre un VPS propio: MySQL 8.4, la API y el
frontend en el mismo servidor, con Caddy sirviendo el build de React y haciendo de proxy a `/api`. La tablet
se abre en <https://mesa247.devkora.com/admin> y la API en <https://mesa247.devkora.com/docs>. El
procedimiento vive en `deploy/`, fuera del repositorio porque depende del servidor de cada cual; el porqué de
dejar Google Cloud y Aiven está en la enmienda § 2.9 del
[alcance](mesa247-docs/analisis/09_alcance_y_plan_de_implementacion.md).

## Documentación

- [Índice de documentación](mesa247-docs/README.md).
- [Alcance y plan de implementación](mesa247-docs/analisis/09_alcance_y_plan_de_implementacion.md): referencia para las siguientes etapas.
- [Registro del uso de IA](mesa247-docs/conversaciones/registro.md).

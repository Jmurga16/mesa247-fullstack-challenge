# Mesa247

Lista de espera digital para restaurantes. Este repositorio reúne el backend, el frontend y la documentación del proyecto.

**Estado actual:** estructura inicial ejecutable del entregable 2. La API expone una comprobación de salud y la web muestra una página de bienvenida. Los flujos de la lista de espera todavía no están implementados.

## Estructura

```text
Mesa247/
├── mesa247-api/     FastAPI · Python
├── mesa247-web/     React · TypeScript · Vite
└── mesa247-docs/    Alcance, decisiones y registro de IA
```

## Arranque local

Requisitos: **Python 3.11+**, **Node.js 22.12+** y npm. Se verificó con Python 3.11 y Node.js 24.

Abre dos terminales desde la raíz del repositorio y sigue los pasos de cada proyecto:

| Proyecto | Instalación y ejecución | URL local |
|---|---|---|
| Backend | [README de la API](mesa247-api/README.md) | <http://127.0.0.1:8000/docs> |
| Frontend | [README de la web](mesa247-web/README.md) | <http://127.0.0.1:5173> |

Ambos arrancan con valores predeterminados; copiar los archivos `.env.example` es opcional. Detén cada servidor con `Ctrl+C`.

## Documentación

- [Índice de documentación](mesa247-docs/README.md).
- [Alcance y plan de implementación](mesa247-docs/analisis/09_alcance_y_plan_de_implementacion.md): referencia para las siguientes etapas.
- [Registro del uso de IA](mesa247-docs/conversaciones/registro.md).

# Mesa247 · Documentación

Documentación de análisis, decisiones y plan de implementación de la lista de espera digital.
Enunciado del encargo: https://prueba-fullstack-mesa247.pages.dev/

## Por dónde empezar

1. [Alcance y plan de implementación](analisis/09_alcance_y_plan_de_implementacion.md): referencia principal para empezar a programar. Ante contradicciones con los documentos anteriores, prevalece este documento.
2. [Resumen de la revisión final](auditoria/03_resumen_revision_final.md): cambios, decisiones y pendientes.
3. [Análisis inicial y contexto](analisis/00_contexto_del_analisis.md): orden de lectura y fundamentos de la propuesta.
4. [Entrega y uso de IA](entrega_y_uso_de_ia.md): restricciones, entregables y cómo se declara el trabajo hecho con IA.

## Organización

```text
Mesa247/
├── mesa247-api/          Backend
├── mesa247-web/          Frontend
└── mesa247-docs/
    ├── README.md
    ├── entrega_y_uso_de_ia.md   Restricciones, entregables y declaración del uso de IA
    ├── analisis/        Contexto, documentos 01–09, SQL y diagrama
    ├── auditoria/       Informe, resolución y resumen final
    └── conversaciones/ Registro de prompts, decisiones y exportaciones
```

- [Auditoría](auditoria/README.md): revisión y resolución de hallazgos.
- [Conversaciones](conversaciones/README.md): explica cómo se registran los prompts, las decisiones y las conversaciones.
- [Registro](conversaciones/registro.md): historial cronológico del trabajo asistido por IA.
- [Prompt inicial](conversaciones/prompt_inicial.md): texto consolidado del análisis y la auditoría. No sustituye las exportaciones originales.
- Las exportaciones completas se guardarán en `conversaciones/` como `conversacion_nota.*`, `conversacion_backend.*` y `conversacion_frontend.*`.

Los antiguos prompts A/B/C que menciona la auditoría no estaban presentes al reorganizar los archivos. Sus menciones se conservan como referencias históricas, sin enlaces a archivos inexistentes.

Se conservaron los documentos originales, con nombres y rutas actualizados. El contexto inicial y el resumen final tienen contenido parcialmente repetido y se mantienen para preservar el registro de trabajo. Esta reorganización no es una nueva auditoría técnica.

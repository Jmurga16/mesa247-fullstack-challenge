# Conversaciones con IA

Esta carpeta conserva el uso de IA durante el desarrollo y permite relacionar cada consulta con las decisiones tomadas.

- [`prompt_inicial.md`](prompt_inicial.md): prompts consolidados del análisis previo y su auditoría.
- [`registro.md`](registro.md): historial cronológico de prompts, decisiones, resultados y correcciones.
- `conversacion_nota.*`, `conversacion_backend.*` y `conversacion_frontend.*`: exportaciones completas y sin editar de cada conversación, cuando existan.

El registro resume el trabajo para facilitar su lectura y **no sustituye a las exportaciones**: está ordenado por tema y es, por definición, material editado. Las conversaciones exportadas son la fuente completa de las consultas y respuestas, y son lo que pide el encargo.

Cada exportación se agrupa por la parte que trabajó la sesión. Varias sesiones tocaron backend y frontend a la vez; cuando ocurre, la exportación va en la parte a la que pertenece el grueso del trabajo y se anota al principio qué más cubre.

Lo único que se recorta son las credenciales del VPS —contraseñas de root y de MySQL, Bearer del seed, claves privadas—: se sustituyen por `[credencial retirada]`, que se ve, y el recorte se declara al principio del archivo. No se recorta nada más.

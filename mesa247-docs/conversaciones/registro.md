# Registro de prompts y decisiones

Este archivo se actualiza durante el desarrollo. Cada entrada registra una solicitud relevante y la decisión resultante, sin reemplazar la exportación completa de la conversación.

## 2026-09-18 — Análisis previo

**Prompt o solicitud**

Analizar el enunciado y el prototipo antes de programar, proponer el alcance, la arquitectura y el orden de implementación, y auditar después la propuesta con un segundo modelo.

**Decisión**

Usar dos puntos de vista antes de iniciar: Claude Opus Extra para el análisis inicial y GPT Astra High para la auditoría. Los prompts consolidados están en [`prompt_inicial.md`](prompt_inicial.md).

**Resultado**

Se generaron los documentos de `../analisis/`, la revisión de `../auditoria/` y el alcance final de implementación.

**Correcciones o rechazos**

La auditoría detectó contradicciones y riesgos; su resolución está documentada en [`../auditoria/02_resolucion_de_hallazgos.md`](../auditoria/02_resolucion_de_hallazgos.md).

## 2026-09-18 — Entregable 1: preguntas al diseñador, enmienda del alcance y cierre de la nota

**Parte del proyecto:** nota.

**Prompt o solicitud**

Cerrar las tres preguntas al diseñador que pide el enunciado, respondidas por el autor, y dejarlas
registradas de forma trazable porque forman parte del entregable 1. Las tres planteadas: si la posición
que ve el comensal debe subir cuando el anfitrión reordena; si la lista debe contemplar zonas o ambientes;
y si el comensal debe poder recuperar su turno con el teléfono tras cerrar la página. Después, cerrar los
demás puntos de la nota con las respuestas del autor: qué se le devuelve al diseñador, qué decisiones no se
deberían cambiar más adelante y cómo se lleva a producción.

**Decisión**

1. Las tres preguntas que van en la nota son las del autor, no las tres que proponía el análisis previo
   (07 § 3). Quedan en [`../analisis/07_disenador_preguntas_y_devolucion.md`](../analisis/07_disenador_preguntas_y_devolucion.md) § 3.1,
   que manda sobre § 3; las candidatas se conservan como registro del análisis.
2. El número visible al comensal nunca sube: se muestra el menor entre el valor calculado y el último ya
   mostrado. En el corte de 4 horas el caso no se da (reordenar está fuera), así que la regla no cuesta
   nada ahora y evita rehacer la pantalla cuando entre reordenar.
3. Sin zonas ni ambientes en esta versión: una sola lista por local. Una cola por zona son N colas y
   cambiaría posición, ETA, deduplicación por teléfono y reporte.
4. Sí se puede recuperar el turno con el teléfono desde «Ya estoy en la lista de espera». Esto reabre una
   decisión congelada (09 § 2.1 O3 y 08 § 4b, que prohibían revelar el token a quien solo conoce el
   teléfono). Motivo: perder el link es un hecho diario y no tener salida devuelve al comensal a la puerta.
   Se asume el riesgo —con el código público del QR y un número se puede abrir y cancelar ese turno— y se
   declara; el OTP queda como mitigación fuera del corte.
5. **Devolución al diseñador**: dos prioridades, no cinco. La posición al reordenar (que el comensal no vea
   que retrocedió) y aplazar WhatsApp para validar antes registro, cola y llamado. Se aclaró el alcance del
   aplazamiento: WhatsApp queda fuera del corte de 4 horas (notificador falso), **pero sigue dentro del
   piloto de 3 semanas**; no se reescribe el plan de 05 § 2.
6. **Decisiones difíciles de cambiar**: las cuatro del autor —id propio de la espera y el teléfono como
   llave de búsqueda, no como identidad; los estados y sobre todo la definición de las métricas; cada
   espera atada a un local; el modelo de tiempo con Lima y Santiago— más la URL del QR impreso, que se
   añadió por ser la más cara de todas y no estaba en la lista inicial.
7. Los seis puntos se redactan en un documento aparte —`entregables/01_nota_tecnica.md`— en vez de dejarlos
   repartidos por `analisis/`. Motivo: el entregable es la nota, y el análisis es lo que la respalda; tenerlos
   mezclados obligaba a reconstruirla al final. Restricción dura: 1–2 páginas.
8. **Producción**: Cloud Run y Cloud Monitoring con aviso por correo y al celular, logs JSON con
   `request_id`, `location_id`, `ticket_id` y teléfonos enmascarados para que cualquiera pueda
   diagnosticar. Base: **Aiven (tier gratuito) para demo y staging, Cloud SQL para el piloto**, decidido
   así por los backups, la recuperación a un punto en el tiempo y la región. Se mantienen las cuatro
   alarmas de 06 § 3 y no solo la de caída: un uptime check no ve el QR roto ni la página que no carga.

**Resultado**

- `../analisis/07_disenador_preguntas_y_devolucion.md`: nueva § 3.1 con las tres preguntas, su respuesta
  asumida y el impacto de cada una en el corte; el borrador del mensaje al diseñador (§ 6) cierra ahora con
  estas tres y con los tres supuestos, y se deja constancia de que salieron de mirar el prototipo.
- `../analisis/05_alcance_estimaciones_y_orden.md`: filas nuevas en la tabla de alcance —«Ya estoy en la
  lista de espera» (0,1 d, dentro del corte), OTP (0,5 d, fuera) y zonas o ambientes (1–1,5 d, fuera)— y
  `displayed_ahead` sumado a la estimación de reordenar.
- `../analisis/04_modelo_de_datos.md`: sin cambios de estructura. Se anota que `/lookup` reutiliza el índice
  único de `active_key`, y que `zone` y `displayed_ahead` quedan explícitamente sin escribir.
- `../analisis/03_arquitectura_y_decisiones.md`: nueva § 6.1 con las cinco decisiones difíciles de cambiar
  que van en la nota.
- `../analisis/06_produccion_y_tests.md`: nueva § 0 con la respuesta corta de producción, y Aiven añadido
  a § 1 como base de demo y staging, con sus límites declarados.
- `../entregables/01_nota_tecnica.md`: **nuevo**. La nota técnica escrita, con los seis puntos que pide el
  enunciado. Es el documento que se envía; `analisis/` queda como el material que lo sostiene.
- `../entrega_y_uso_de_ia.md` y `../README.md`: apuntan al entregable escrito, y la tabla de secciones a
  07 § 3.1, 07 § 4.1, 03 § 6.1 y 06 § 0.
- `../analisis/09_alcance_y_plan_de_implementacion.md`: nueva § 2.5 (enmienda posterior al congelamiento),
  O3 reescrito, nuevo O13, endpoint `POST /api/public/locations/{code}/lookup` en § 5.1, séptimo test no
  negociable y renumeración de § 7.2, paso 5 del frontend, definición de listo y punto 10 de deuda conocida.
- `../analisis/08_decisiones_y_preguntas_tecnicas.md`: 4b corregido y nuevos 4d (zonas) y 4e (reordenar).

**Correcciones o rechazos**

La IA propuso que la consulta por teléfono devolviera solo lectura (grupos delante, tiempo y estado) sin el
token ni «Ya no voy», para no tocar O3. Se rechazó: adivinar un móvil completo y válido de alguien que
además está en la cola de ese local hoy no se considera un ataque realista, y media recuperación no resuelve
el caso. El OTP se acepta como propuesta de seguridad posterior, no alcanzable en este corte.

## 2026-09-18 — Entregable 2: estructura inicial ejecutable

**Parte del proyecto:** backend y frontend.

**Prompt o solicitud**

Crear la estructura de carpetas de FastAPI y React, con README breves y actualizables. En esta etapa solo se requiere que ambos proyectos levanten, sin funcionalidades de negocio.

**Decisión**

Mantener `mesa247-api` y `mesa247-web` conforme al plan: FastAPI con `/healthz` y configuración mediante Pydantic Settings; React + TypeScript + Vite + React Router con una página inicial y `app.css`. Preparar carpetas de dominio, rutas, tests, páginas y componentes. Posponer base de datos y flujos de negocio al desarrollo posterior. Configurar el proxy local de Vite hacia el backend y ejemplos de entorno opcionales.

**Resultado**

- Creados los puntos de entrada, configuración y dependencias de ambos proyectos, con versiones directas fijas y `package-lock.json` en la web.
- Añadidos README de raíz, API y web, con arranque en PowerShell y Bash; `.gitignore` excluye entornos, dependencias, builds y datos locales.
- Validado en Windows con Python 3.11.9 y Node.js 24.19.0: instalación de dependencias, `pip check`, `npm ci`, comprobación de tipos y build. Ambos servidores arrancaron; `/healthz`, `/docs`, el HTML y el módulo de entrada de React respondieron por HTTP, y `/healthz` funcionó a través del proxy de Vite.
- Esta validación cubre el arranque inicial; todavía no corresponde al corte funcional completo ni a sus tests de negocio. Los comandos de Bash quedan documentados, sin ejecución en Linux/macOS en esta etapa.

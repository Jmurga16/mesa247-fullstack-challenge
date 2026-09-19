# Nota técnica · Lista de espera digital

Piloto: La Terraza Azul y Cuatro Vientos (Lima), Casa Mediterránea (Santiago) · 18/09/2026

## 1. Tres preguntas al diseñador, y qué asumo mientras tanto

Salieron de mirar las cinco pantallas del prototipo.

1. **Cuando reordenas la cola, ¿al comensal le sube el número?** En el celular dice "estás en el puesto 7";
   si subes a otro grupo, a esa persona le toca ver el 8.
   *Asumo que no.* El número visible nunca sube: se muestra el menor entre el valor real y el último ya
   mostrado, y se normaliza solo cuando la cola avanza. Animación solo hacia abajo. El tiempo sí se
   recalcula, porque se presenta como aproximado.
2. **¿La lista separa terraza, salón y barra, o es una sola cola por local?** Una cola por ambiente no es
   una pantalla más: son varias colas, con su posición, su tiempo y su reporte, y agregarlas después obliga
   a migrar turnos ya registrados.
   *Asumo una sola cola por local.* El único dato que entra es el tamaño del grupo; quién se sienta dónde
   lo decide el anfitrión.
3. **Si el comensal cierra la página, ¿vuelve a su turno con su teléfono?** El link es lo único que tiene y
   se pierde al cerrar la pestaña.
   *Asumo que sí*, con un «Ya estoy en la lista de espera» que busca la espera activa de ese local y ese
   día. Acepto el riesgo y lo digo: el QR es público, así que con un número se puede abrir ese turno. La
   mitigación es un código de verificación y depende del canal real de WhatsApp.

## 2. Qué construyo primero y qué corto

Primero el flujo punta a punta, que es lo único que demuestra que el cuaderno se puede reemplazar: **se une
por QR → el anfitrión lo ve → lo llama, lo sienta o lo marca como que no vino**, con cada hecho registrado.
Dentro va lo que parece detalle y no lo es: alta idempotente (en la puerta hay mala señal y el doble toque
va a pasar), transiciones atómicas para que dos anfitriones un viernes no se pisen, bitácora en la misma
transacción que el cambio de estado, y estados de red que conservan el último dato en vez de mostrar un
error. Cierra con notificador falso, siete tests, seed de los tres locales y README probado desde un clon
limpio.

Lo que corto, en días ideales de una persona y para producción:

| Pieza | Est. | Decisión |
|---|---|---|
| WhatsApp real (plantilla, envío, webhook, estados) | 3 d | Piloto, semana 2. Depende de Meta: lo único que no controlo |
| SMS de respaldo | 1 d | Piloto. Plan B si Meta rechaza o no hay WhatsApp |
| Reporte por correo al cierre | 1,5–2 d | Semana 3. **Los datos se guardan desde el día 1** |
| Alta manual en la tablet | 0,5 d | Lo primero si sobra tiempo: quien no escanea queda fuera |
| Arrastrar para reordenar | 1–1,5 d | Fuera. «Llamar» en cualquier fila ya prioriza al frecuente |
| Cliente frecuente | 2–4 d | Fuera. No está definido de dónde sale el dato |
| Infra, CI/CD y observabilidad | 3–4 d | Se describe en § 6 |
| Cierre del día, rate limiting, editar el tamaño del grupo | ~1 d | Deuda declarada |

El piloto suma ~14–15 días en 15 hábiles: sin margen. Si algo se atrasa se mueve el reporte por correo,
porque los datos ya están guardados.

## 3. El modelo de datos

Cuatro tablas. **locations**: código del QR, zona horaria, hora de corte del día, minutos por grupo.
**host_devices**: la tablet, con el token hasheado — el local sale del token, nunca del cuerpo de la
petición. **tickets**: id interno y token público opaco para el link; local, día de servicio, nombre,
teléfono en E.164, tamaño, estado, orden de llegada, y la espera prometida al unirse, para medir después
cuánto se equivoca el estimador. **ticket_events**: bitácora append-only.

Estados: `waiting → called → seated`, con las salidas `cancelled`, `no_show`, `removed` y `expired`.

Dos claves hacen el trabajo. `active_key = "{local}:{día}:{teléfono}"`, única y en NULL al cerrarse el
turno: un turno activo por teléfono, local y día — con el día dentro, un pendiente del viernes no bloquea
ese número el sábado. Y el identificador de petición del navegador, único por local: el reintento devuelve
el mismo turno. Regla de negocio e idempotencia son cosas distintas, a propósito.

Invariante: **toda transición a estado final fija estado, hora de cierre y `active_key = NULL` en el mismo
UPDATE, y escribe su evento en la misma transacción.** Si el evento falla, la transición no ocurre.

## 4. Qué le devolvería al diseñador, y cómo

Dos cosas. **La posición cuando se reordena**: que nadie vea que retrocedió; un número que sube se lee como
que alguien te pasó por delante, y es la vía más corta a que la persona se vaya. **Y WhatsApp después**:
primero valido registro, cola y llamado, que es lo que reemplaza el cuaderno; si eso no funciona, el
WhatsApp solo hace más caro el fracaso. No lo aplazo indefinidamente —tiene su semana en el piloto— y le
digo por qué no se puede aplazar para siempre: la página del turno solo avisa si está abierta y a la vista,
así que **WhatsApp es el único canal que alcanza a quien se fue a caminar**. Mientras no esté, la regla es
"quédate cerca" más llamado por voz, y eso el local tiene que saberlo antes de arrancar, no después.

Cómo: mensaje corto con lo que sí sale y cuándo, cada "no" con alternativa y con la razón del lado del
comensal, separando "no para el piloto" de "no nunca", y quince minutos de llamada. Su diseño es claro y
resuelve el dolor real: son ajustes, no un rediseño.

## 5. Lo que no voy a poder cambiar después

- **La URL del QR impreso.** A 150 locales, cambiarla es reimprimir y recorrer puertas. Por eso desde el
  día 1: dominio propio y código corto con indirección en base, nunca un `*.run.app`.
- **Que cada espera tenga identificador propio.** El teléfono es llave de búsqueda, no identidad: dos
  familias comparten número y la gente lo cambia.
- **La definición de los estados y las métricas.** Cambiar a mitad del piloto qué cuenta como "se fue sin
  sentarse" no rompe nada técnico: rompe la comparabilidad, que es lo que el piloto tiene que demostrar.
- **Que cada espera pertenezca a un local.** Un fallo aquí no es un bug, es una fuga entre clientes.
- **El modelo de tiempo**: UTC, zona por local y día de servicio con hora de corte. El piloto cruza dos
  husos y un viernes que termina a las 00:30 sigue siendo viernes.

Irrecuperables de verdad hay dos: el evento que no registré y el consentimiento que no pedí. Por eso la
bitácora entra el día 1 aunque el reporte sea de la semana 3.

## 6. Cómo lo llevo a producción

**Despliegue.** Cloud Run en southamerica-west1, cerca de los tres locales. Cloud SQL MySQL 8 en el piloto,
por backups, recuperación a un punto en el tiempo e IP privada; Aiven con su tier gratuito para la demo y
el entorno de prueba. Secretos en Secret Manager, migraciones antes de mover tráfico, rollback en un
comando.

**Alarmas: cuatro, no una.** Uptime externo, errores 5xx, avisos fallidos y **silencio del negocio** —cero
altas en un local dentro del horario en que normalmente las hay—. Las tres primeras las ve cualquier
chequeo técnico; la cuarta es la que importa, porque la API puede responder 200 mientras el QR está roto o
la página no carga en móviles.

**Un viernes a las 9.** Uptime y 5xx llegan al correo y al celular de guardia en uno o dos minutos; si la
API está bien pero el producto no, avisa el silencio del negocio; y el encargado del local tiene un número
al que escribir. Lo primero no es arreglar, es sostener la operación: la tablet conserva la última cola con
aviso de "sin conexión" y el local pasa a papel. Después: si hubo deploy, rollback de tráfico; si es la
base, failover; si es WhatsApp, ese local pasa a SMS con un flag. Los logs son JSON con identificador de
petición, de local y de turno, y con teléfonos enmascarados, para que el diagnóstico no dependa de quién
esté mirando.

## Límites, dichos antes de que los pregunten

El test de doble llamado prueba la condición del UPDATE en secuencial, no concurrencia real: esa versión
corre contra MySQL en CI. El tiempo estimado es una heurística sin calibrar, y se guarda la promesa de cada
alta para medir el error desde el día 1. El notificador falso no prueba entrega. El cierre del día no está
implementado: la cola filtra por día de servicio, así que lo de ayer no ensucia hoy, pero el turno queda
abierto.

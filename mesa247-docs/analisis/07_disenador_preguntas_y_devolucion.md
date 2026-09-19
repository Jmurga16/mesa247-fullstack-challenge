# 07 · El diseñador: preguntas, supuestos y devolución

## 1. Criterio para elegir las 3 preguntas
Una buena pregunta aquí cumple las tres:
- Cambia el modelo de datos o una decisión difícil de revertir.
- Bloquea el piloto si se responde mal.
- No se puede asumir con seguridad (a diferencia de colores, textos o tamaños).
Regla práctica: preguntar por el comportamiento en la puerta, no por la interfaz. Lo que se puede asumir
sin riesgo, se asume y se declara.

## 2. Candidatas (lista larga)
1. ¿El anfitrión llama por orden de llegada o por la mesa que se libera (tamaño del grupo)?
2. ¿Qué ve el comensal cuando alguien es priorizado y su número sube? ¿Posición o solo tiempo?
3. ¿Qué pasa cuando vencen los 10 minutos? ¿Se cancela solo, se re-llama, decide el anfitrión?
4. ¿Cómo cuentan en el reporte los que dicen «Ya no voy» después de ser llamados? ¿"Espera media" de quién?
5. ¿Qué pasa con quien no puede escanear el QR o no tiene WhatsApp (sin datos, turista, adulto mayor)?
6. ¿Qué es "cliente frecuente" y de dónde sale el dato?
7. ¿La nueva lista reemplaza a la de El Libro? ¿Compite con las reservas por las mismas mesas?
8. ¿Cómo entra el anfitrión en una tablet compartida?
9. ¿Puede unirse alguien que no está en la puerta (foto del QR)? ¿Es deseado o abuso?
10. ¿Tamaño máximo de grupo? ¿Los grupos grandes se manejan igual?
11. ¿Quién recibe el reporte y a qué hora es el cierre en cada local?
12. ¿El remitente es Mesa247 o el restaurante? ¿Un número por país?
13. ¿"12 en cola" incluye a los ya llamados?
14. ¿Qué debe ver el anfitrión si el WhatsApp no se entregó?

## 3. Las 3 que yo haría (con el supuesto si no hay respuesta)

P1. "¿El anfitrión llama por orden de llegada o según la mesa que se libera? En el prototipo la Familia Rojas
     (puesto 3, 6 personas) ya fue llamada antes que Carla y Jorge."
- Por qué importa: define qué significa la "posición", cómo se calcula el tiempo estimado, si hace falta reordenar y
  qué promesa le hacemos al comensal. Toca el modelo (orden, tamaño) y la experiencia pública.
- Supuesto: se llama según la mesa disponible; la cola usa el orden de llegada como referencia; el anfitrión puede
  llamar a cualquier fila (así también prioriza al frecuente, sin arrastrar); el comensal ve "grupos antes que tú" y
  un tiempo conservador; no se anima cuando el número sube.

P2. "Cuando alguien es llamado, ¿qué pasa si no aparece en los 10 minutos, y cómo cuenta en el reporte quien dice
     «Ya no voy» después de ser llamado?"
- Por qué importa: define los estados finales, quién los dispara (persona o sistema) y las métricas del piloto,
  que no se pueden redefinir a mitad del piloto sin perder comparabilidad.
- Supuesto: nada automático en v1; la fila se pinta en rojo al vencer; el anfitrión decide Sentar, Re-llamar o No vino.
  Al cierre, los llamados sin resolver cuentan como "no vinieron" y los que esperaban como "se fueron sin sentarse".
  «Ya no voy» después del llamado cuenta como "no vino al ser llamado". "Espera media" = llegada → sentado.

P3. "¿Qué hacemos con quien no puede o no quiere escanear el QR, o no tiene WhatsApp?"
- Por qué importa: si esa gente queda fuera, el cuaderno sigue y habrá dos listas; el piloto fracasa por adopción,
  no por tecnología. Define si el teléfono es obligatorio y si hace falta un canal de respaldo.
- Supuesto: el anfitrión agrega a esa persona desde la tablet (nombre y tamaño; teléfono opcional). Sin teléfono se le
  llama por voz; sin WhatsApp, SMS con link. El QR sigue siendo el camino principal.
- La otra mitad de esta pregunta, que conviene hacer explícita: **¿puede el comensal alejarse del local?**
  La página del turno solo avisa si está abierta y a la vista — el polling se pausa con la pestaña oculta y
  no despierta un teléfono bloqueado. Es decir: **WhatsApp no es un canal más, es el único que alcanza a
  alguien que se fue a caminar**. Si Meta rechaza la plantilla, la regla operativa del piloto pasa a ser
  "quédate cerca" + llamado por voz, y eso hay que decírselo al local antes de arrancar, no después.
  "No tener WhatsApp" y "no poder escanear un QR" son dos casos distintos con dos respuestas distintas.

Alternativas fuertes si prefieres otra: la 6 (frecuente; pero en v1 se corta, así que se puede asumir) y la 7
(El Libro; es más de producto e ingeniería que de diseño).

## 3.1 Las tres preguntas finales (decisión del 18/09/2026)

Las de § 3 salen del análisis del prototipo y se conservan como tal. **Las que van en la nota son estas
tres**: salieron de mirar las cinco pantallas del prototipo en primera instancia —antes de congelar el
alcance— y están más pegadas a lo que el corte de 4 horas construye de verdad. Cada una lleva la respuesta
que se asume si el diseñador no contesta a tiempo. Donde esta sección y § 3 difieran, manda esta.

### P1 · Cuando el anfitrión reordena la cola, ¿la posición que ve el comensal se actualiza al instante?

> Si un comensal figura como #3 y el anfitrión mueve a otro grupo por encima de él, ¿debe pasar a ver #4
> y recalcularse también su tiempo estimado?

- **Por qué importa.** Ese número es lo único que esa persona tiene en la mano mientras espera. Si sube,
  se lee como que alguien le pasó por delante: es la vía más corta a que se vaya o a que reclame en la
  puerta. La decisión define si el número es una posición real o una promesa, y eso cambia qué se guarda
  y qué se anima.
- **Respuesta asumida: el número visible nunca sube.** Se muestra el menor entre el valor calculado y el
  último valor ya mostrado. Cuando la cola avanza, el cálculo real alcanza al número mostrado y a partir
  de ahí vuelve a bajar solo — esa es la "normalización", y no se anuncia. Solo se anima cuando baja. El
  tiempo estimado sí se recalcula siempre: se muestra como aproximado ("≈ 28 min, depende de las mesas
  que se liberen"), así que moverse no rompe ninguna promesa.
- **En el corte de 4 horas esto no cuesta nada, porque el caso no se da.** Reordenar está fuera
  (09 § 2.3) y `groups_ahead` cuenta solo los `waiting` con `(sort_key, id)` menor: llamar a alguien de
  más abajo no sube el número de nadie, y los estados terminales solo restan. El número ya es monótono
  no creciente por construcción. La regla hay que tenerla escrita **antes** de implementar reordenar o
  la prioridad del frecuente, no después.
- **Cuando llegue reordenar**, el último valor mostrado se guarda en el turno y en el servidor
  (`displayed_ahead`), no en el navegador: el comensal recarga, cambia de navegador o vuelve desde el
  WhatsApp, y el dato del navegador se pierde. Estimación: incluida en el 1–1,5 d de "arrastrar para
  reordenar" de 05 § 2.
- **Matiz de vocabulario.** En v1 la pantalla no dice "puesto 3", dice "3 grupos antes que ti"
  (§ 4 punto 2 y el contrato de 09 § 5.1, campo `groups_ahead`). La regla es la misma; el número que no
  sube es ese.

### P2 · ¿La lista de espera debe contemplar zonas o ambientes (terraza, salón, barra)?

- **Por qué importa.** Una cola por zona no es una pantalla más: son N colas. Cambia la posición, el
  tiempo estimado, qué significa "un turno activo por teléfono", la vista del anfitrión y el reporte del
  cierre. Es de las cosas que salen caras si se agregan después, porque obliga a migrar turnos ya
  registrados y a redefinir métricas a mitad del piloto.
- **Respuesta asumida: en esta versión no hay preferencia de zona.** Una sola lista de espera por local,
  sin importar el ambiente ni el tipo de mesa. El único dato que entra en la decisión es el tamaño del
  grupo, y quién se sienta dónde lo decide el anfitrión, no el sistema (la asignación de mesas está
  fuera, 09 § 2.3).
- **Si el diseñador dice que sí**, la forma barata es un campo `zone` en `tickets` y la lista de zonas en
  `locations` — no tablas nuevas —, con posición y ETA calculadas por `(local, día, zona)` y la cola del
  anfitrión filtrable. Se mantiene **un turno activo por teléfono, local y día**, no uno por zona: si no,
  la misma persona se apunta en las tres colas y el reporte deja de significar nada. Estimación: 1–1,5 d,
  más lo que toque del reporte.
- **Riesgo declarado.** En un local con terraza, "sin zonas" significa que alguien puede rechazar la mesa
  que le toca. En v1 eso lo resuelve el anfitrión hablando, y el turno queda como «Se fue» o «No vino».

### P3 · Si el comensal cierra la página después de unirse, ¿debe poder recuperar su turno con el teléfono?

- **Por qué importa.** El link con el token es lo único que tiene, y se pierde al cerrar la pestaña,
  cambiar de navegador, entrar en incógnito o limpiar datos. Sin salida, esa persona vuelve a la puerta a
  preguntar —justo lo que el producto promete evitar— o se une otra vez y recibe un error que no entiende.
- **Respuesta asumida: sí.** La pantalla de alta incluye **«Ya estoy en la lista de espera»**: se ingresa
  el teléfono y se devuelve la espera activa **de ese local y de ese día de servicio**, con su token, de
  modo que el comensal cae en su página de turno con «Ya no voy» incluido. Si no hay espera activa, 404
  con un texto claro; la respuesta nunca dice "ese teléfono no está en la lista", para no confirmar ni
  negar nada sobre un número ajeno.
- **Lo que esto cambia respecto del análisis previo.** 09 § 2.1 O3 y 08 § 4b decían lo contrario: no
  revelar el token a quien solo conoce el teléfono, porque el QR de la puerta es público.
  **Decisión del 18/09/2026: prevalece la recuperación**, recogida en la enmienda 09 § 2.5. El argumento:
  adivinar un móvil completo y válido de alguien que además está en la cola de ese local hoy no es un
  ataque realista, y el costo de no tener salida es seguro y diario. El riesgo se declara, no se disimula.
- **La mejora conocida es OTP**: enviar un código al teléfono y devolver el token solo contra el código.
  Es la versión segura de esto mismo, pero depende del canal real de WhatsApp o SMS, que está fuera del
  corte (3 d y 1 d en 05 § 2), y añade en la puerta la fricción que se quiso quitar. Queda como deuda
  declarada (09 § 9), no como algo que se pasó por alto.
- **Lo que sí se hace gratis.** El teléfono se normaliza a E.164 con la región del local antes de buscar;
  solo se consideran turnos `waiting` o `called` del `service_date` actual; y el 409 al unirse deja de ser
  un callejón sin salida: su mensaje apunta a esta misma pantalla.

### Impacto en el corte

| | ¿Cambia el modelo? | ¿Cambia el contrato? | ¿Cambia el corte de 4 h? |
|---|---|---|---|
| P1 | No hoy; `displayed_ahead` solo cuando entre reordenar | No | No: el número ya no sube por construcción |
| P2 | No; `zone` queda sin escribir | No | No |
| P3 | No | **Sí**: `POST /api/public/locations/{code}/lookup` | **Sí**: un endpoint, una pantalla y un test (≈ 0,3 d) |

## 4. Qué le devolvería al diseñador
Cambios que propongo (siempre con alternativa):
1. Sin arrastrar para reordenar en el piloto → poder «Llamar» a cualquier fila (y "Subir al primero" si hace falta
   después). Con dos anfitriones y wifi malo los cambios se pisan, y a los de abajo les sube el número.
   Ojo al decirlo: es **aplazado, no rechazado**. La columna sort_key queda desde el día 1 justamente para
   que reordenar sea un cambio chico cuando toque.
2. En el celular: "N grupos antes que tú" + tiempo conservador, en vez de prometer que el número solo baja
   (a veces pasa antes alguien de atrás por el tamaño de mesa). Animación solo cuando baja.
3. En el WhatsApp: hora límite ("hasta las 21:24") en vez de "10 minutos"; texto neutro para que Meta lo apruebe
   como utility; se envía esta semana y puede cambiar si Meta lo rechaza. El remitente es Mesa247.
4. Un solo mensaje por grupo (el de "tu mesa está lista"): cada mensaje se cobra y la confirmación de alta ya se ve
   en pantalla.
5. El reporte por correo llega en la semana 3; los datos se guardan desde el primer día. Necesito saber quién lo
   recibe y a qué hora cierra cada local (Santiago va 2 horas adelante de Lima ahora).
Faltantes en el prototipo:
- Tablet: «No vino», «Se fue», «Deshacer», alta manual, estados "enviando…", "aviso no entregado" y "sin conexión".
- Comensal: el estado "¡Tu mesa está lista!" con los mismos botones del WhatsApp, estados finales, qué ve si el
  código del QR no existe o la lista está cerrada, el aviso de uso del teléfono, y qué ve **quien ya tiene un
  turno activo y vuelve a enviar el formulario** (no podemos mostrarle el turno solo porque sepa el teléfono).
- Formulario: rango de "¿Cuántos son?", prefijo según el país del local, ¿nombre o nombre + inicial?
- Encabezado de la tablet: definir "espera media" (con los números del prototipo no puede ser la espera actual)
  y si "en cola" incluye a los llamados.

## 4.1 Lo que le devuelvo, en orden de prioridad (decisión del 18/09/2026)

§ 4 es el inventario completo de lo que le diría. **Esto es lo que va en la nota**: dos cosas, en este
orden. El resto se menciona en una lista corta, no se desarrolla.

**1. Cómo se muestra la posición cuando el anfitrión reordena la cola.** Es el cambio principal que le
pediría revisar, y es el mismo asunto de § 3.1 P1: que el comensal no vea que "retrocedió" de puesto.
El número visible nunca sube; cuando la cola avanza, el valor real lo alcanza y vuelve a bajar solo.
Se anima solo hacia abajo. Alternativa si el diseñador quiere fidelidad por encima de todo: mostrar
únicamente el tiempo aproximado y no el número — pero entonces se pierde la pantalla que él mismo dibujó.

**2. WhatsApp entra después, no en la primera versión.** Primero se valida el flujo principal —registro,
cola y llamado— porque es la parte que reemplaza el cuaderno; si eso no funciona, el WhatsApp solo hace
más caro el fracaso. Lo que esto significa en concreto:

- **En lo que se entrega y se enseña** va un notificador falso que registra el aviso y el evento
  (09 § 2.1 O8). El flujo punta a punta se ve completo salvo el mensaje real.
- **En el piloto de 3 semanas WhatsApp sí entra** (3 d, 05 § 2), una vez validado el flujo principal.
  No se aplaza a "algún día": se aplaza dentro del plan, con su semana.
- **Por qué no se puede aplazar para siempre**, y conviene decirlo en la misma frase: la página del turno
  solo avisa si está abierta y a la vista; el polling se pausa con la pestaña oculta y no despierta un
  teléfono bloqueado. WhatsApp no es un canal más, es el único que alcanza a quien se fue a caminar
  (§ 3 P3). Mientras no esté, la regla operativa es "quédate cerca" + llamado por voz, y eso el local
  tiene que saberlo antes de arrancar, no después.
- La dependencia externa refuerza el orden: la plantilla la aprueba Meta y puede rechazarla. Empezar por
  ahí es empezar por lo único que no controlamos.

Lo demás de § 4 —hora límite en vez de "10 minutos", un solo mensaje por grupo, los faltantes del
prototipo— va como lista corta, sin desarrollar.

## 5. Cómo se lo diría (principios)
- Empezar por lo que sí sale y cuándo.
- Cada "no" con alternativa y con la razón del lado del comensal o del anfitrión, no de la tecnología.
- Separar "no para el piloto" de "no nunca".
- Priorizar: 3 cambios importantes; el resto en lista corta.
- Pedir decisiones concretas y con fecha. Mensaje asíncrono + 15 minutos de llamada.
- Reconocer lo bueno del diseño (es claro y resuelve el dolor real).

## 6. Borrador de referencia (reescríbelo con tu voz en la conversación de la nota)
    ¡Hola! Gracias por el encargo, el problema está clarísimo. Te cuento qué saldría para el piloto y qué necesito.

    Para el piloto (en 3 semanas):
    - Unirse por QR, y que el anfitrión pueda agregar a alguien a mano.
    - En el celular: su turno, tiempo estimado y «Ya no voy».
    - En la tablet: la cola con Llamar / Sentar / No vino, y el WhatsApp con los dos botones.
    - El reporte por correo llega la semana 3; los datos se guardan desde el día 1.

    Tres cambios que te propongo:
    1. Sin arrastrar en el piloto: con dos anfitriones y wifi malo se pisan, y a los de abajo les sube el número.
       En su lugar, «Llamar» funciona en cualquier fila, así priorizan al frecuente.
    2. En el celular, "N grupos antes que tú" y un tiempo aproximado: a veces pasa antes alguien de atrás por el
       tamaño de la mesa, y un número que sube se siente injusto.
    3. En el WhatsApp, "hasta las 21:24" en vez de "10 minutos" (el mensaje puede leerse tarde). Meta aprueba el
       texto y a veces lo rechaza, así que lo mando esta semana en versión neutra.

    Me faltan en el prototipo: «No vino» y «Deshacer» en la tablet, el alta manual, la pantalla de "tu mesa está
    lista" en el celular y el aviso de uso del teléfono.

    Y tres preguntas, que me salieron mirando las pantallas:
    1. Cuando reordenas la cola, ¿al comensal le sube el número? En la pantalla del celular dice "estás en el
       puesto 7"; si en la tablet subes a otro grupo, a esa persona le toca ver el 8. ¿Lo mostramos, o el
       número solo baja?
    2. ¿La lista tiene que separar terraza, salón y barra, o es una sola cola por local? Lo pregunto ahora
       porque una cola por ambiente no es una pantalla más: son varias colas, con su posición y su tiempo.
    3. Si el comensal cierra la página, ¿lo dejamos volver a su turno poniendo su teléfono? Es lo único que
       recuerda; el link se pierde al cerrar la pestaña.

    Si no me contestas a tiempo asumo: el número nunca sube, una sola cola por local, y sí se puede volver
    con el teléfono. Los tres supuestos están escritos y son fáciles de cambiar salvo el segundo.

    ¿Lo vemos 15 minutos mañana?

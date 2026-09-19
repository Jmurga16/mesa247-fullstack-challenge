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

    Y tres preguntas:
    1. ¿Llaman por orden de llegada o por la mesa que se libera?
    2. ¿Qué pasa al vencer los 10 minutos, y cómo cuenta quien dice «Ya no voy» después de ser llamado?
    3. ¿Qué hacemos con quien no puede escanear el QR o no tiene WhatsApp?

    ¿Lo vemos 15 minutos mañana?

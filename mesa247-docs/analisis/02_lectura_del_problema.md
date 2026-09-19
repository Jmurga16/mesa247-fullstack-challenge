# 02 · Lectura del problema

## 1. Qué exige el encargo (lectura entre líneas)
- El prototipo completo no es el objetivo: esas cinco pantallas se generan en una tarde. Lo que decide el
  resultado es el criterio: qué pantalla va primero, qué preguntar antes de escribir una línea y qué no se
  podrá cambiar después.
- El corte es deliberadamente incompleto y argumentado. Entregar las 5 pantallas equivale a no haber elegido.
- 4 horas de implementación: el alcance se ajusta a ese presupuesto, no al revés.
- "El WebSocket, la librería extra, la abstracción por si acaso" es una advertencia literal del encargo:
  cada dependencia adicional hay que justificarla o rechazarla con argumento.
- "Lo expuesto al público, pensado para el público": la pantalla del comensal y la API pública (seguridad,
  privacidad, red mala, textos claros).
- "Tests que cubren lo que se rompe, no lo que se ve": concurrencia, reintentos, estados inválidos, aislamiento
  entre locales, zonas horarias. No cobertura.
- Lo que separa un piloto que aguanta de una demo: idempotencia, dos anfitriones a la vez, caída un viernes,
  costo por mensaje, rollback, datos personales, plan B operativo.
- Rol: "llevar prototipos del Lead Product Designer a producción, muchas veces solo". El escenario es un lunes
  normal de ese puesto: el diseñador pregunta "¿Qué necesitas?" y espera respuesta.

## 2. Actores y su contexto real
- Comensal: en la vereda, con datos móviles, a veces con poca batería; no quiere instalar nada ni crear cuenta.
  Puede ser turista (número extranjero en Santiago), no tener WhatsApp o no tener smartphone.
- Anfitrión: tablet compartida en la puerta (el wifi malo también le pega a él), dos personas a la vez los viernes,
  manos ocupadas, se equivoca de fila. Necesita un toque por acción y poder corregir.
- Gerente o dueño: quiere saber cuánta gente se fue sin sentarse (la métrica que motiva el proyecto).
- Mesa247: necesita que el piloto demuestre valor en 3 semanas y que escale a 150 locales en 3 meses sin reescribir.
  Paga cada WhatsApp.
- Diseñador: dueño de la experiencia; espera que le digas qué necesitas y qué no conviene.
- El Libro (PHP): ya tiene locales, mesas y reservas. Su lista de espera fracasó por fricción (login + 4 pantallas).
  Lección: cada toque extra mata la adopción.

## 3. Del dolor a la funcionalidad (sirve para justificar el corte)
| Dolor del encargo | Qué lo resuelve | Cuándo |
|---|---|---|
| Se pierden nombres | Registro digital: QR + alta manual en la tablet | v1 |
| La gente se va sin avisar | «Ya no voy» (web y WhatsApp) + estados finales claros | v1 |
| El anfitrión no da abasto | Cola clara, 1 toque por acción, el comensal ve su turno (menos "¿cuánto falta?"), aviso automático | v1 |
| Priorizar frecuentes | Llamar a cualquier fila (v1) → "subir al primero"/arrastrar (v2) → frecuente automático (v3) | v1 parcial |
| Saber cuánta gente se fue | Eventos desde el día 1 (v1) → reporte por correo (semana 3) | v1 datos |

## 4. Hallazgos en el prototipo (material para la nota y para las preguntas al diseñador)
H1. La cola no es FIFO. La "Familia Rojas" (6 personas, puesto 3) ya fue llamada (21:12) mientras Carla (puesto 1,
    4 personas) y Jorge (puesto 2) siguen esperando. *Observación*: se llamó fuera de orden. *Inferencia*:
    probablemente se liberó una mesa para 6. No está demostrado que la causa sea el tamaño del grupo —por eso
    es la pregunta 1 al diseñador y no un supuesto.
    Consecuencia: la "posición" no es una promesa; el tiempo estimado depende del tamaño del grupo; el comensal puede
    ver que alguien "de atrás" pasa antes.
H2. El número puede subir. Si el anfitrión arrastra a un frecuente hacia arriba, todos los de abajo suben un puesto.
    El diseño solo contempla que "baja con animación".
H3. "Espera media 31 min" no cuadra con las filas. Hay 12 en cola; los 5 primeros llevan 34, 31, 28, 22 y 15 min.
    Si la lista está en orden de llegada —premisa necesaria y que un reordenamiento rompería—, los otros 7
    llegaron después y llevan ≤ 15 min, así que el promedio de la espera *actual* sería como máximo
    (34+31+28+22+15+7×15)/12 ≈ 19,6 min (y el de los 5 visibles, 26). Entonces "espera media" es otra métrica
    (¿espera real de los ya sentados hoy?). Hay que definirla.
H4. El reporte cuadra exacto: 97 + 31 + 14 = 142. Todo el que se une termina en exactamente un estado final.
    Implica estados terminales bien definidos y un cierre del día que resuelva a los que quedaron pendientes.
H5. Falta la acción "No vino". El reporte cuenta "No vinieron al ser llamados" (14), pero la tablet solo muestra
    Llamar y Sentar. ¿Se marca a mano? ¿Vence solo a los 10 minutos?
H6. "Tienes 10 minutos" es relativo al envío. El WhatsApp puede leerse tarde o llegar con demora. ¿Qué pasa en el
    minuto 11? No está definido. Mejor una hora absoluta ("hasta las 21:24").
H7. No hay alta manual. Quien no escanea (sin datos, sin smartphone, sin WhatsApp, número extranjero, adulto mayor)
    queda fuera. Si el anfitrión no puede agregarlo, el cuaderno sigue vivo y habrá dos fuentes de verdad:
    el piloto fracasa por adopción.
H8. No hay "Deshacer". Un viernes con 40 personas, llamar a la fila equivocada es seguro que pasa, y "Llamar" envía un
    WhatsApp que no se puede des-enviar.
H9. "Frecuente" no tiene origen. ¿Sale de El Libro? ¿De visitas previas por teléfono? ¿Lo marca el anfitrión?
    Implica identidad del cliente entre días y locales (dato personal + retención).
H10. La pantalla 2 no tiene el estado "te llamaron". Si el comensal tiene la página abierta, debería ver
     "¡Tu mesa está lista!" con los mismos dos botones del WhatsApp (canal gratis y sin plantilla).
H11. No hay aviso de privacidad ni consentimiento en la pantalla 1: se pide un teléfono y se va a enviar WhatsApp.
H12. Detalles del formulario: "¿Cuántos son?" sin límites (¿grupos de 15?); el formulario pide "Nombre" pero la
     tablet muestra "Carla M." (¿apellido o inicial?); el teléfono muestra +51 fijo (Santiago es +56; turistas).
H13. El remitente es "Mesa247 · Cuenta de empresa", no el restaurante: un número compartido por todos los locales.
     La plantilla necesita el nombre del local como variable, y la calidad del número (bloqueos, reportes) afecta a
     todos los locales a la vez.
H14. "12 en cola": ¿incluye a los ya llamados? La Familia Rojas sigue en la lista. Definirlo.
H15. Las pantallas no son el mismo instante (WhatsApp a Carla a las 21:14; en la tablet Carla aún no fue llamada y
     Rojas fue llamada a las 21:12). No es grave, pero confirma que el prototipo es ilustrativo, no especificación.
H16. El reporte "llega por correo al cierre": ¿a quién?, ¿a qué hora es el cierre?, ¿en qué zona horaria?
     Un viernes el servicio pasa la medianoche.
H17. El prototipo implica unos 3,5 min por grupo (puesto 7 → ≈ 25 min). Es un número **ilustrativo de una
     maqueta**, no una medición de capacidad del local: sirve para arrancar el estimador y para nada más.
     Se calibra con quoted_wait_min vs real en las primeras semanas.
H18. En la tablet, la "posición" incluye a los llamados (Rojas es el 3); para el comensal, "puesto" debería contar solo
     a los que esperan delante. Son dos números distintos.

## 5. Hechos del contexto que cambian el diseño (verificados el 15/09/2026)
- Dos zonas horarias desde el día 1: Lima UTC-5 (sin horario de verano) y Santiago UTC-3 (Chile adelantó la hora el
  domingo 6/09/2026; vuelve a UTC-4 en abril de 2027). Hoy hay 2 horas de diferencia. "Cierre del día" y "viernes"
  son locales, y el servicio del viernes termina el sábado de madrugada.
- Teléfonos con formatos distintos (+51, +56; luego +593 y +57): normalizar a E.164 desde el primer registro.
- WhatsApp cambia de precios justo antes del piloto: según Zendesk y varios BSP (aviso de agosto de 2026), desde el
  1/10/2026 Meta cobra también los mensajes de servicio y las plantillas utility enviadas dentro de la ventana de 24 h,
  que antes eran gratis.
  Varios proveedores (BSP) indican 1.000 mensajes de servicio gratis al mes por número y tarifas por país.
  Referencias publicadas por BSPs: Perú ~US$0,03 por utility tras el cambio (antes ~US$0,02); Chile ~US$0,02;
  Colombia ~US$0,0008. Verificar en el rate card oficial de Meta antes de citar cifras.
  Implicación: cada mensaje cuesta → política de "un mensaje por grupo".
- Plantillas: Meta las revisa (de minutos a ~24 h), puede rechazarlas y recategoriza como marketing (más caro) las
  que suenan promocionales. Es la dependencia externa del camino crítico: se envía el día 1.
- Cloud Run y WebSocket (documentación de Google): las conexiones son requests sujetas al timeout (máx. 60 min;
  el cliente debe reconectar), la afinidad de sesión es "best effort", sincronizar instancias exige un sistema externo
  (p. ej. Redis/Memorystore) y una instancia con sockets abiertos se factura como activa. Para colas de 40 no compensa.
- Datos personales:
  - Perú: Ley 29733 y su nuevo reglamento (DS 016-2024-JUS), vigente desde fines de marzo de 2025: refuerza
    consentimiento, exige oficial de datos personales en ciertos casos y notificar incidentes en 48 horas.
  - Chile: Ley 21.719, entra en vigencia en diciembre de 2026 (en pleno piloto o escalamiento).
  - Nombre + teléfono son datos personales: minimizar, avisar, retener poco.
- Mesa247 ("mesa 24/7") es una plataforma de reservas con sitios en Perú, Ecuador y Colombia; su web pública todavía
  es PHP. El Libro encaja con ese legado.

## 6. Riesgos principales
| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Plantilla de WhatsApp rechazada o demorada | Media | Alto: sin aviso no hay producto | Enviarla el día 1 con texto neutro utility y variantes; SMS de respaldo; la página del turno también avisa |
| Comensales sin QR/WhatsApp → cuaderno paralelo | Alta | Alto: adopción | Alta manual en la tablet; teléfono opcional |
| Wifi malo (comensal y tablet) | Alta | Medio | Polling con reintentos, idempotencia, banner "sin conexión", respuestas chicas; sugerir 4G para la tablet |
| Dos anfitriones sobre la misma fila | Alta los viernes | Medio: WhatsApp duplicado | Transiciones atómicas; el 2.º intento es un no-op; refresco inmediato |
| Tiempo estimado incorrecto | Alta | Medio: frustración | Estimación conservadora y redondeada; guardar prometido vs real para calibrar |
| Bugs de fecha y hora (medianoche, Santiago) | Media | Medio: reporte falso | UTC + zona IANA por local + fecha de servicio con corte 05:00; test |
| Abuso del QR (unirse desde casa, spam) | Media | Bajo/Medio | Rate limit, validar teléfono, un turno activo por teléfono, "Borrar" en la tablet |
| Fuga de datos (IDs adivinables) | Media | Alto: legal | Token aleatorio en el link; respuesta mínima; no loguear teléfonos |
| Turno ajeno tomado conociendo el teléfono | Media | Medio | El alta nunca devuelve el token de un turno existente (409); idempotencia por request_id, no por teléfono |
| Pendientes del servicio anterior bloquean el alta | Media | Medio | service_date dentro de active_key y en la consulta de la cola; cierre diario desde el día 1 del piloto |
| Costo de WhatsApp al escalar | Alta | Medio | Un mensaje por grupo; métricas por país; interruptor para apagar envíos |
| Calidad del número compartido | Baja/Media | Alto: todos los locales | Solo mensajes esperados, opt-in claro, sin promociones |
| Adopción del anfitrión | Media | Alto | Un toque por acción, sin login personal, botones grandes, capacitación de 15 min |
| Caída un viernes en hora punta | Baja | Alto | Alarmas técnicas y de negocio, rollback rápido, plan B en papel |

## 7. Supuestos globales (para escribir en la nota)
S1. El piloto es solo para walk-ins; las reservas siguen en El Libro, sin integración en v1.
S2. Los locales se cargan a mano (seed) con su id de El Libro como referencia; El Libro sigue siendo la fuente de verdad.
S3. La tablet se empareja una vez por local (token de dispositivo); no hay login personal.
S4. El anfitrión puede llamar a cualquier fila, no solo a la primera (así prioriza al frecuente o elige por mesa).
S5. Un teléfono tiene como máximo un turno activo por local **y día de servicio**. Ojo: es una regla de
    negocio, **no autenticación** — conocer un teléfono no da derecho al turno. Reintentar la *misma*
    solicitud (mismo request_id) devuelve el mismo turno; una solicitud distinta con ese teléfono recibe
    409 y nunca el token. Contra: quien reserva para dos familias con el mismo número queda bloqueado;
    lo cubre el alta manual sin teléfono.
S6. No hay asignación de mesas en v1: "Sentar" solo cierra el turno.
S7. El día de servicio termina a las 05:00 hora local.
S8. Un solo idioma (español) y un solo dominio para todos los países durante el piloto.
S9. El número de WhatsApp es de Mesa247 (compartido); el nombre del local va dentro de la plantilla.
S10. Retención: el teléfono se anonimiza a los 30 días (si después se quiere "frecuente", se pide consentimiento).

## 8. Cómo sabremos si el piloto funciona
- % de grupos que se van sin sentarse y % que no vienen al ser llamados, por local y día.
- Error del tiempo estimado (prometido vs real).
- Adopción: grupos registrados vs lo que antes anotaba el cuaderno; % de altas manuales.
- WhatsApp entregados, leídos y fallidos; costo por grupo sentado.
- Sin línea base no se puede afirmar una mejora: pedir a los locales que cuenten una semana antes con el cuaderno,
  o usar la primera semana del piloto como base.

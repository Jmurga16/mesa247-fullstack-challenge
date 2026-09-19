# 05 · Alcance, estimaciones y orden de ataque

## 1. Criterio del corte
La primera versión en producción es la que reemplaza al cuaderno sin dejar a nadie fuera y deja registrado todo lo que
el piloto necesita medir. Lo que mejora la experiencia pero no bloquea el piloto, va después.
Hay dos niveles que no hay que mezclar:
- El corte de 4 horas: el mínimo de punta a punta, bien hecho.
- El plan del piloto (3 semanas): lo que se documenta en la nota, con estimación y dependencia.

> **El alcance exacto del código está congelado en `09_alcance_y_plan_de_implementacion.md` § 2** (obligatorio / opcional /
> fuera). Este documento da las estimaciones y el plan del piloto. Si alguna fila de abajo contradice al 09,
> manda el 09.

## 2. Qué entra y qué no (con estimación)
Estimaciones en días ideales de una persona, para producción (no para el prototipo).

| Pieza | ¿Piloto? | ¿En el corte de 4 horas? | Estimación | Depende de | Por qué |
|---|---|---|---|---|---|
| P1 Unirse por QR | Sí | Sí | 0,5 d | dominio y QR impresos | es la entrada; sin esto no hay cola |
| Alta manual en la tablet | Sí | **Opcional 1** (solo si lo obligatorio está cerrado) | 0,5 d | — | sin esto el cuaderno sigue vivo |
| P2 Mi turno (grupos delante, ETA, «Ya no voy») | Sí | Sí, con polling (la animación es **opcional 4**) | 1 d | — | menos preguntas al anfitrión; canal gratis |
| Estado "te llamaron" en P2 | Sí | **Sí, obligatorio** | 0,1 d | — | es la mitad del flujo punta a punta |
| «Voy en camino» | Sí | **Opcional 2** | 0,15 d | — | misma lógica que los botones del WhatsApp |
| P4 Cola en la tablet (Llamar, Sentar, No vino, Se fue) | Sí | Sí | 1,5 d | — | núcleo operativo |
| Concurrencia de dos anfitriones e idempotencia | Sí | Sí | incluido arriba | — | viernes real |
| P3 WhatsApp real (plantilla, envío, webhook, estados) | Sí | No: notificador falso | 3 d | aprobación de Meta (de minutos a ~24 h, puede rechazar), credenciales, número | promesa central, pero con dependencia externa |
| SMS de respaldo con link | Sí (mínimo) | No | 1 d | API del proveedor contratado | plan B si Meta rechaza o el comensal no tiene WhatsApp |
| Emparejar tablets (token de dispositivo) | Sí | Token fijo en el seed | 0,5 d | — | sin login personal |
| Deshacer llamado / Re-llamar | Sí | **No** | 0,5 d | — | errores de viernes; el mensaje ya salió, así que "deshacer" es parcial por definición |
| P5 Reporte por correo al cierre | Sí (semana 3); la 1.ª semana, SQL manual | No (los datos sí se guardan) | 1,5–2 d | proveedor de correo, destinatarios, hora de cierre por local | los datos importan desde el día 1; el correo puede esperar |
| Arrastrar para reordenar | No | No | 1–1,5 d bien hecho (concurrencia + vista del comensal) | definición de experiencia | "Llamar" en cualquier fila cubre al frecuente |
| "Cliente frecuente" | No | No | 2–4 d | datos o API de El Libro, consentimiento | origen del dato indefinido |
| Infra de producción (Cloud Run, Cloud SQL, secretos, CI/CD, dominio) | Sí | No (se describe) | 2 d | accesos a GCP y DNS | — |
| Observabilidad y alarmas | Sí | No (se describe; logs estructurados sí) | 1 d | canal de guardia | — |
| Estimador calibrado con datos | No | No | 1–2 d | 2–3 semanas de datos del piloto | sin datos no hay calibración |
| Pausar o cerrar la lista por hoy | Después | No | 0,5 d | — | — |
| Panel para dar de alta locales | No (para 150 sí) | No | 2 d | — | escalar |

Resumen para la nota: núcleo ~4 d · tablets (emparejar, deshacer, re-llamar) 1 d · WhatsApp + SMS 4 d ·
infra y observabilidad 2,5–3 d · reporte 1,5–2 d · arranque del piloto 1 d → 14–15 días de trabajo en 15 hábiles.
No hay margen: por eso quedan fuera arrastrar y frecuente (3–5,5 d más), y el reporte por correo es la pieza que se
mueve si algo se atrasa (los primeros días se saca con una consulta SQL: los datos ya se guardan).

## 3. Plan del piloto en 3 semanas (para la nota)
Semana 1
- Día 1: enviar la plantilla a Meta (con 1–2 variantes de respaldo); pedir accesos (GCP, DNS, ids de locales en
  El Libro, API del proveedor SMS). Esqueleto del servicio desplegado en Cloud Run: el camino a producción primero.
- Días 2–4: núcleo (P1, P2, P4, alta manual, eventos, concurrencia) con sus tests.
- Día 5: cerrar el núcleo; Cloud SQL, secretos, CI/CD y dominio; primer despliegue real con datos falsos.
Semana 2
- Días 6–9: WhatsApp (envío, webhook, estados de entrega), SMS de respaldo, outbox + Cloud Tasks.
- Día 10: alarmas, logs estructurados y runbook.
Semana 3
- Día 11: emparejamiento de tablets, deshacer y re-llamar; prueba en un local en hora tranquila.
- Días 12–13: cierre del día y reporte por correo. **Se mueve el correo, no el cierre.** Son dos cosas:
  el cierre resuelve los pendientes y libera la clave activa (sin él, el turno del viernes bloquea al
  mismo teléfono el sábado), y el correo solo envía números. Si hay que recortar, el reporte de la
  primera semana sale con una consulta SQL a mano; el cierre puede ser un botón o un script manual,
  pero tiene que existir desde el primer día de piloto.
- Día 14: ajustes de la prueba, capacitación de 15 minutos a anfitriones, QRs impresos.
- Día 15: margen. Arrancar el piloto un día tranquilo (martes o miércoles), nunca un viernes.

Honestidad sobre el margen: son 14–15 días de trabajo en 15 hábiles, o sea **entre 1 y 0 días de holgura**.
No es un plan con margen, es un plan ajustado, y conviene decirlo así en la nota junto con qué se mueve
primero: el correo del reporte, después «Voy en camino» y deshacer/re-llamar, después el emparejamiento
de tablets (que puede salir con tokens cargados a mano para tres locales). Lo que no se mueve es WhatsApp,
porque depende de Meta y no del equipo.
Dependencias críticas: aprobación de la plantilla; accesos a GCP y DNS; tablets y conectividad en la puerta;
lista de locales de El Libro. Si Meta rechaza la plantilla, el piloto arranca con SMS y la página del turno.

## 4. Plan de las 4 horas (orden de ataque)
| Bloque | Tiempo | Conversación | Qué haces | Sale |
|---|---|---|---|---|
| 0–1 | 0:00–0:30 | A · nota | huecos, 3 preguntas, supuestos, corte, estados y contrato | decisiones + esquema |
| 2 | 0:30–1:50 | B · backend | proyecto, modelos, transiciones, endpoints, notificador falso, 6 tests, seed | pytest en verde |
| 3 | 1:50–3:05 | C · frontend | unirse, mi turno (polling), tablet (acciones) | flujo de punta a punta |
| 4 | 3:05–3:20 | B y C | README y prueba desde un clon limpio | README probado |
| 5 | 3:20–4:00 | A · nota | nota final (2 páginas), devolución al diseñador, producción | nota |

Son 4:00 **sin margen**, y el bloque 2 es el que se desborda: son ~11 endpoints, 4 modelos y 6 tests en
80 minutos. Lo realista es 4:30–5:00 en total, y conviene anotar el tiempo real por bloque.
El punto de control es a las 1:50 — si el backend no está con pytest en verde, se cortan los opcionales
del frontend antes de empezarlo, no a las 3:00.

Por qué este orden
1. Preguntas y datos antes que código: sin las decisiones tomadas, el código se rehace.
2. Contrato de API antes que back y front: cada parte avanza sin adivinar.
3. Backend con tests de fallos antes que el front: lo que se rompe un viernes vive en el back.
4. Front mínimo que demuestre el flujo, sin pulir.
5. README probado desde cero: el proyecto tiene que levantarse en 5 minutos en una máquina limpia.
6. La nota al final, pero con el borrador del inicio: las decisiones ya estaban tomadas; solo se redactan.

Si vas atrasado, el orden de corte está en `09_alcance_y_plan_de_implementacion.md` § 8.5. En resumen: primero los cuatro
opcionales (que ya están fuera de la definición de listo), después los tests de segunda prioridad, después
`/remove`, después la espera media del encabezado.
Nunca cortes: los seis tests no negociables, el README probado, el aislamiento entre locales y la nota.

## 5. Cuándo parar (definición de «listo» del corte)
La lista completa está en `09_alcance_y_plan_de_implementacion.md` § 8.6. Lo esencial:
- Con el README, en una máquina limpia y en 5 minutos o menos: back y front arriba, 3 locales sembrados,
  links impresos en la consola.
- Flujo: unirse desde el celular (o la vista móvil del navegador) → aparece en la tablet → Llamar → la página
  del turno muestra "¡Tu mesa está lista!" con la hora límite → «Ya no voy» se refleja en la tablet →
  Sentar o No vino. (**«Voy en camino» NO está en esta lista**: es opcional.)
- Reintentar el mismo formulario devuelve el mismo turno; el mismo teléfono desde otro navegador **no**
  entrega el turno ajeno.
- Dos pestañas de tablet, Llamar en ambas → un solo aviso en el log.
- pytest en verde con los seis tests no negociables.
- Nada más. Lo que falte va a la nota con su estimación.

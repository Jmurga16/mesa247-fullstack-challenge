# 04 · Diez líneas sobre algo que llevé a producción

Lo último que llevé solo a producción es esta misma lista de espera: corre en mi VPS,
mesa247.devkora.com, y no en Cloud Run porque el servidor ya estaba pagado. Corté lo que no entraba en 4
horas: WhatsApp real quedó como un aviso falso, y afuera reordenar la cola, las zonas, el panel de
administración y el WebSocket que me proponía la IA. Lo que salió mal todo lo encontraron los test, lo vi yo
probando: solo se registraba la primera persona, porque guardé la llave de idempotencia en el navegador
por local y la segunda reenviaba la del primero, y entraba al turno de otro. Mis 17 pruebas de navegador
estaban en verde, pero rellenaban el formulario de un golpe y nunca tecleaban, así que no valían. Al
desplegar me enteré de que ufw no filtra los puertos que publica Docker, y el 3306 quedó abierto. Si lo
volviera a hacer desplegaría el primer día y no el último, y probaría escribiendo, no rellenando: que el
código funcione no es lo mismo a que una persona pueda usarlo un viernes a las 9 de la noche.

# 01 · El encargo y sus requisitos, en formato checklist

Fuente: https://prueba-fullstack-mesa247.pages.dev/ (leída el 15/09/2026). Resumen fiel, no copia literal.

## Restricciones de trabajo
- Stack pedido: Python + FastAPI en el backend, React + TypeScript en el frontend, MySQL o SQLite en local.
- Esfuerzo de implementación: 4 horas. El alcance se recorta para caber ahí, no al revés.
- No hay diseñador disponible: hay que escribir las 3 preguntas que se le harían antes de empezar y qué se asume en cada una.
- No se construye todo: se elige el corte que saldría primero a producción y se explica qué se hace con el resto. Un prototipo completo equivale a no haber elegido.
- Donde falte información: supuesto razonable y explícito.

## Qué debe cubrir la nota técnica (1–2 páginas)
[ ] Las 3 preguntas al diseñador + el supuesto de cada una.
[ ] Qué se construye primero y qué se corta, con una estimación para cada parte.
[ ] El modelo de datos (vale un esquema a mano).
[ ] Qué se le devolvería al diseñador y cómo se le diría.
[ ] Qué decisiones no se van a poder cambiar después.
[ ] Cómo se lleva a producción: el despliegue, qué alarma se pone y cómo se detecta una caída un viernes a las 9 de la noche.

## Qué debe cumplir el código
[ ] Repositorio con FastAPI y React con TypeScript.
[ ] Punta a punta mínimo: un comensal se une a la cola → el anfitrión la ve → llama al siguiente.
[ ] README para levantarlo en 5 minutos.
[ ] Tests solo de lo que importa: lo que se rompe, no lo que se ve.
[ ] MySQL o SQLite para correrlo en local (lo que sea más rápido).
[ ] Lo expuesto al público, pensado para el público (seguridad, privacidad, red mala, textos claros).

## Registro del trabajo con IA
[ ] Conversaciones separadas por parte: la nota, el backend, el frontend.
[ ] Completas y sin editar; si se recorta algo personal, declararlo.
[ ] Nota literal del encargo: la IA va a proponer "el WebSocket, la librería extra, la abstracción por si acaso".
      Los rechazos se argumentan y quedan registrados.

## El encargo (mensaje del Lead Product Designer, lunes 10:04)
Problema: restaurantes con mucho walk-in tienen los viernes colas de 30 a 40 personas anotadas en un cuaderno;
se pierden nombres, la gente se va sin avisar y el anfitrión no da abasto.
Pide una lista de espera digital:
1. El comensal escanea un QR en la puerta, pone nombre, teléfono y cuántos son, y entra a la cola.
2. En su celular ve su posición en vivo (baja con animación) y un tiempo estimado.
3. Cuando su mesa está lista le llega un WhatsApp con dos botones: «Voy en camino» y «Ya no voy».
4. El anfitrión ve la cola en su tablet, puede arrastrar para reordenar (a veces priorizan a un frecuente) y toca «Llamar».
5. Al cierre del día, un reporte: cuánta gente se fue sin sentarse.
Piloto: 3 locales — La Terraza Azul y Cuatro Vientos (Lima), Casa Mediterránea (Santiago) — en tres semanas.
Cierra con: "¿Qué necesitas?"

## Prototipo (5 pantallas): datos visibles
1. Comensal · Unirse: "La Terraza Azul / Lista de espera · hoy"; Nombre (Carla); Teléfono (+51 987 654 321);
   ¿Cuántos son? (– 4 +); botón «Unirme a la cola». Nota: se abre al escanear el QR de la puerta.
2. Comensal · Tu turno: "Estás en el puesto 7"; "Tiempo estimado ≈ 25 min"; "Te avisaremos por WhatsApp cuando tu
   mesa esté lista"; botón «Ya no voy». Nota: el número baja en vivo, con animación.
3. Comensal · WhatsApp: remitente "Mesa247 · Cuenta de empresa"; "¡Carla, tu mesa en La Terraza Azul está lista!
   Tienes 10 minutos para acercarte a la entrada." (21:14); botones «Voy en camino» / «Ya no voy».
   Nota: los botones actualizan la cola del anfitrión.
4. Anfitrión · Cola en la tablet: "La Terraza Azul · viernes — 12 en cola · espera media 31 min".
   Filas (⋮⋮ · posición · nombre · personas · esperando · estado/acción):
     1  Carla M.       4 pers.  34 min                   [Llamar]
     2  Jorge P.       2 pers.  31 min  (Frecuente)      [Llamar]
     3  Familia Rojas  6 pers.  28 min  Llamado 21:12    [Sentar]
     4  Andrés V.      2 pers.  22 min                   [Llamar]
     5  Lucía y Ana    2 pers.  15 min                   [Llamar]
   Nota: arrastrar ⋮⋮ para reordenar · «Llamar» envía el WhatsApp.
5. Reporte del día: "Viernes 11 de septiembre — La Terraza Azul · cierre del día";
   Se unieron 142 · Se sentaron 97 · Se fueron sin sentarse 31 · No vinieron al ser llamados 14 · Espera media 34 min.
   Nota: llega por correo al cierre.

## Lo que se sabe del sistema
- Stack: Python + FastAPI en el backend, React + TypeScript en el frontend, MySQL. Todo en Google Cloud, sobre Cloud Run.
- Países: Perú, Chile, Ecuador y Colombia. Piloto: dos locales en Lima y uno en Santiago.
- "El Libro": el sistema actual, más antiguo, en PHP. Tiene locales, mesas y reservas. También una lista de espera que
  casi nadie usa: exige iniciar sesión y pasar por cuatro pantallas.
- Anfitriones: tablets compartidas en la entrada; los viernes hay dos atendiendo a la vez.
- La puerta: el wifi es malo; el comensal usa sus datos móviles.
- WhatsApp: cuenta Business; los mensajes que inicia el negocio necesitan plantillas aprobadas por Meta (que a veces las
  rechaza) y se cobran por mensaje, con tarifa distinta por país. También hay un proveedor de SMS contratado.
- Escala: 3 locales en el piloto, hasta 40 personas en cola por local un viernes; si funciona, 150 locales en tres meses.

## La tarea
Decidir qué sale primero a producción para el piloto, construirlo y explicar el resto en la nota técnica.

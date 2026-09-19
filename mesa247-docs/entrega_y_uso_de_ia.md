# Entrega y uso de IA

Qué se entrega, bajo qué restricciones, y cómo se declara el trabajo hecho con IA.
Está aquí porque explica decisiones del proyecto que de otro modo parecen arbitrarias: por qué el
alcance se corta donde se corta, por qué existe el registro de conversaciones y por qué esta carpeta
no forma parte del repositorio entregado.

No incluye preparación de la entrevista ni el guion del correo: eso no es materia del proyecto.

## 1. Restricciones

- Esfuerzo de implementación: **4 horas**. El alcance se recorta para caber ahí, no al revés
  (alcance congelado en [09 § 2](analisis/09_alcance_y_plan_de_implementacion.md)).
- Plazo: viernes 18/09/2026, 12:00 hora de Lima.
- Sin capturas ni presentaciones: la nota va en texto o PDF.
- El repositorio se envía a talento@mesa247.pe: público o con acceso para esa dirección.

## 2. Qué se entrega

**Nota técnica (1–2 páginas).** Escrita, en [`entregables/01_nota_tecnica.md`](entregables/01_nota_tecnica.md):
ese es el documento que se envía. La tabla dice de dónde sale cada sección y dónde está el desarrollo largo
que **no** entra en las dos páginas.

| Sección | Líneas | Dónde está el material |
|---|---|---|
| Las 3 preguntas al diseñador + supuesto de cada una | ~12 | [07 § 3.1](analisis/07_disenador_preguntas_y_devolucion.md) (las que se envían; § 3 son las candidatas del análisis) |
| Qué se construye y qué se corta, con estimación | ~18 | [05 § 2](analisis/05_alcance_estimaciones_y_orden.md) · [09 § 2](analisis/09_alcance_y_plan_de_implementacion.md) |
| Modelo de datos (4 tablas y los estados, sin DDL) | ~12 | [04](analisis/04_modelo_de_datos.md) |
| Qué se le devuelve al diseñador y cómo | ~10 | [07 § 4.1](analisis/07_disenador_preguntas_y_devolucion.md) (las dos prioridades; § 4 es el inventario completo) |
| Lo difícil de deshacer (cinco decisiones) | ~8 | [03 § 6.1](analisis/03_arquitectura_y_decisiones.md) (las cinco de la nota; § 6 es el catálogo por niveles) |
| Producción: despliegue, 4 alarmas, viernes 9 pm | ~15 | [06 § 0](analisis/06_produccion_y_tests.md) (la respuesta corta; el detalle en § 1, § 3 y § 4) |
| **Total** | **~75** | |

El presupuesto de líneas importa: este material da para diez páginas y la nota son dos. Todo lo que
no entra se menciona con su estimación y su dependencia, no se desarrolla.

**El código.** Requisitos que salen del encargo, no de preferencia propia:

- [ ] FastAPI + React con TypeScript; MySQL o SQLite en local.
- [ ] Punta a punta: un comensal se une → el anfitrión la ve → llama al siguiente.
- [ ] README que levante el proyecto en 5 minutos, probado desde un clon limpio (bash y PowerShell).
- [ ] Tests de lo que se rompe, no de lo que se ve ([09 § 7](analisis/09_alcance_y_plan_de_implementacion.md)).
- [ ] `.env.example`, ningún secreto, dependencias con versión fija, `.gitignore` (venv, node_modules, *.db, .env).
- [ ] Commits pequeños, con mensajes que cuenten la historia.
- [ ] **Esta carpeta `mesa247-docs` no va en el repositorio entregado.**

**Las conversaciones con IA.** Tres exportaciones separadas —nota, backend y frontend—, completas y
sin editar. Si se recorta algo personal, se declara el recorte. Ver
[conversaciones/README.md](conversaciones/README.md).

**Una reflexión de 10 líneas** sobre algo propio que llegó a producción. Es personal y se escribe a
mano; no vive en este repositorio.

## 3. Honestidad sobre el uso de IA

El encargo permite usar IA sin límite y pide las conversaciones como parte de la entrega. La postura
del proyecto:

- **El análisis previo también se hizo con IA** y contiene decisiones que se usan. Se declara, no se
  omite: está en [conversaciones/prompt_inicial.md](conversaciones/prompt_inicial.md) y en el
  [registro](conversaciones/registro.md).
- **Se declara el tiempo real invertido**, aunque pase de 4 horas, separando análisis previo,
  implementación y redacción. El plan de [09 § 8.4](analisis/09_alcance_y_plan_de_implementacion.md)
  son 4:00 sin margen y lo realista es 4:30–5:00.
- **Se declara qué generó la IA y qué se revisó o cambió.** Los rechazos con argumento están en
  [03 § 7](analisis/03_arquitectura_y_decisiones.md); los del propio trabajo, en el registro.
- **Se declara lo que no se alcanzó** y cómo se haría: deuda conocida en
  [09 § 9](analisis/09_alcance_y_plan_de_implementacion.md).
- **Los límites de lo entregado se dicen antes de que los pregunten**: el test de doble llamado no
  prueba concurrencia real, el ETA es una heurística sin calibrar, el notificador falso no prueba
  entrega, y las tarifas de WhatsApp del 1/10/2026 no están confirmadas en el rate card de Meta.

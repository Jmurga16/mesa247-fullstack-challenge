# Análisis previo

Antes de iniciar el proyecto, utilicé dos modelos para tener dos puntos de vista: uno para analizar la prueba y plantear una solución, y otro para revisar la propuesta y detectar posibles problemas.

## 1. Análisis inicial — Claude Opus Extra

Quiero que me ayudes a analizar esta prueba técnica antes de empezar a programar: https://prueba-fullstack-mesa247.pages.dev/

Revisa el enunciado y el prototipo para entender qué piden, qué dudas hay y qué conviene construir primero. Necesito separar lo que haría para la primera versión y lo que puedo implementar en la prueba, dejando claro qué queda fuera y por qué.

Propón una arquitectura sencilla con el stack indicado, el modelo de datos, los estados de los turnos y los endpoints principales. Considera problemas como acciones simultáneas de los anfitriones,reintentos, mala conexión, datos personales y locales en distintas zonas horarias. Incluye las tres preguntas al diseñador, los tests
importantes y cómo llevaría esto a producción.

Distingue los requisitos de tus supuestos y propón un alcance con prioridades y un orden de implementación realista. Organiza el resultado en documentos .md que pueda consultar mientras desarrollo, sin repetir información ni escribir código de la aplicación todavía.

## 2. Auditoría del análisis — GPT Astra High

Ya tengo un análisis previo de esta prueba técnica: https://prueba-fullstack-mesa247.pages.dev/

Quiero que lo revises como una segunda opinión antes de empezar a programar. Lee los documentos y contrástalos con el enunciado y el prototipo.

Busca contradicciones, requisitos que se hayan pasado por alto, supuestos sin justificar y complejidad innecesaria. Revisa si la arquitectura, el modelo de datos, los estados y los endpoints son coherentes entre sí y si el alcance es realista para la prueba.

No des por correcta la propuesta anterior, pero tampoco propongas cambios solo por hacer algo distinto. Explica los problemas que encuentres y cómo los resolverías.

Guarda la revisión en auditoria/, en documentos .md. Termina con una recomendación de alcance: qué mantener, qué corregir y qué dejar fuera, junto con los pendientes que debería resolver antes de implementar. Por ahora no modifiques los documentos originales ni escribas código de la aplicación.
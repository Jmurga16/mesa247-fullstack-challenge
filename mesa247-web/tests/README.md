# Pruebas funcionales integradas

`functional.py` abre Chromium con vistas de celular (390 × 844) y tablet (1024 × 768),
ejecuta Vite y FastAPI reales en puertos libres y siembra los tres locales en SQLite temporal.
Detiene sus servidores y elimina esa base al terminar. No usa la base ni las sesiones de desarrollo.

Requiere las dependencias de API y web instaladas según sus READMEs, más Playwright:

```powershell
# Desde la raíz del repositorio
.\mesa247-api\.venv\Scripts\python.exe -m pip install -r mesa247-web/tests/requirements.txt
.\mesa247-api\.venv\Scripts\python.exe -m playwright install chromium
.\mesa247-api\.venv\Scripts\python.exe mesa247-web/tests/functional.py
```

```bash
# Desde la raíz del repositorio
mesa247-api/.venv/bin/python -m pip install -r mesa247-web/tests/requirements.txt
mesa247-api/.venv/bin/python -m playwright install chromium
mesa247-api/.venv/bin/python mesa247-web/tests/functional.py
```

La ejecución dura aproximadamente cuatro minutos. Devuelve código 1 si encuentra fallos y continúa
con los demás escenarios. El JSON de resultados, los logs y las capturas se guardan en
`.artifacts/functional/`, excluido de Git. Los datos son sintéticos; los logs pueden contener tokens
de esos turnos temporales. Una nueva ejecución sobrescribe resultados y capturas del mismo nombre.

Los 17 escenarios cubren alta, polling entre dispositivos, llamado y asiento, parada del polling
terminal, altas distintas desde un navegador, duplicados y recuperación, validación y tamaño del grupo,
teléfonos de Chile y extranjeros, cancelación, nuevo registro, acciones del anfitrión, reporte y fecha,
aislamiento, tokens inválidos, reintentos, revocación de sesión, cuenta regresiva y fallos de red.

El negocio usa respuestas reales de la API. Para reproducir fallos se descarta una respuesta de alta
ya confirmada por el servidor, se corta la red del navegador o se detiene el proceso de la API durante
30 segundos. La prueba de cuenta regresiva adelanta 61 segundos el reloj del navegador sin modificar
los tiempos del servidor. La caída de API espera otros 65 segundos después del reinicio para cubrir
el backoff máximo documentado.

El doble llamado usa dos tablets con la misma sesión y una fila aún sin refrescar. La simultaneidad
de dos conexiones a la base la comprueban los tests de concurrencia del backend.

Los resultados y los fallos abiertos del 19/09/2026 están en el
[informe funcional](../../mesa247-docs/auditoria/04_pruebas_funcionales_integradas.md).
La suite conserva las expectativas del producto: no convierte los fallos conocidos en tests aprobados.

# Imagen de la API. Se construye en el VPS; no hace falta Python en local.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY seed.py ./

# Sin privilegios: la API no escribe nada en disco cuando usa MySQL.
RUN useradd --uid 10001 --no-create-home mesa247 && chown -R mesa247:mesa247 /app
USER mesa247

EXPOSE 8000

# --no-access-log a propósito: las rutas públicas llevan el token del turno
# (/api/public/tickets/{token}) y un access log lo dejaría escrito en disco.
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

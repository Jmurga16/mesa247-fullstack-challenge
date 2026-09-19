# Construye el frontend y lo sirve con Caddy, que además hace de proxy a la API
# y gestiona el certificado TLS. Mismo origen para /api: por eso el frontend no
# necesita CORS ni una URL de API configurable.
FROM node:22-alpine AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# `npm run build` incluye `tsc --noEmit`: si el tipado falla, la imagen no sale.
RUN npm run build

FROM caddy:2-alpine
COPY --from=build /src/dist /srv

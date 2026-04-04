FROM node:lts-trixie

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY index.mjs ./
COPY telemetry.mjs ./

EXPOSE 8080

CMD ["node", "--import=/app/telemetry.mjs", "/app/index.mjs"]
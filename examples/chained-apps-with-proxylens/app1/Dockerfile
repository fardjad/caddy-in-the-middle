FROM node:lts-trixie

WORKDIR /app

COPY package.json /app/package.json
COPY package-lock.json /app/package-lock.json
RUN npm ci

COPY app.js /app/app.js
COPY config.js /app/config.js
COPY otel.js /app/otel.js

EXPOSE 8080

CMD ["node", "/app/app.js"]
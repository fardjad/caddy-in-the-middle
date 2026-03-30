import process from "node:process";

import { appConfig } from "./config.js";
import { startOpenTelemetry } from "./otel.js";

startOpenTelemetry();

// Fastify must load after OTEL registration so the instrumentation can patch it.
const { default: Fastify } = await import("fastify");

const app = Fastify({ logger: false });

app.get("/", async (_req, reply) => {
  try {
    const response = await fetch(appConfig.service2BaseUrl, {
      method: "GET",
      headers: {
        accept: "application/json",
      },
      signal: AbortSignal.timeout(10_000),
    });

    if (!response.ok) {
      throw new Error(`received status ${response.status}`);
    }

    return {
      service: appConfig.serviceName,
      message: `${appConfig.serviceName} called app2`,
      downstream: await response.json(),
    };
  } catch (error) {
    reply.code(502);
    return {
      service: appConfig.serviceName,
      error: `downstream request failed: ${error.message}`,
    };
  }
});

try {
  await app.listen({ host: appConfig.bind, port: appConfig.port });
} catch (error) {
  app.log.error(error);
  process.exit(1);
}

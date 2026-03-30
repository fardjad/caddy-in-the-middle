import { AsyncLocalStorageContextManager } from "@opentelemetry/context-async-hooks";
import {
  CompositePropagator,
  W3CBaggagePropagator,
  W3CTraceContextPropagator,
} from "@opentelemetry/core";
import { registerInstrumentations } from "@opentelemetry/instrumentation";
import { FastifyInstrumentation } from "@opentelemetry/instrumentation-fastify";
import { HttpInstrumentation } from "@opentelemetry/instrumentation-http";
import { UndiciInstrumentation } from "@opentelemetry/instrumentation-undici";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { NodeTracerProvider } from "@opentelemetry/sdk-trace-node";
import { ATTR_SERVICE_NAME } from "@opentelemetry/semantic-conventions";

import { appConfig } from "./config.js";

export const startOpenTelemetry = () => {
  const provider = new NodeTracerProvider({
    resource: resourceFromAttributes({
      [ATTR_SERVICE_NAME]: appConfig.serviceName,
    }),
  });

  provider.register({
    contextManager: new AsyncLocalStorageContextManager(),
    propagator: new CompositePropagator({
      propagators: [new W3CTraceContextPropagator(), new W3CBaggagePropagator()],
    }),
  });

  registerInstrumentations({
    instrumentations: [
      new HttpInstrumentation(),
      new FastifyInstrumentation(),
      new UndiciInstrumentation(),
    ],
  });
};

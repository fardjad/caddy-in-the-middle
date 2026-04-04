import { register } from 'node:module';
import { pathToFileURL } from 'node:url';
import { FastifyOtelInstrumentation } from "@fastify/otel";
import { getNodeAutoInstrumentations } from "@opentelemetry/auto-instrumentations-node";
import { NodeSDK } from "@opentelemetry/sdk-node";

register('@opentelemetry/instrumentation/hook.mjs', pathToFileURL('./'));

const sdk = new NodeSDK({
	instrumentations: [
		getNodeAutoInstrumentations(),
		new FastifyOtelInstrumentation({ registerOnInitialization: true }),
	],
});

sdk.start();

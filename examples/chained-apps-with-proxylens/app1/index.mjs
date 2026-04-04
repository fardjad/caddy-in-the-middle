import process from "node:process";
import Fastify from "fastify";

const HOST = process.env.HOST ?? "0.0.0.0";
const PORT = Number(process.env.PORT ?? "8080");
const serviceName = process.env.OTEL_SERVICE_NAME ?? "app1";
const service2BaseUrl = process.env.SERVICE2_BASE_URL;

const app = Fastify({ logger: true });

app.get("/", async (_req, reply) => {
	try {
		const response = await fetch(service2BaseUrl, {
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
			service: serviceName,
			message: `${serviceName} called app2`,
			downstream: await response.json(),
		};
	} catch (error) {
		reply.code(502);
		return {
			service: serviceName,
			error: `downstream request failed: ${error.message}`,
		};
	}
});

await app.listen({
	host: HOST,
	port: PORT,
});

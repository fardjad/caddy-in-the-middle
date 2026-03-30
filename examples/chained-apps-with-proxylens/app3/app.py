from __future__ import annotations

from flask import Flask
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

APP_BIND = "0.0.0.0"
APP_PORT = 8080
APP_NAME = "app3"

app = Flask(__name__)
trace.set_tracer_provider(
    TracerProvider(resource=Resource.create({"service.name": APP_NAME}))
)
FlaskInstrumentor().instrument_app(app)


@app.get("/")
def index() -> tuple[dict[str, object], int]:
    return {
        "service": APP_NAME,
        "message": f"hello from {APP_NAME}",
    }, 200


if __name__ == "__main__":
    app.run(
        host=APP_BIND,
        port=APP_PORT,
        debug=False,
    )

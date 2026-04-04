import os
from flask import Flask

SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "app3")

app = Flask(__name__)


@app.get("/")
def index():
    return {
        "service": SERVICE_NAME,
        "message": f"hello from {SERVICE_NAME}",
    }, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)

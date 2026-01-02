import pip_system_certs.wrapt_requests

pip_system_certs.wrapt_requests.inject_truststore()

from flask import Flask, send_file, request, jsonify
import subprocess
import fcntl
import os
import socket
import requests

app = Flask(__name__)


@app.route("/", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def get_info():
    request_data = {
        "method": request.method,
        "url": request.url,
        "host": request.host,
        "remote_addr": request.remote_addr,
        "headers": dict(request.headers),
        "args": request.args.to_dict(flat=False),
        "cookies": request.cookies,
    }
    return (
        jsonify({"hostname": socket.gethostname(), "request_data": request_data}),
        200,
    )


@app.route("/health", methods=["GET"])
def get_health():

    checks = [
        ("https://citm.internal:3858", 404),
        ("https://supervisor.citm.internal:3858", 200),
        ("https://mitm.citm.internal:3858", 200),
    ]

    results = []

    for url, expected_status in checks:
        try:
            resp = requests.get(
                url,
                timeout=2,
            )
            ok = resp.status_code == expected_status
            results.append(
                {
                    "url": url,
                    "expected": expected_status,
                    "actual": resp.status_code,
                    "ok": ok,
                }
            )
        except Exception as e:
            results.append(
                {
                    "url": url,
                    "expected": expected_status,
                    "error": str(e),
                    "ok": False,
                }
            )

    if all(r["ok"] for r in results):
        return jsonify(status="ok", checks=results), 200

    return jsonify(status="unhealthy", checks=results), 503


@app.route("/har", methods=["GET"])
def get_har():
    lock_path = "/mitm-dump/har.lock"
    flow_path = "/mitm-dump/dump.flow"
    har_path = "/mitm-dump/dump.har"

    with open(lock_path, "w") as lock_file:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return jsonify({"error": "HAR generation already in progress"}), 409

        subprocess.check_call(
            [
                "mitmdump",
                "-nr",
                flow_path,
                "--set",
                f"hardump={har_path}",
            ]
        )

    return send_file(har_path, mimetype="application/json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

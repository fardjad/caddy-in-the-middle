import pip_system_certs.wrapt_requests

pip_system_certs.wrapt_requests.inject_truststore()

from flask import Flask, send_file, request, jsonify
import subprocess
import fcntl
import socket
import requests

app = Flask(__name__)


def run_supervisorctl(args):
    result = subprocess.run(
        ["supervisorctl", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def parse_status_lines(raw_output):
    services = []
    for line in raw_output.splitlines():
        parts = line.split(None, 2)
        if len(parts) < 2:
            continue
        name = parts[0]
        state = parts[1]
        description = parts[2] if len(parts) == 3 else ""
        services.append(
            {
                "name": name,
                "state": state,
                "description": description.strip(),
            }
        )
    return services


@app.route("/supervisor", methods=["GET"])
def get_ui():
    return send_file("supervisor.html")


@app.route("/supervisor/api/services", methods=["GET"])
def list_services():
    result = run_supervisorctl(["status"])
    if result.returncode != 0:
        return (
            jsonify({"error": "Failed to read supervisor status", "details": result.stderr}),
            502,
        )
    services = parse_status_lines(result.stdout)
    return jsonify({"services": services, "hostname": socket.gethostname()}), 200


@app.route("/supervisor/api/services/<name>/<action>", methods=["POST"])
def service_action(name, action):
    if action not in {"start", "stop", "restart"}:
        return jsonify({"error": "Unsupported action"}), 400
    result = run_supervisorctl([action, name])
    if result.returncode != 0:
        return (
            jsonify(
                {
                    "error": "Supervisor action failed",
                    "details": result.stderr or result.stdout,
                }
            ),
            502,
        )
    return jsonify({"status": "ok", "output": result.stdout}), 200


@app.route("/supervisor/api/services/restart-all", methods=["POST"])
def restart_all():
    result = run_supervisorctl(["restart", "all"])
    if result.returncode != 0:
        return (
            jsonify(
                {
                    "error": "Supervisor action failed",
                    "details": result.stderr or result.stdout,
                }
            ),
            502,
        )
    return jsonify({"status": "ok", "output": result.stdout}), 200


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

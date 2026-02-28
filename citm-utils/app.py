import pip_system_certs.wrapt_requests

pip_system_certs.wrapt_requests.inject_truststore()

import supervisor
from flask import Flask, send_file, request, jsonify
import subprocess
import fcntl
import socket
import requests
import service_discovery
import docker

docker_client = docker.from_env()

app = Flask(__name__)
app.json.compact = False


@app.route("/supervisor", methods=["GET"])
def get_ui():
    return send_file("supervisor.html")


@app.route("/supervisor/api/services", methods=["GET"])
def list_services():
    try:
        services = supervisor.list_services()
        return jsonify({"services": services, "hostname": socket.gethostname()}), 200
    except supervisor.SupervisorError as e:
        return jsonify({"error": e.message, "details": e.details}), e.status_code
    except Exception as e:
        return (
            jsonify({"error": "Failed to read supervisor services", "details": str(e)}),
            502,
        )


@app.route("/supervisor/api/services/<name>/<action>", methods=["POST"])
def service_action(name, action):
    try:
        supervisor.service_action(name, action)
        return jsonify({"status": "ok"}), 200
    except supervisor.SupervisorError as e:
        return jsonify({"error": e.message, "details": e.details}), e.status_code
    except Exception as e:
        return jsonify({"error": "Supervisor action failed", "details": str(e)}), 502


@app.route("/supervisor/api/services/restart-all", methods=["POST"])
def restart_all():
    try:
        supervisor.restart_all()
        return jsonify({"status": "ok"}), 200
    except supervisor.SupervisorError as e:
        return jsonify({"error": e.message, "details": e.details}), e.status_code
    except Exception as e:
        return jsonify({"error": "Supervisor action failed", "details": str(e)}), 502


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
    dns_entries = service_discovery.get_citm_dns_entries(docker_client)
    return (
        jsonify(
            {
                "hostname": socket.gethostname(),
                "request_data": request_data,
                "dns_entries": dns_entries,
            }
        ),
        200,
    )


@app.route("/health", methods=["GET"])
def get_health():
    results = []

    try:
        docker_ping = docker_client.ping()
        results.append(
            {
                "check": "docker_connection",
                "ok": bool(docker_ping),
                "actual": docker_ping,
            }
        )
    except Exception as e:
        results.append(
            {
                "check": "docker_connection",
                "ok": False,
                "error": str(e),
            }
        )

    dns_name = "citm.internal"
    expected_ipv4 = "127.0.0.1"

    try:
        resolved_ips = sorted(
            {
                info[4][0]
                for info in socket.getaddrinfo(
                    dns_name,
                    None,
                    family=socket.AF_INET,
                )
            }
        )
        results.append(
            {
                "check": "dns_forwarder_resolution",
                "name": dns_name,
                "expected_ipv4": expected_ipv4,
                "resolved_ipv4": resolved_ips,
                "ok": expected_ipv4 in resolved_ips,
            }
        )
    except Exception as e:
        results.append(
            {
                "check": "dns_forwarder_resolution",
                "name": dns_name,
                "expected_ipv4": expected_ipv4,
                "ok": False,
                "error": str(e),
            }
        )

    service_checks = [
        {
            "check": "caddy_serving",
            "url": "https://citm.internal:3858",
            "expected_status": 404,
        },
        {
            "check": "mitmproxy_serving",
            "url": "https://mitm.citm.internal:3858",
            "expected_status": 200,
        },
    ]

    for service_check in service_checks:
        try:
            response = requests.get(service_check["url"], timeout=2)
            results.append(
                {
                    "check": service_check["check"],
                    "url": service_check["url"],
                    "expected_status": service_check["expected_status"],
                    "actual_status": response.status_code,
                    "ok": response.status_code == service_check["expected_status"],
                }
            )
        except Exception as e:
            results.append(
                {
                    "check": service_check["check"],
                    "url": service_check["url"],
                    "expected_status": service_check["expected_status"],
                    "ok": False,
                    "error": str(e),
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

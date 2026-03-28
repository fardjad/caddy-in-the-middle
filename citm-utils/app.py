import pip_system_certs.wrapt_requests

pip_system_certs.wrapt_requests.inject_truststore()

import os
import socket
from collections.abc import Callable

import docker
import requests
from flask import Flask, jsonify, request

from mitmproxy.routes import mitmproxy_blueprint
from service_discovery import get_citm_dns_entries

# BEGIN GENERATED DEFAULT PORTS
DEFAULT_CADDY_ADMIN_PORT = 63858
DEFAULT_CITM_UTILS_WEB_PORT = 19000
# END GENERATED DEFAULT PORTS

DockerClientFactory = Callable[[], docker.DockerClient]


def create_app(
    *,
    docker_client: docker.DockerClient | None = None,
    docker_client_factory: DockerClientFactory = docker.from_env,
    dns_entries_loader: Callable[
        [docker.DockerClient], dict[str, dict[str, list[str]]]
    ] = get_citm_dns_entries,
    http_get: Callable[..., requests.Response] = requests.get,
    hostname_getter: Callable[[], str] = socket.gethostname,
    addrinfo_getter: Callable[..., list[tuple]] = socket.getaddrinfo,
) -> Flask:
    resolved_docker_client = docker_client
    caddy_admin_port = int(os.getenv("CADDY_ADMIN_PORT", str(DEFAULT_CADDY_ADMIN_PORT)))

    app = Flask(__name__)
    app.json.compact = False
    app.register_blueprint(mitmproxy_blueprint)

    def get_docker_client() -> docker.DockerClient:
        nonlocal resolved_docker_client
        if resolved_docker_client is None:
            resolved_docker_client = docker_client_factory()
        return resolved_docker_client

    @app.route(
        "/", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
    )
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
        dns_entries = dns_entries_loader(get_docker_client())
        return (
            jsonify(
                {
                    "hostname": hostname_getter(),
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
            docker_ping = get_docker_client().ping()
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
                    for info in addrinfo_getter(
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
                "url": f"https://citm.internal:{caddy_admin_port}",
                "expected_status": 404,
            },
            {
                "check": "mitmproxy_serving",
                "url": f"https://mitm.citm.internal:{caddy_admin_port}",
                "expected_status": 200,
            },
        ]

        for service_check in service_checks:
            try:
                response = http_get(service_check["url"], timeout=2)
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

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("CITM_UTILS_WEB_PORT", str(DEFAULT_CITM_UTILS_WEB_PORT))),
    )

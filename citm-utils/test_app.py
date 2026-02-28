from __future__ import annotations

import socket
from typing import Any

from app import create_app


class FakeDockerClient:
    def __init__(self, *, ping_result: Any = True, ping_error: Exception | None = None):
        self._ping_result = ping_result
        self._ping_error = ping_error

    def ping(self) -> Any:
        if self._ping_error is not None:
            raise self._ping_error
        return self._ping_result


class FakeResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


def test_root_returns_request_data_and_dns_entries():
    expected_dns_entries = {
        "api.internal": {
            "ipv4": ["10.0.0.2"],
            "ipv6": [],
        }
    }

    app = create_app(
        docker_client=FakeDockerClient(),
        dns_entries_loader=lambda _client: expected_dns_entries,
        hostname_getter=lambda: "citm-host",
    )
    client = app.test_client()

    response = client.get("/?a=1&a=2", headers={"X-Test": "ok"})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["hostname"] == "citm-host"
    assert payload["dns_entries"] == expected_dns_entries
    assert payload["request_data"]["method"] == "GET"
    assert payload["request_data"]["args"] == {"a": ["1", "2"]}
    assert payload["request_data"]["headers"]["X-Test"] == "ok"


def test_health_returns_ok_when_all_checks_pass():
    def fake_get(url: str, timeout: int) -> FakeResponse:
        status_map = {
            "https://citm.internal:3858": 404,
            "https://mitm.citm.internal:3858": 200,
        }
        assert timeout == 2
        return FakeResponse(status_map[url])

    def fake_getaddrinfo(*_args, **_kwargs):
        return [
            (socket.AF_INET, 0, 0, "", ("127.0.0.1", 0)),
            (socket.AF_INET, 0, 0, "", ("127.0.0.1", 0)),
        ]

    app = create_app(
        docker_client=FakeDockerClient(ping_result=True),
        http_get=fake_get,
        addrinfo_getter=fake_getaddrinfo,
    )
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "ok"

    checks = {check["check"]: check for check in payload["checks"]}
    assert checks["docker_connection"]["ok"] is True
    assert checks["dns_forwarder_resolution"]["ok"] is True
    assert checks["caddy_serving"]["actual_status"] == 404
    assert checks["mitmproxy_serving"]["actual_status"] == 200


def test_health_returns_unhealthy_when_any_check_fails():
    def failing_get(_url: str, timeout: int) -> FakeResponse:
        assert timeout == 2
        raise TimeoutError("network timeout")

    def failing_getaddrinfo(*_args, **_kwargs):
        raise socket.gaierror("name lookup failed")

    app = create_app(
        docker_client=FakeDockerClient(ping_error=RuntimeError("docker unavailable")),
        http_get=failing_get,
        addrinfo_getter=failing_getaddrinfo,
    )
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 503
    payload = response.get_json()
    assert payload["status"] == "unhealthy"
    assert any(not check["ok"] for check in payload["checks"])

    checks = {check["check"]: check for check in payload["checks"]}
    assert checks["docker_connection"]["ok"] is False
    assert "docker unavailable" in checks["docker_connection"]["error"]
    assert checks["dns_forwarder_resolution"]["ok"] is False
    assert checks["caddy_serving"]["ok"] is False
    assert checks["mitmproxy_serving"]["ok"] is False

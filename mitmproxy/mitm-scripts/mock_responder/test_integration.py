from __future__ import annotations

import socketserver
import threading
from http.server import BaseHTTPRequestHandler
from pathlib import Path

import pytest
from mitmproxy import connection, http

from mock_responder.addon import MockResponder

FIXTURES_DIR = Path(__file__).with_name("fixtures")


def _build_flow(url: str, http_version: str = "HTTP/1.1") -> http.HTTPFlow:
    client = connection.Client(
        peername=("127.0.0.1", 55123),
        sockname=("127.0.0.1", 8380),
    )
    server = connection.Server(address=("public.example", 443))
    flow = http.HTTPFlow(client, server, live=True)
    request = http.Request.make("GET", url)
    request.http_version = http_version
    flow.request = request
    return flow


def _create_addon(monkeypatch: pytest.MonkeyPatch, *patterns: str) -> MockResponder:
    monkeypatch.setenv("MOCK_PATHS", ",".join(patterns))
    return MockResponder()


def test_exact_match_serves_rendered_response(monkeypatch: pytest.MonkeyPatch):
    addon = _create_addon(monkeypatch, str(FIXTURES_DIR / "exact_render.mako"))
    flow = _build_flow("https://service.example/api/users")

    addon.request(flow)

    assert flow.response is not None
    assert flow.response.status_code == 201
    assert flow.response.headers["Content-Type"] == "text/plain"
    assert flow.response.headers["X-Scenario"] == "exact"
    assert flow.response.get_text().strip() == "Hello service.example /api/users"


def test_wildcard_match_serves_response(monkeypatch: pytest.MonkeyPatch):
    addon = _create_addon(monkeypatch, str(FIXTURES_DIR / "wildcard_match.mako"))
    flow = _build_flow("https://service.example/orders/42")

    addon.request(flow)

    assert flow.response is not None
    assert flow.response.status_code == 202
    assert flow.response.headers["X-Scenario"] == "wildcard"
    assert flow.response.get_text().strip() == "Matched order path /orders/42"


def test_code_block_before_separator_is_executed(monkeypatch: pytest.MonkeyPatch):
    addon = _create_addon(
        monkeypatch, str(FIXTURES_DIR / "pre_separator_code_block.mako")
    )
    flow = _build_flow("https://pre-separator.example/subscriptions/alpha")

    addon.request(flow)

    assert flow.response is not None
    assert flow.response.status_code == 200
    assert flow.response.headers["X-Scenario"] == "pre-separator"
    assert (
        flow.response.get_text().strip()
        == '<result resource="subscriptions" id="alpha"/>'
    )


def test_request_without_match_is_passthrough(monkeypatch: pytest.MonkeyPatch):
    addon = _create_addon(monkeypatch, str(FIXTURES_DIR / "exact_render.mako"))
    flow = _build_flow("https://service.example/api/unknown")

    addon.request(flow)

    assert flow.response is None


def test_hot_reload_reflects_updated_fixture(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    hot_reload_fixture = tmp_path / "hot_reload.mako"
    hot_reload_fixture.write_text(
        (FIXTURES_DIR / "hot_reload.mako").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    addon = _create_addon(monkeypatch, str(hot_reload_fixture))

    first_flow = _build_flow("https://reload.example/value")
    addon.request(first_flow)

    hot_reload_fixture.write_text(
        (
            "GET https://reload.example/value\n\n"
            "200\n"
            "Content-Type: text/plain\n\n"
            "---\n"
            "updated value\n"
        ),
        encoding="utf-8",
    )

    second_flow = _build_flow("https://reload.example/value")
    addon.request(second_flow)

    assert first_flow.response is not None
    assert second_flow.response is not None
    assert first_flow.response.get_text().strip() == "initial value"
    assert second_flow.response.get_text().strip() == "updated value"


def test_external_fetch_uses_upstream_status_and_merges_headers(
    monkeypatch: pytest.MonkeyPatch,
):
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = b"from upstream"
            self.send_response(209)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Connection", "keep-alive")
            self.send_header("X-Mock-Override", "from-upstream")
            self.send_header("X-Upstream", "yes")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt, *args):
            return

    with socketserver.TCPServer(("127.0.0.1", 0), _Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            addon = _create_addon(
                monkeypatch, str(FIXTURES_DIR / "external_fetch.mako")
            )
            flow = _build_flow("https://external.example/data")
            flow.request.headers["X-Upstream-URL"] = (
                f"http://127.0.0.1:{server.server_address[1]}/data"
            )

            addon.request(flow)
        finally:
            server.shutdown()
            thread.join(timeout=2)

    assert flow.response is not None
    assert flow.response.status_code == 209
    assert flow.response.get_text() == "from upstream"
    assert flow.response.headers["X-Upstream"] == "yes"
    assert flow.response.headers["X-Mock-Override"] == "from-mock"
    assert flow.response.headers["Content-Type"] == "application/json"


@pytest.mark.parametrize("http_version", ["HTTP/1.1", "HTTP/2.0", "HTTP/3"])
def test_template_host_header_is_available_across_protocols(
    monkeypatch: pytest.MonkeyPatch, http_version: str
):
    addon = _create_addon(
        monkeypatch, str(FIXTURES_DIR / "http_compat_host_header.mako")
    )
    flow = _build_flow("https://compat.example/resource", http_version=http_version)

    addon.request(flow)

    assert flow.response is not None
    assert flow.response.get_text().strip() == "Host=compat.example"


@pytest.mark.parametrize("http_version", ["HTTP/1.1", "HTTP/2.0", "HTTP/3"])
def test_response_headers_are_protocol_safe(
    monkeypatch: pytest.MonkeyPatch, http_version: str
):
    addon = _create_addon(monkeypatch, str(FIXTURES_DIR / "protocol_headers.mako"))
    flow = _build_flow("https://protocol.example/check", http_version=http_version)

    addon.request(flow)

    assert flow.response is not None
    assert flow.response.headers["X-Stable"] == "yes"
    if http_version == "HTTP/1.1":
        assert flow.response.headers["Connection"] == "keep-alive"
        assert flow.response.headers["Transfer-Encoding"] == "chunked"
        assert flow.response.headers["Upgrade"] == "websocket"
    else:
        assert flow.response.headers.get("Connection") is None
        assert flow.response.headers.get("Transfer-Encoding") is None
        assert flow.response.headers.get("Upgrade") is None

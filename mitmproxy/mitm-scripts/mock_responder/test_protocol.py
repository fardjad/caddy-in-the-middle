from __future__ import annotations

from mitmproxy import connection, http

from mock_responder.protocol import build_template_flow, normalize_response_headers


def _build_flow(http_version: str = "HTTP/1.1") -> http.HTTPFlow:
    client = connection.Client(
        peername=("127.0.0.1", 55123),
        sockname=("127.0.0.1", 8380),
    )
    server = connection.Server(address=("public.example", 443))
    flow = http.HTTPFlow(client, server, live=True)
    request = http.Request.make("GET", "https://public.example/api")
    request.http_version = http_version
    flow.request = request
    return flow


def test_template_flow_provides_host_header_without_mutating_original_request():
    flow = _build_flow("HTTP/2.0")
    original_host = flow.request.headers.get("Host")

    template_flow = build_template_flow(flow)

    assert original_host is None
    assert template_flow.request.headers["Host"] == "public.example"
    assert flow.request.headers.get("Host") is None


def test_template_flow_keeps_explicit_host_header():
    flow = _build_flow("HTTP/3")
    flow.request.headers["Host"] = "override.example:8443"

    template_flow = build_template_flow(flow)

    assert template_flow.request.headers["Host"] == "override.example:8443"


def test_normalize_response_headers_keeps_http1_hop_by_hop_headers():
    headers = {
        "Connection": "keep-alive",
        "Transfer-Encoding": "chunked",
        "Upgrade": "websocket",
        "X-Stable": "yes",
    }

    normalized = normalize_response_headers(headers, "HTTP/1.1")

    assert normalized == headers


def test_normalize_response_headers_drops_disallowed_http2_headers():
    headers = {
        "Connection": "keep-alive",
        "Transfer-Encoding": "chunked",
        "Upgrade": "websocket",
        "X-Stable": "yes",
    }

    normalized = normalize_response_headers(headers, "HTTP/2.0")

    assert normalized == {"X-Stable": "yes"}

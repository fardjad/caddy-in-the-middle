from __future__ import annotations

from types import SimpleNamespace

import pytest
from mitmproxy import connection, http

import rewrite_host.addon as addon_module
from rewrite_host.addon import RewriteHost


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


@pytest.mark.parametrize("http_version", ["HTTP/1.1", "HTTP/2.0", "HTTP/3"])
def test_request_rewrites_host_and_preserves_authority(http_version: str):
    flow = _build_flow(http_version)
    flow.request.headers["X-MITM-To"] = "backend.internal:8443"
    flow.request.headers["X-MITM-Emoji"] = ":rocket:"

    RewriteHost().request(flow)

    assert flow.request.host == "backend.internal"
    assert flow.request.port == 8443
    assert flow.server_conn.sni == "public.example"
    assert flow.request.host_header == "public.example:443"
    assert flow.marked == ":rocket:"
    assert flow.comment == "Rewriting host public.example -> backend.internal:8443"

    if http_version == "HTTP/1.1":
        assert flow.request.headers["Host"] == "public.example:443"
        assert flow.request.authority == ""
    else:
        assert flow.request.authority == "public.example:443"
        assert flow.request.headers.get("Host") is None


def test_request_without_target_header_is_noop():
    flow = _build_flow("HTTP/1.1")

    RewriteHost().request(flow)

    assert flow.request.host == "public.example"
    assert flow.request.port == 443
    assert flow.server_conn.sni is None
    assert flow.comment == ""


@pytest.mark.parametrize(
    "target_value,expected_reason",
    [
        ("backend.internal", "target must use host:port format"),
        ("backend.internal:not-a-number", "port must be a number"),
        ("backend.internal:0", "port must be in range 1..65535"),
        ("backend.internal:65536", "port must be in range 1..65535"),
        (":443", "target must use host:port format"),
    ],
)
def test_invalid_target_kills_flow_marks_warning_and_logs(
    monkeypatch: pytest.MonkeyPatch,
    target_value: str,
    expected_reason: str,
):
    flow = _build_flow("HTTP/3")
    flow.request.headers["X-MITM-To"] = target_value

    captured_errors: list[str] = []
    monkeypatch.setattr(
        addon_module,
        "ctx",
        SimpleNamespace(log=SimpleNamespace(error=captured_errors.append)),
    )

    RewriteHost().request(flow)

    assert flow.error is not None
    assert flow.error.msg == "Connection killed."
    assert flow.marked == ":warning:"
    assert flow.request.host == "public.example"
    assert flow.request.port == 443
    assert flow.server_conn.sni is None

    assert f"Invalid X-MITM-To '{target_value}'" in flow.comment
    assert expected_reason in flow.comment
    assert "Blocking request." in flow.comment

    assert captured_errors == [flow.comment]

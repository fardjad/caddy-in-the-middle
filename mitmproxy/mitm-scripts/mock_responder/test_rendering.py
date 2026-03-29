from __future__ import annotations

from types import SimpleNamespace

from mitmproxy import connection, http

import mock_responder.rendering as rendering_module
from mock_responder.rendering import fetch_external, render_and_extract_body


def _build_flow() -> http.HTTPFlow:
    client = connection.Client(
        peername=("127.0.0.1", 55123),
        sockname=("127.0.0.1", 8380),
    )
    server = connection.Server(address=("public.example", 443))
    flow = http.HTTPFlow(client, server, live=True)
    request = http.Request.make("GET", "https://public.example/api")
    flow.request = request
    return flow


def test_render_and_extract_body_renders_template_with_flow():
    flow = _build_flow()

    rendered = render_and_extract_body("---\nURL=${flow.request.url}", flow)

    assert rendered == "URL=https://public.example/api"


def test_render_and_extract_body_falls_back_to_unrendered_body_on_mako_error():
    flow = _build_flow()

    rendered = render_and_extract_body("---\n${1/0}", flow)

    assert rendered == "${1/0}"


def test_fetch_external_failure_uses_mock_status_and_headers(monkeypatch):
    def _failing_urlopen(_url):
        raise RuntimeError("network down")

    monkeypatch.setattr(
        rendering_module,
        "urllib",
        SimpleNamespace(request=SimpleNamespace(urlopen=_failing_urlopen)),
    )

    status, headers, body = fetch_external(
        "@@http://127.0.0.1:8999/fail",
        mock_status=503,
        mock_headers={"X-Mock": "yes"},
    )

    assert status == 503
    assert headers == {"X-Mock": "yes"}
    assert body == b""

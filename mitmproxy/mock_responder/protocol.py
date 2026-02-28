from __future__ import annotations

from typing import Any

from mitmproxy.http import Headers

from .models import HTTP2_OR_3_DISALLOWED_HEADERS


def build_template_flow(flow: Any) -> Any:
    return _TemplateFlowAdapter(flow)


def normalize_response_headers(
    headers: dict[str, str], http_version: str | None
) -> dict[str, str]:
    normalized = dict(headers)
    if http_version not in {"HTTP/2.0", "HTTP/3"}:
        return normalized

    return {
        key: value
        for key, value in normalized.items()
        if key.lower() not in HTTP2_OR_3_DISALLOWED_HEADERS
    }


class _TemplateRequestAdapter:
    def __init__(self, request: Any) -> None:
        self._request = request
        self.headers = Headers(request.headers.fields)

        if self.headers.get("Host") is None:
            self.headers["Host"] = _request_host_header(request)

    def __getattr__(self, attr: str) -> Any:
        return getattr(self._request, attr)


class _TemplateFlowAdapter:
    def __init__(self, flow: Any) -> None:
        self._flow = flow
        self.request = _TemplateRequestAdapter(flow.request)

    def __getattr__(self, attr: str) -> Any:
        return getattr(self._flow, attr)


def _request_host_header(request: Any) -> str:
    if request.host_header:
        return request.host_header

    default_port = 443 if request.scheme == "https" else 80
    if request.port == default_port:
        return request.host

    return f"{request.host}:{request.port}"

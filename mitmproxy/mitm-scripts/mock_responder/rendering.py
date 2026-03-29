from __future__ import annotations

import logging
import urllib.request

from mako.template import Template
from mitmproxy import ctx

from .models import EXTERNAL_RESPONSE_EXCLUDED_HEADERS
from .protocol import build_template_flow


def _log_info(message: str) -> None:
    logger = getattr(ctx, "log", None)
    if logger is not None:
        logger.info(message)
        return
    logging.getLogger(__name__).info(message)


def _log_warn(message: str) -> None:
    logger = getattr(ctx, "log", None)
    if logger is not None:
        logger.warn(message)
        return
    logging.getLogger(__name__).warning(message)


def _log_error(message: str) -> None:
    logger = getattr(ctx, "log", None)
    if logger is not None:
        logger.error(message)
        return
    logging.getLogger(__name__).error(message)


def render_and_extract_body(remainder: str, flow) -> str:
    try:
        template_flow = build_template_flow(flow)
        rendered = Template(remainder).render(flow=template_flow)
    except Exception as exc:
        _log_warn(f"Mako render error for {flow.request.url}: {exc}")
        rendered = remainder

    separator = "---\n"
    if separator in rendered:
        _, body = rendered.split(separator, 1)
        return body

    return rendered


def should_fetch_external(rendered_body: str) -> bool:
    return rendered_body.lstrip().startswith("@@")


def fetch_external(
    rendered_body: str, mock_status: int, mock_headers: dict[str, str]
) -> tuple[int, dict[str, str], bytes]:
    target_url = rendered_body.lstrip().split("\n")[0][2:].strip()
    _log_info(f"Fetching external content from: {target_url}")

    try:
        with urllib.request.urlopen(target_url) as response:
            status = response.getcode()
            remote_headers = _clean_external_headers(dict(response.getheaders()))
            response_body = response.read()
            merged_headers = {**remote_headers, **mock_headers}
            return status, merged_headers, response_body
    except Exception as exc:
        _log_error(f"Failed to fetch from {target_url}: {exc}")
        return mock_status, dict(mock_headers), b""


def _clean_external_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        key: value
        for key, value in headers.items()
        if key.lower() not in EXTERNAL_RESPONSE_EXCLUDED_HEADERS
    }

from __future__ import annotations

import logging
from typing import Tuple

from mitmproxy import ctx


def _log_error(message: str) -> None:
    logger = getattr(ctx, "log", None)
    if logger is not None:
        logger.error(message)
        return
    logging.getLogger(__name__).error(message)


def _parse_target(value: str) -> Tuple[str, int]:
    host, separator, port_text = value.rpartition(":")
    if separator == "" or not host or not port_text:
        raise ValueError("target must use host:port format")

    try:
        port = int(port_text)
    except ValueError as exc:
        raise ValueError("port must be a number") from exc

    if port < 1 or port > 65535:
        raise ValueError("port must be in range 1..65535")

    return host, port


class RewriteHost:
    def request(self, flow) -> None:
        headers = {k.lower(): v for k, v in flow.request.headers.items()}
        emoji = headers.get("x-mitm-emoji", "")
        target = headers.get("x-mitm-to", "").strip()

        if not target:
            return

        try:
            target_host, target_port = _parse_target(target)
        except ValueError as exc:
            reason = str(exc)
            message = f"Invalid X-MITM-To '{target}': {reason}. Blocking request."
            flow.marked = ":warning:"
            flow.comment = message
            _log_error(message)
            flow.kill()
            return

        if emoji:
            flow.marked = emoji

        pretty_host = flow.request.pretty_host
        flow.comment = f"Rewriting host {pretty_host} -> {target}"

        flow.server_conn.sni = pretty_host

        preserved_host_header = f"{pretty_host}:{flow.request.port}"
        flow.request.host = target_host
        flow.request.port = target_port
        flow.request.host_header = preserved_host_header

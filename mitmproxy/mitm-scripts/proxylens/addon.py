import os
import socket

from proxylens_mitmproxy import (
    DEFAULT_MAX_CONCURRENT_REQUESTS_PER_HOST_ENV_VAR,
    DEFAULT_PROXYLENS_SERVER_BASE_URL_ENV_VAR,
    ProxyLens,
)

ENABLE_PROXYLENS_SERVER_ENV_VAR = "ENABLE_PROXYLENS_SERVER"
PROXYLENS_NODE_NAME_ENV_VAR = "PROXYLENS_NODE_NAME"
PROXYLENS_SERVER_PORT_ENV_VAR = "PROXYLENS_SERVER_PORT"
DEFAULT_PROXYLENS_SERVER_PORT = "19003"


def resolve_default_server_base_url(
    *,
    server_base_url: str | None,
    server_base_url_env_var: str,
) -> str | None:
    if server_base_url is not None:
        return server_base_url

    configured = os.environ.get(server_base_url_env_var)
    if configured is not None:
        return configured

    if os.environ.get(ENABLE_PROXYLENS_SERVER_ENV_VAR, "").lower() not in {
        "1",
        "true",
    }:
        return None

    return (
        "http://127.0.0.1:"
        f"{os.environ.get(PROXYLENS_SERVER_PORT_ENV_VAR, DEFAULT_PROXYLENS_SERVER_PORT)}"
    )


class CitmProxyLens(ProxyLens):
    def __init__(
        self,
        *,
        node_name: str | None = None,
        node_name_env_var: str = PROXYLENS_NODE_NAME_ENV_VAR,
        server_base_url: str | None = None,
        server_base_url_env_var: str = DEFAULT_PROXYLENS_SERVER_BASE_URL_ENV_VAR,
        max_concurrent_requests_per_host: int | None = None,
        max_concurrent_requests_per_host_env_var: str = (
            DEFAULT_MAX_CONCURRENT_REQUESTS_PER_HOST_ENV_VAR
        ),
    ) -> None:
        super().__init__(
            node_name=(
                node_name or os.environ.get(node_name_env_var) or socket.gethostname()
            ),
            node_name_env_var=node_name_env_var,
            server_base_url=resolve_default_server_base_url(
                server_base_url=server_base_url,
                server_base_url_env_var=server_base_url_env_var,
            ),
            server_base_url_env_var=server_base_url_env_var,
            max_concurrent_requests_per_host=max_concurrent_requests_per_host,
            max_concurrent_requests_per_host_env_var=(
                max_concurrent_requests_per_host_env_var
            ),
        )

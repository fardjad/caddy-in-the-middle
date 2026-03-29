import os
import socket

from proxylens_mitmproxy import (
    DEFAULT_MAX_CONCURRENT_REQUESTS_PER_HOST_ENV_VAR,
    DEFAULT_PROXYLENS_SERVER_BASE_URL_ENV_VAR,
    ProxyLens,
)

PROXYLENS_NODE_NAME_ENV_VAR = "PROXYLENS_NODE_NAME"


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
            server_base_url=server_base_url,
            server_base_url_env_var=server_base_url_env_var,
            max_concurrent_requests_per_host=max_concurrent_requests_per_host,
            max_concurrent_requests_per_host_env_var=(
                max_concurrent_requests_per_host_env_var
            ),
        )

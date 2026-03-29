from proxylens.addon import (
    CitmProxyLens,
    DEFAULT_MAX_CONCURRENT_REQUESTS_PER_HOST_ENV_VAR,
    DEFAULT_PROXYLENS_SERVER_BASE_URL_ENV_VAR,
    PROXYLENS_NODE_NAME_ENV_VAR,
)
from proxylens_mitmproxy import ProxyLens


def test_citm_proxylens_uses_hostname_by_default(monkeypatch) -> None:
    monkeypatch.delenv(PROXYLENS_NODE_NAME_ENV_VAR, raising=False)
    monkeypatch.setattr("proxylens.addon.socket.gethostname", lambda: "citm-host")

    addon = CitmProxyLens()

    assert isinstance(addon, ProxyLens)
    assert addon._node_name == "citm-host"


def test_citm_proxylens_prefers_proxylens_env_var(monkeypatch) -> None:
    monkeypatch.setenv(PROXYLENS_NODE_NAME_ENV_VAR, "edge-proxy")
    monkeypatch.setattr("proxylens.addon.socket.gethostname", lambda: "citm-host")

    addon = CitmProxyLens()

    assert addon._node_name == "edge-proxy"


def test_citm_proxylens_supports_upstream_runtime_options() -> None:
    addon = CitmProxyLens(
        node_name="proxy-a",
        server_base_url="http://proxylens-server:8000",
        max_concurrent_requests_per_host=2,
    )

    assert addon._node_name == "proxy-a"
    assert addon._client is not None
    assert addon._client.base_url == "http://proxylens-server:8000"
    assert addon._max_concurrent_requests_per_host == 2


def test_citm_proxylens_re_exports_upstream_env_var_names() -> None:
    assert DEFAULT_PROXYLENS_SERVER_BASE_URL_ENV_VAR == "PROXYLENS_SERVER_BASE_URL"
    assert (
        DEFAULT_MAX_CONCURRENT_REQUESTS_PER_HOST_ENV_VAR
        == "PROXYLENS_MAX_CONCURRENT_REQUESTS_PER_HOST"
    )

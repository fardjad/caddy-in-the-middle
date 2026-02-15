import pytest
import shutil
import tempfile
from pathlib import Path
from caddy_in_the_middle import CitmContainer, generate_root_ca


@pytest.fixture(scope="module")
def citm_fixture():
    # Setup
    certs_dir = tempfile.mkdtemp()
    mocks_dir = tempfile.mkdtemp()

    try:
        certs_path = Path(certs_dir)
        generate_root_ca(certs_path)

        container = CitmContainer()
        container.with_certs_directory(certs_path)
        container.with_mocks_directory(Path(mocks_dir))

        container.start()

        yield container

        # Teardown
        container.stop()
    finally:
        if Path(certs_dir).exists():
            shutil.rmtree(certs_dir)
        if Path(mocks_dir).exists():
            shutil.rmtree(mocks_dir)


class TestCitmContainer:
    def test_should_start_container(self, citm_fixture):
        wrapped_container = citm_fixture.get_wrapped_container()
        wrapped_container.reload()  # Refresh status
        assert wrapped_container.status == "running"

        container_info = citm_fixture.get_docker_client().client.api.inspect_container(
            wrapped_container.id
        )
        state = container_info.get("State", {})
        assert state.get("Health", {}).get("Status") == "healthy"

    def test_should_return_valid_caddy_http_base_url(self, citm_fixture):
        url = citm_fixture.get_caddy_http_base_url()
        assert url.startswith("http://")
        assert ":" in url
        assert len(url.split(":")) == 3  # http://host:port

    def test_should_return_valid_caddy_https_base_url(self, citm_fixture):
        url = citm_fixture.get_caddy_https_base_url()
        assert url.startswith("https://")
        assert ":" in url

    def test_should_return_valid_http_proxy_address(self, citm_fixture):
        address = citm_fixture.get_http_proxy_address()
        assert address.startswith("http://")
        assert ":" in address

    def test_should_return_valid_socks_proxy_address(self, citm_fixture):
        address = citm_fixture.get_socks_proxy_address()
        assert address.startswith("socks5://")
        assert ":" in address

    def test_should_return_valid_admin_base_url(self, citm_fixture):
        url = citm_fixture.get_admin_base_url()
        assert url.startswith("http://")
        assert ":" in url

    def test_should_create_configured_http_client_handler(self, citm_fixture):
        session = citm_fixture.create_client(ignore_ssl_errors=True)
        assert session is not None

        assert "http" in session.proxies
        assert "https" in session.proxies

        proxy_url = citm_fixture.get_http_proxy_address()
        assert session.proxies["http"] == proxy_url
        assert session.proxies["https"] == proxy_url

        assert session.verify is False

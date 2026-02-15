import pytest
from pathlib import Path
from caddy_in_the_middle import CitmContainer


class TestCitmConfiguration:
    def test_should_set_certs_directory(self):
        certs_path = "/tmp/certs"
        container = CitmContainer()
        container.with_certs_directory(Path(certs_path))

        abs_path = str(Path(certs_path).absolute())
        assert abs_path in container.volumes
        assert container.volumes[abs_path]["bind"] == "/certs"

    def test_should_throw_if_certs_directory_is_not_set_on_start(self):
        container = CitmContainer()
        with pytest.raises(ValueError, match="Certs directory must be mounted"):
            container.start()

    def test_should_set_mocks_directory(self):
        mocks_path = "/tmp/mocks"
        container = CitmContainer()
        container.with_mocks_directory(Path(mocks_path))

        abs_path = str(Path(mocks_path).absolute())
        assert abs_path in container.volumes
        assert container.volumes[abs_path]["bind"] == "/citm-mocks/"

        assert container.env["MOCK_PATHS"] == "/citm-mocks/**/*.mako"

    def test_should_set_caddyfile_directory(self):
        caddy_path = "/tmp/caddy"
        container = CitmContainer()
        container.with_caddyfile_directory(Path(caddy_path))

        abs_path = str(Path(caddy_path).absolute())
        assert abs_path in container.volumes
        assert container.volumes[abs_path]["bind"] == "/etc/caddy/conf.d"

    def test_should_set_citm_network(self):
        network_name = "some-network"
        container = CitmContainer()
        container.with_citm_network(network_name)

        assert container._kwargs.get("network") == network_name

        labels = container._kwargs.get("labels", {})
        assert labels.get("citm_network") == network_name

    def test_should_mount_docker_socket_by_default(self):
        container = CitmContainer()

        assert "/var/run/docker.sock" in container.volumes
        assert (
            container.volumes["/var/run/docker.sock"]["bind"] == "/var/run/docker.sock"
        )

    def test_should_set_dns_names(self):
        names = ["name1", "name2"]
        container = CitmContainer()
        container.with_dns_names(*names)

        labels = container._kwargs.get("labels", {})
        assert labels.get("citm_dns_names") == "name1,name2"

    def test_should_set_default_mock_paths(self):
        container = CitmContainer()
        # Mocks directory helper sets the default if mock_paths is None
        container.with_mocks_directory(Path("/tmp/mocks"))
        assert container.env["MOCK_PATHS"] == "/citm-mocks/**/*.mako"

    def test_should_override_default_mock_paths(self):
        container = CitmContainer()
        container.with_mocks_directory(
            Path("/tmp/mocks"), mock_paths=["/citm-mocks/custom.mako"]
        )
        assert container.env["MOCK_PATHS"] == "/citm-mocks/custom.mako"

    def test_explicit_mock_paths(self):
        container = CitmContainer()
        container.with_mock_paths(["/citm-mocks/a", "/citm-mocks/b"])
        assert container.env["MOCK_PATHS"] == "/citm-mocks/a,/citm-mocks/b"

    def test_should_throw_if_mock_paths_do_not_have_the_correct_base_dir(self):
        container = CitmContainer()
        with pytest.raises(ValueError, match="'/citm-mocks/'"):
            container.with_mock_paths(["/whatever/*.mako"])

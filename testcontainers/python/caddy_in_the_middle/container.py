from pathlib import Path
from typing import Optional, List
import requests
import os
import subprocess
import posixpath
import urllib3
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import HealthcheckWaitStrategy
from .version import __version__


class CitmContainer(DockerContainer):
    """
    Testcontainers module for CaddyInTheMiddle.
    """

    def __init__(self, image: str = f"fardjad/citm:{__version__}", **kwargs):
        self._auto_configure_docker_host()
        super().__init__(image, **kwargs)
        self.with_exposed_ports(80, 443, 8380, 8381, 3858)
        self.with_volume_mapping("/var/run/docker.sock", "/var/run/docker.sock", "rw")
        self.waiting_for(HealthcheckWaitStrategy())

    @staticmethod
    def _auto_configure_docker_host():

        if os.environ.get("DOCKER_HOST"):
            return

        # If the variable is not set, then extract it from the context

        result = subprocess.run(
            ["docker", "context", "inspect", "--format", "{{.Endpoints.docker.Host}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        socket_path = result.stdout.strip()
        if socket_path:
            os.environ["DOCKER_HOST"] = socket_path

    def start(self):
        if not self._check_volume_mounted("/certs"):
            raise ValueError(
                "Certs directory must be mounted using with_certs_directory()"
            )

        super().start()
        return self

    def _check_volume_mounted(self, target: str) -> bool:
        for volume in self.volumes.values():
            if volume["bind"] == target:
                return True
        return False

    def with_certs_directory(self, path: Path) -> "CitmContainer":
        path = str(Path(path).absolute())
        self.with_volume_mapping(path, "/certs", "ro")
        return self

    def with_mocks_directory(
        self, path: Path, mock_paths: Optional[List[str]] = None
    ) -> "CitmContainer":
        path = str(Path(path).absolute())
        self.with_volume_mapping(path, "/citm-mocks/", "ro")

        if not mock_paths:
            self.with_env("MOCK_PATHS", "/citm-mocks/**/*.mako")
        else:
            self.with_mock_paths(mock_paths)
        return self

    def with_mock_paths(self, patterns: List[str]) -> "CitmContainer":

        normalized_patterns = []
        for pattern in patterns:
            normalized = posixpath.normpath(pattern)

            if not normalized.startswith("/citm-mocks/"):
                raise ValueError(f"Mock path '{pattern}' must be under '/citm-mocks/'.")
            normalized_patterns.append(normalized)

        self.with_env("MOCK_PATHS", ",".join(normalized_patterns))
        return self

    def with_caddyfile_directory(self, path: Path) -> "CitmContainer":
        path = str(Path(path).absolute())
        self.with_volume_mapping(path, "/etc/caddy/conf.d", "ro")
        return self

    def with_citm_network(self, network_name: str) -> "CitmContainer":
        # We handle network connection via run kwargs
        labels = self._kwargs.get("labels", {})
        labels["citm_network"] = network_name
        self._kwargs["labels"] = labels

        self._kwargs["network"] = network_name
        return self

    def with_dns_names(self, *names: str) -> "CitmContainer":
        labels = self._kwargs.get("labels", {})
        labels["citm_dns_names"] = ",".join(names)
        self._kwargs["labels"] = labels
        return self

    def _get_hostname_with_subdomains(self, *subdomains: str) -> str:
        ip = self.get_container_host_ip()

        # Convert loopback IPs to localhost
        if ip == "127.0.0.1" or ip == "::1":
            base_hostname = "localhost"
        else:
            base_hostname = ip

        if not subdomains:
            return base_hostname

        return f"{'.'.join(subdomains)}.{base_hostname}"

    def get_caddy_http_base_url(self, *subdomains: str) -> str:
        return f"http://{self._get_hostname_with_subdomains(*subdomains)}:{self.get_exposed_port(80)}"

    def get_caddy_https_base_url(self, *subdomains: str) -> str:
        return f"https://{self._get_hostname_with_subdomains(*subdomains)}:{self.get_exposed_port(443)}"

    def get_http_proxy_address(self) -> str:
        return f"http://{self.get_container_host_ip()}:{self.get_exposed_port(8380)}"

    def get_socks_proxy_address(self) -> str:
        return f"socks5://{self.get_container_host_ip()}:{self.get_exposed_port(8381)}"

    def get_admin_base_url(self, *subdomains: str) -> str:
        return f"https://{self._get_hostname_with_subdomains(*subdomains)}:{self.get_exposed_port(3858)}"

    def create_client(
        self, ignore_ssl_errors: bool = True, **kwargs
    ) -> requests.Session:
        session = requests.Session()
        proxy_url = self.get_http_proxy_address()
        session.proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }

        if ignore_ssl_errors:
            session.verify = False
            # Suppress InsecureRequestWarning

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        return session

# Testcontainers CaddyInTheMiddle Module (Python)

A [Testcontainers](https://github.com/testcontainers/testcontainers-python) module for [CaddyInTheMiddle](https://github.com/fardjad/caddy-in-the-middle), designed to simplify integration testing where you need a programmable reverse proxy or MITM proxy.

This library allows you to spin up a pre-configured Caddy instance in Docker, complete with mock responses, custom certificates, and proxy settings, all from your Python test code.

## Getting Started

1.  **Install the package**:
    (Assuming local development or future package name)
    ```bash
    # using uv
    uv add caddy-in-the-middle
    
    # or pip
    pip install caddy-in-the-middle
    ```

2.  **Generate Test Certificates**:
    Integration tests typically require trusted certificates. This library includes a helper to generate valid self-signed Root CA certificates on the fly.

3.  **Start the Container**:
    Use the `CitmContainer` class to configure and build the container instance.

## Usage Example

Here is a complete example using `pytest`:

```python
import pytest
from pathlib import Path
import tempfile
import shutil
from caddy_in_the_middle import CitmContainer, generate_root_ca

@pytest.fixture(scope="module")
def citm_container():
    # Create a temporary directory for certs
    certs_dir = tempfile.mkdtemp()
    certs_path = Path(certs_dir)
    
    try:
        # Generate the Root CA certificates
        generate_root_ca(certs_path)

        # Configure and start the container
        # Note: DOCKER_HOST is auto-detected if not set (e.g. for OrbStack)
        with CitmContainer().with_certs_directory(certs_path) as container:
            yield container
    finally:
        if Path(certs_dir).exists():
           shutil.rmtree(certs_dir)

def test_should_proxy_request(citm_container):
    # Create a requests.Session configured to use the container's proxy
    # This session ignores SSL errors by default since we use self-signed certs
    session = citm_container.create_client(ignore_ssl_errors=True)

    # Make a request through MITMProxy in the citm container
    # Note: 'example.com' will be proxied
    response = session.get("https://registered-dns-name-in-citm-network:1234/blabla")
    assert response.status_code == 200
```

## Configuration

The `CitmContainer` provides a fluent API for customization:

*   **`with_certs_directory(path: Path)`** (Required): Path to the directory containing `rootCA.pem` and `rootCA-key.pem`.
*   **`with_mocks_directory(path: Path)`**: Mounts a directory of mock templates (e.g., `*.mako` files) into the container.
*   **`with_caddyfile_directory(path: Path)`**: Mounts a directory containing a custom `Caddyfile` if you need advanced Caddy configuration.
*   **`with_citm_network(network_name: str)`**: Connects the container to a specific Docker network. This enables automatic service discovery: if other containers on this network have the `citm_dns_names` label, their DNS names will be automatically resolved by the `dnsmasq` instance running inside the CITM container.
*   **`with_dns_names(*names: str)`**: Sets the `citm_dns_names` label on the container. This leverages CITM's built-in service discovery to register these DNS names.
*   **`with_mock_paths(patterns: List[str])`**: explicit list of mock file patterns to load. *Note: Paths are validated to prevent traversal outside the mocks directory.*

## Helper Methods

Once the container is running and healthy, you can access helpful properties and methods:

*   **`create_client(ignore_ssl_errors=True)`**: Returns a `requests.Session` pre-configured with the correct proxy settings.
*   **`get_http_proxy_address()`**: Returns the address of the HTTP proxy (e.g., `http://localhost:32768`).
*   **`get_socks_proxy_address()`**: Returns the address of the SOCKS5 proxy.
*   **`get_admin_base_url()`**: Returns the base URL for the Caddy admin API.
*   **`get_caddy_http_base_url()` / `get_caddy_https_base_url()`**: Returns the base URLs for direct access to Caddy.

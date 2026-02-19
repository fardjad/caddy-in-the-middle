# CaddyInTheMiddle Testcontainers Module Specification

This document serves as the implementation specification for creating `CaddyInTheMiddle` Testcontainers modules in various languages (e.g., Python, Java, Go).

## 1. Container Configuration

*   **Image**: `fardjad/citm:<version>`
*   **Wait Strategy**: Wait until the container's healthcheck passes. This ensures Caddy is fully up and ready to serve traffic.

`version` comes from the `VERSION.txt` file in the root of the repository. Depending on the language, the build process should be adjusted to use the version from the `VERSION.txt` file for the image tag and the package version.

### 1.1 Ports

The module must expose the following container ports and map them to random host ports (unless the user explicitly binds them, though random is preferred for tests).

| Port | Description |
| :--- | :--- |
| `80` | HTTP traffic (incoming to Caddy) |
| `443` | HTTPS traffic (incoming to Caddy) |
| `8380` | HTTP Proxy (outgoing via Caddy) |
| `8381` | SOCKS5 Proxy (outgoing via Caddy) |
| `3858` | Admin API |

### 1.2 Default Mounts

*   **Docker Socket**: The module **MUST** mount the Docker socket to allow CITM to interact with the Docker daemon for service discovery.
    *   **Source**: `/var/run/docker.sock` (or auto-detected host path)
    *   **Target**: `/var/run/docker.sock`

### 1.3 Runtime Environment

*   **Docker Auto-detection**: Depending on the library/language, the module **SHOULD** attempt to automatically detect the Docker socket path (e.g., using `docker context inspect`) if the standard `DOCKER_HOST` environment variable is not set.

## 2. Configuration API (Builder Pattern)

The module should provide a fluent API (Builder) to configure the container.

### 2.1 Required Configuration

*   **`WithCertsDirectory(path)`**:
    *   **Description**: Path to a directory containing valid `rootCA.pem` and `rootCA-key.pem` files.
    *   **Action**: Bind mount this directory to `/certs` in the container.
    *   **Validation**: The builder should throw an error if this is not provided before building.

### 2.2 Optional Configuration

*   **`WithMocksDirectory(path)`**:
    *   **Description**: Path to a directory containing mock templates (e.g., `.mako` files).
    *   **Action**: Bind mount this directory to `/citm-mocks/` in the container.
    *   **Default Behavior**: If `WithMocksDirectory` is called but `WithMockPaths` is **not**, the module should automatically set the environment variable `MOCK_PATHS="/citm-mocks/**/*.mako"`.

*   **`WithMockPaths(patterns...)`**:
    *   **Description**: Glob patterns for mock files relative to the mocks directory.
    *   **Action**: Set the environment variable `MOCK_PATHS` to a comma-separated list of the provided patterns.
    *   **Validation & Normalization**:
        *   The module **MUST** normalize paths (e.g., resolving `..`) to prevent directory traversal.
        *   The module **MUST** validate that all resolved paths start with `/citm-mocks/`.
        *   The module **must** throw an error if a path attempts to escape the mocks directory.

*   **`WithCaddyfileDirectory(path)`**:
    *   **Description**: Path to a directory containing a custom `Caddyfile`.
    *   **Action**: Bind mount this directory to `/etc/caddy/conf.d`.

*   **`WithCitmNetwork(networkName)`**:
    *   **Description**: Connects the container to a specific Docker network.
    *   **Action**:
        1.  Connect the container to the specified network.
        2.  Add the label `citm_network=<networkName>` to the container.

*   **`WithDnsNames(names...)`**:
    *   **Description**: Sets custom DNS names for the container.
    *   **Action**: Add the label `citm_dns_names=<comma-separated-names>` to the container.

## 3. Helper Methods

The container instance should provide methods to easily access the exposed services. When resolving the `<host>`, if the container's hostname is a loopback IP (e.g., `127.0.0.1` or `::1`), it **SHOULD** be converted to `localhost` to allow for proper subdomain routing.

Some methods accept an optional list of subdomains. If provided, they are prepended to the host (e.g., `sub1.sub2.<host>`).

*   **`GetCaddyHttpBaseUrl(subdomains...)`**: Returns `http://[subdomains.]<host>:<mapped_port_80>`.
*   **`GetCaddyHttpsBaseUrl(subdomains...)`**: Returns `https://[subdomains.]<host>:<mapped_port_443>`.
*   **`GetHttpProxyAddress()`**: Returns `http://<host>:<mapped_port_8380>`.
*   **`GetSocksProxyAddress()`**: Returns `socks5://<host>:<mapped_port_8381>`.
*   **`GetAdminBaseUrl(subdomains...)`**: Returns `https://[subdomains.]<host>:<mapped_port_3858>`.
*   **`CreateHttpClientHandler(ignoreSslErrors=true)`**: Returns an HTTP client handler (or equivalent) configured to use the container's HTTP proxy. It should default to ignoring SSL errors (since CITM uses self-signed certs).

## 4. Certificate Generation Helper

The library **SHOULD** include a utility to generate valid self-signed Root CA certificates on the fly, as users often need this for ephemeral test environments.

### 4.1 Requirements

*   **Algorithm**: RSA 4096.
*   **Subject**: `CN=CITM Root CA`.
*   **Extensions**:
    *   **Basic Constraints**: CA=true, PathLenConstraint=None (Must allow downstream CA creation).
    *   **Key Usage**: DigitalSignature, KeyCertSign, CrlSign.
    *   **Subject Key Identifier**: Generated from public key.
*   **Validity**: 1 hour is sufficient for tests (or longer).
*   **Output Files**:
    *   `rootCA.pem` (Certificate PEM)
    *   `rootCA-key.pem` (Private Key PEM)
    *   `rootCA.cer` (Certificate DER/Binary - optional but strictly standard)

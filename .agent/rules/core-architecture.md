______________________________________________________________________

## trigger: always_on

# Core Architecture Rules

These rules define the structural guarantees and key decisions underlying the
`Caddy in the Middle` (CITM) project. This file dictates the container topology
and structural constraints for the project.

## 1. Container Image Structure

The primary artifact shipped by this project is a multi-stage Docker/OCI image.

- **Final Layer Context**: The `FROM` instruction in the final stage is based on
  `mitmproxy/mitmproxy`, meaning the final operating environment is **Debian
  Linux**. Modifications to the Dockerfile require the use of the appropriate
  package manager and tools. For example for Debian use `apt-get`, and for
  Alpine use `apk`.
- **Devcontainers Context**: This project supports development in devcontainers
  which can be enabled by a build flag. Enabling the flag will install some
  additional tools by running `.devcontainer/setup-devenv.sh`. Any new tools
  introduced during development must be included there.
- **Init System**: Process management within the container is exclusively
  handled by `supervisord`.
- **Sub-processes**: The container orchestrates several distinct services:
  - `caddy` (reverse proxy)
  - `dnsmasq` (DNS hijacking/routing)
  - `mitmproxy` (traffic inspection and endpoint mocking)
  - `citm-utils` (custom Python-based helper web services and tools)

## 2. Certificate Requirements

CITM is fundamentally reliant on intercepting encrypted traffic.

- **Mandatory Presence**: For the container to start successfully, a valid Root
  CA certificate must be present. Specifically, `/certs/rootCA.pem` and
  `/certs/rootCA-key.pem` must exist.
- **No Enforced Generation**: The container initialization script
  (`/start-supervisord`) strictly checks for the *existence* of these files but
  does not enforce, restrict, or mandate *how* they are generated beforehand.
  Testcontainers or the user are responsible for generating these and mounting
  them correctly.

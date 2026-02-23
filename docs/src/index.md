# Caddy in the Middle

Caddy in the Middle (CITM) is a containerized toolkit designed to facilitate the
configuration, inspection, and debugging of HTTP(S) communication in distributed
systems.

Debugging microservices architectures frequently requires the local management
of TLS certificates, reverse proxy configuration, traffic inspection, and
endpoint mocking. CITM addresses these requirements by integrating these
networking capabilities into a single Docker container.

______________________________________________________________________

## Core Capabilities

- **Automated Local HTTPS**: CITM utilizes a user-provided Root CA to
  dynamically sign leaf certificates for requested domains. This removes the
  need for manual certificate generation during local development.
- **Traffic Inspection and Routing**: Utilizes an embedded `mitmproxy` instance
  to capture HTTP(S) traffic and execute dynamic routing rules between internal
  services.
- **Programmable Endpoint Mocking**: Supports intercepting HTTP requests to
  serve file-based responses. Mocks are defined using the Mako templating
  engine. This allows for dynamic response generation via Python.
- **Container-Native Service Discovery**: Acts as an internal DNS server for its
  network stack. It monitors Docker container labels to map specified DNS names
  to container ip addresses. This isolates network configurations from the host
  machine.
- **Test Suite Integration**: Provides `Testcontainers` modules. These allow
  automated integration tests to programmatically provision and configure proxy
  instances.

______________________________________________________________________

## Documentation Structure

- **[Tutorials](./tutorials/getting-started.md)**: Step-by-step instructions for
  initial setup and basic usage.
- **[How-To Guides](./how-to/run-via-docker.md)**: Formatted procedures for
  specific tasks, such as configuring service discovery or authoring mock
  endpoints.
- **[Reference](./reference/configuration.md)**: Technical specifications
  covering environment variables, supported Docker labels, and module APIs.
- **[Explanation](./explanation/architecture.md)**: Documentation regarding the
  system architecture and internal request lifecycle.

______________________________________________________________________

## Next Steps

The **[Getting Started](./tutorials/getting-started.md)** tutorial provides
step-by-step instructions for a minimal setup.

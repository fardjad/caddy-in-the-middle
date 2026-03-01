# Caddy in the Middle

Caddy in the Middle (CITM) is a containerized toolkit for configuring,
inspecting, and debugging HTTP(S) communication in distributed systems.

CITM combines TLS termination, proxying, DNS service discovery, traffic
inspection, and endpoint mocking in one container image.

______________________________________________________________________

## Core Capabilities

- **Automated Local HTTPS**: Uses a provided Root CA to issue certificates for
  local domains through Caddy internal PKI.
- **Traffic Inspection and Routing**: Uses embedded `mitmproxy` for inspection,
  host rewrite routing, and protocol-aware flow handling.
- **Programmable Endpoint Mocking**: Supports file-based Mako mock templates
  loaded through `MOCK_PATHS`.
- **Container-Native Service Discovery**: Builds DNS records from Docker labels
  (`citm_network`, `citm_dns_names`).
- **Test Suite Integration**: Provides Testcontainers integrations for Python
  and .NET.

______________________________________________________________________

## Documentation Structure

- **[Tutorials](./tutorials/getting-started.md)**: Step-by-step learning paths.
- **[How-To Guides](./how-to/inspect-traffic-and-export-har.md)**: Task-oriented
  procedures for operations and configuration.
- **[Reference](./reference/runtime-configuration.md)**: Runtime contracts.
- **[Explanation](./explanation/architecture.md)**: Architecture, flows, and
  design tradeoffs.

______________________________________________________________________

## Next Steps

1. Follow the **[Getting Started](./tutorials/getting-started.md)** tutorial.
1. Use
   **[Inspect Traffic and Export HAR](./how-to/inspect-traffic-and-export-har.md)**
   for repeatable operational checks.
1. Use **[Runtime Configuration](./reference/runtime-configuration.md)** to
   confirm deployment contracts.

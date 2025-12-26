# Caddy in the Middle

> A developer-focused debugging toolkit for service-to-service communication

## Synopsis

Caddy in the Middle is a containerized toolkit that streamlines the setup, 
inspection, and debugging of HTTP(S) communication between services.

Working with distributed systems often involves complex debugging scenarios: 
certificate management, proxy configuration, traffic inspection, and endpoint 
mocking typically require significant manual setup. This project consolidates 
these tools into a containerized environment that enables developers to become 
productive within minutes.

## Why?

During development and debugging, common requirements include:

* Enabling HTTPS between services without certificate management overhead
* Routing traffic through a controllable proxy
* Inspecting and capturing requests and responses
* Mocking endpoints for testing scenarios
* Visualizing service communication patterns

Caddy in the Middle provides visibility and control over inter-service 
communication to address these needs.

## Features

Caddy in the Middle provides the following capabilities:

- **Automatic HTTPS Configuration** - Generates a Root CA for import into clients. 

- **Preconfigured Reverse Proxy with Traffic Capture** - Leverages Caddy as a reverse proxy and integrates mitmproxy for automatic traffic capture and inspection.

- **Developer-Friendly Networking** - `.localhost` domain resolves to the host machine IP address despite running in containers.

- **Traffic Visualization Tools** [In Progress] - Visual tools for understanding service communication patterns.

- **Lightweight Mocking Framework** [In Progress] - Built on top of mitmproxy for flexible endpoint mocking.

## Usage

The recommended deployment method is via Docker Compose:

```yaml
# compose.yml for Caddy in the Middle
services:
  citm:
    image: fardjad/citm:latest
    volumes:
      # User provided Caddy config files
      - ./caddy-conf.d:/etc/caddy/conf.d:ro
      # User provided MITMProxy scripts
      - ./mitm-scripts:/mitm-scripts:ro
      # The directory containing the rootCA and the key for on-demand TLS
      - ../shared-certificates/certs:/certs:ro
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"
```

## Example Configuration

Create a file named `example.Caddyfile` in your `./conf.d` directory to define 
routing rules:

```caddyfile
example.localhost {
	# Enable on-demand TLS certificate generation for this site
	import dev_certs
	
	reverse_proxy {
		# Ignored unless proxy is disabled with proxy_off macro
    # This must not be 'localhost' to ensure traffic routes through mitmproxy
		to mitm

		# Upstream target host (localhost resolves to host-gateway/host.docker.internal in containers)
		header_up X-MITM-To "localhost:8000"
		
		# Visual marker for easier flow identification in mitmproxy UI
		header_up X-MITM-Emoji ":gear:"
		
		# Standard reverse proxy headers
		header_up Host "example.localhost:80"
		header_up X-Forwarded-Host "example.localhost:80"
		
		# Uncomment when upstream server uses TLS
		# import tls_transport
		
		# Uncomment to bypass mitmproxy and connect directly to upstream
		# proxy_off
	}
}
```

This configuration:

- Enables automatic HTTPS for `example.localhost`
- Routes all traffic through mitmproxy for inspection
- Forwards requests to a service running on the host machine at port 8000
- Tags traffic with a visual emoji marker (`:gear:`) for easy identification in mitmproxy
- Sets appropriate headers for proper reverse proxying

The `X-MITM-To` header tells the system where to forward the request after 
inspection, while `localhost` inside the Caddy in the Middle container 
automatically resolves to the host machine.

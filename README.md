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

- **Lightweight Mocking Framework** - Built on top of mitmproxy for flexible endpoint mocking.

- **Traffic Visualization Tools** [In Progress] - Visual tools for understanding service communication patterns.

## Usage

TODO: rewrite in a user-friendly way
1. Add CITM to all services (side-car pattern, use the CITM service network for all other containers)
    1. Add the CITM container
    2. Mount the Docker socket (`/var/run/docker.sock:/var/run/docker.sock:ro`)
    3. Define the service names for containers with labels (e.g. `citm_name=service1.internal`)
2. Make sure CITM containers are part of the same network:
    1. One docker compose project with multiple containers
    2. Multiple docker compose projects all attached to a shared external isolated network

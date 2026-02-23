# Getting Started

This tutorial walks through the smallest useful setup for Caddy in the Middle
(CITM): one CITM gateway container and one `whoami` application container on the
same Docker network, with no sidecar.

### Prerequisites

The following tools are required:

- **Docker** and **Docker Compose**
- A Root CA certificate and key (`rootCA.pem`, `rootCA-key.pem`)
- **cURL**

Certificate generation is documented in
**[Development Root CA Generation](../how-to/create-dev-root-ca.md)**.

### Architecture

- **CITM gateway**: Exposes ports `80/443`, discovers labeled containers, and
  routes requests.
- **whoami**: A simple HTTP app that is registered in CITM DNS using Docker
  labels.

```mermaid
flowchart LR
    User([User]) -- "GET https://whoami.localhost" --> Gateway[CITM Gateway]
    Gateway -- "HTTP to whoami.internal:80" --> Whoami[whoami]
```

### Gateway Service

File: `compose.yml`

```yaml
services:
  citm:
    image: fardjad/citm:latest
    environment:
      - CITM_NETWORK=my-citm-network
    ports:
      - "443:443"
      - "443:443/udp"
      - "80:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./certs:/certs:ro
      - ./caddy-conf.d:/etc/caddy/conf.d:ro
    networks:
      - my-citm-network

networks:
  my-citm-network:
    name: my-citm-network
```

Gateway routing rules for public hostnames are defined in
`caddy-conf.d/whoami.conf`:

```caddy
whoami.localhost {
	import dev_certs

	reverse_proxy {
		# Send traffic through mitmproxy and forward to the labeled whoami target
		to mitm
		header_up X-MITM-To "whoami.internal:80"
		header_up Host "whoami.internal:80"
	}
}
```

### Backend Service

The application service is defined in the same `compose.yml` file:

```yaml
  whoami:
    image: traefik/whoami
    labels:
      # Register this container in CITM DNS (no sidecar required)
      - citm_network=my-citm-network
      - citm_dns_names=whoami.internal
    networks:
      - my-citm-network
```

### Inspecting the Environment

Stack startup command:

```bash
docker compose up -d
```

#### 1. External Access

External reachability check for `whoami` through the gateway:

```bash
curl -k https://whoami.localhost
```

#### 2. DNS Registration

DNS registration check for `whoami.internal` in CITM:

```bash
curl -s -k https://utils.citm.localhost
```

#### 3. Traffic Inspection

Traffic inspection is available at `https://mitm.citm.localhost`.

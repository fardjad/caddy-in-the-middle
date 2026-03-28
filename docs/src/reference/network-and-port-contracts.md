# Network and Port Contracts

## What it is

CITM exposes ingress, proxy, and admin interfaces. It also runs internal
processes behind `supervisord` in one container.

## Allowed values

### Exposed container ports

- `CADDY_HTTP_PORT/tcp`: HTTP ingress via Caddy
- `CADDY_HTTPS_PORT/tcp`: HTTPS ingress via Caddy
- `MITMPROXY_HTTP_PROXY_PORT/tcp`: HTTP proxy via mitmproxy
- `MITMPROXY_SOCKS_PROXY_PORT/tcp`: SOCKS5 proxy via mitmproxy
- `CADDY_ADMIN_PORT/tcp`: admin and utility virtual hosts through Caddy

### Internal service ports

- `CITM_UTILS_WEB_PORT/tcp`: `citm-utils-web` (Flask + gunicorn)
- `SUPERVISOR_WEBUI_PORT/tcp`: `supervisor-webui` (Flask + gunicorn)
- `MITMPROXY_WEB_PORT/tcp`: `mitmweb` UI backend
- `CITM_DNS_LISTEN_PORT/udp` and `CITM_DNS_LISTEN_PORT/tcp`: DNS forwarder
  listener

### Network membership

- CITM must be attached to the application network used in `citm_network`
  labels.
- Example workflows use external network `my-citm-network`.

## Defaults

- Default values are documented in [Default Ports](default-ports.md).
- Test environment runners can map exposed ports to random host ports.
- Example compose workflows map fixed host ports for local development.
- DNS forwarder listens on `CITM_DNS_LISTEN_HOST:CITM_DNS_LISTEN_PORT` unless
  overridden.

## Examples

```yaml
ports:
  - "0.0.0.0:80:80"
  - "0.0.0.0:443:443"
  - "0.0.0.0:443:443/udp"
  - "0.0.0.0:8380:${MITMPROXY_HTTP_PROXY_PORT:-19080}"
```

```bash
# Mapped host addresses in test environments:
# http://<host>:<mapped_${MITMPROXY_HTTP_PROXY_PORT}>
# socks5://<host>:<mapped_${MITMPROXY_SOCKS_PROXY_PORT}>
# https://<host>:<mapped_${CADDY_ADMIN_PORT}>
```

## Failure behavior

- Host port conflicts on mapped ingress or proxy ports: compose startup fails.
- Missing network attachment: discovered services are unreachable by internal
  DNS names.
- DNS forwarder bind failure on `CITM_DNS_LISTEN_PORT`:
  `citm-utils-dns-forwarder` process fails.

# Network and Port Contracts

## What it is

CITM exposes ingress, proxy, and admin interfaces. It also runs internal
processes behind `supervisord` in one container.

## Allowed values

### Exposed container ports

- `80/tcp`: HTTP ingress via Caddy
- `443/tcp`: HTTPS ingress via Caddy
- `8380/tcp`: HTTP proxy via mitmproxy
- `8381/tcp`: SOCKS5 proxy via mitmproxy
- `3858/tcp`: admin and utility virtual hosts through Caddy

### Internal service ports

- `5000/tcp`: `citm-utils-web` (Flask + gunicorn)
- `8382/tcp`: `mitmweb` UI backend
- `53/udp` and `53/tcp`: DNS forwarder listener

### Network membership

- CITM must be attached to the application network used in `citm_network`
  labels.
- Example workflows use external network `my-citm-network`.

## Defaults

- Test environment runners can map exposed ports to random host ports.
- Example compose workflows map fixed host ports for local development.
- DNS forwarder listens on `0.0.0.0:53` unless overridden.

## Examples

```yaml
ports:
  - "0.0.0.0:80:80"
  - "0.0.0.0:443:443"
  - "0.0.0.0:443:443/udp"
  - "0.0.0.0:8380:8380"
```

```bash
# Mapped host addresses in test environments:
# http://<host>:<mapped_8380>
# socks5://<host>:<mapped_8381>
# https://<host>:<mapped_3858>
```

## Failure behavior

- Host port conflicts on `80`, `443`, or `8380`: compose startup fails.
- Missing network attachment: discovered services are unreachable by internal
  DNS names.
- DNS forwarder bind failure on `53`: `citm-utils-dns-forwarder` process fails.

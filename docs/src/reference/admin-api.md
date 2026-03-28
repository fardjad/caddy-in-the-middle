# Admin API

## What it is

Admin endpoints are served through Caddy on `CADDY_ADMIN_PORT` and routed to
`citm-utils-web`, `supervisor-webui`, and `mitmweb`. Default values are
documented in [Default Ports](default-ports.md).

## Allowed values

### Endpoint contracts

1. Path `/` with method `GET` returns request metadata and `dns_entries`.
1. Path `/health` with method `GET` runs docker, DNS, and internal service
   checks.
1. Path `/har` with method `GET` generates HAR from `/mitm-dump/dump.flow`.
1. Path `/` with method `GET` on `supervisor.citm.*` returns supervisor UI HTML.
1. Path `/api/services` with method `GET` on `supervisor.citm.*` returns managed
   process list.
1. Path `/api/services/<name>/<action>` with method `POST` on
   `supervisor.citm.*` accepts `start`, `stop`, and `restart`.
1. Path `/api/services/restart-all` with method `POST` on `supervisor.citm.*`
   restarts all managed processes.

### Host routing contracts

1. Host `mitm.citm.*` on `CADDY_ADMIN_PORT` routes to internal `mitmweb` on
   `MITMPROXY_WEB_PORT`.
1. Host `utils.citm.*` on `CADDY_ADMIN_PORT` routes to internal `citm-utils-web`
   on `CITM_UTILS_WEB_PORT`.
1. Host `supervisor.citm.*` on `CADDY_ADMIN_PORT` routes to internal
   `supervisor-webui` on `SUPERVISOR_WEBUI_PORT`.

## Defaults

1. Health check DNS name is `citm.internal`.
1. Health check expects `https://citm.internal:${CADDY_ADMIN_PORT}` to return
   `404`.
1. Health check expects `https://mitm.citm.internal:${CADDY_ADMIN_PORT}` to
   return `200`.
1. HAR output path is `/mitm-dump/dump.har`.

## Examples

```bash
curl -k https://utils.citm.localhost
curl -k https://utils.citm.localhost/health
curl -k https://utils.citm.localhost/har -o dump.har
```

```bash
curl -k https://supervisor.citm.localhost/api/services
curl -k -X POST \
  https://supervisor.citm.localhost/api/services/mitmproxy/restart
```

## Failure behavior

1. Health check failure returns HTTP `503` from `/health`.
1. HAR lock contention returns HTTP `409` from `/har`.
1. HAR generation command failure returns HTTP `502` from `/har`.
1. Unsupported supervisor actions or blocked services return HTTP `400`.
1. Supervisor RPC failures return HTTP `502`.

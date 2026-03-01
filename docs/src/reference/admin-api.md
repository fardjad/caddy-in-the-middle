# Admin API

## What it is

Admin endpoints are served through Caddy on port `3858` and routed to
`citm-utils-web` and `mitmweb`.

## Allowed values

### Endpoint contracts

1. Path `/` with method `GET` returns request metadata and `dns_entries`.
1. Path `/health` with method `GET` runs docker, DNS, and internal service
   checks.
1. Path `/har` with method `GET` generates HAR from `/mitm-dump/dump.flow`.
1. Path `/supervisor` with method `GET` returns supervisor UI HTML.
1. Path `/supervisor/api/services` with method `GET` returns managed process
   list.
1. Path `/supervisor/api/services/<name>/<action>` with method `POST` accepts
   `start`, `stop`, and `restart`.
1. Path `/supervisor/api/services/restart-all` with method `POST` restarts all
   managed processes.

### Host routing contracts

1. Host `mitm.citm.*` on port `3858` routes to internal `mitmweb` on `8382`.
1. Host `utils.citm.*` on port `3858` routes to internal `citm-utils-web` on
   `5000`.

## Defaults

1. Health check DNS name is `citm.internal`.
1. Health check expects `https://citm.internal:3858` to return `404`.
1. Health check expects `https://mitm.citm.internal:3858` to return `200`.
1. HAR output path is `/mitm-dump/dump.har`.

## Examples

```bash
curl -k https://utils.citm.localhost
curl -k https://utils.citm.localhost/health
curl -k https://utils.citm.localhost/har -o dump.har
```

```bash
curl -k https://utils.citm.localhost/supervisor/api/services
curl -k -X POST \
  https://utils.citm.localhost/supervisor/api/services/mitmproxy/restart
```

## Failure behavior

1. Health check failure returns HTTP `503` from `/health`.
1. HAR lock contention returns HTTP `409` from `/har`.
1. HAR generation command failure returns HTTP `502` from `/har`.
1. Unsupported supervisor actions or blocked services return HTTP `400`.
1. Supervisor RPC failures return HTTP `502`.

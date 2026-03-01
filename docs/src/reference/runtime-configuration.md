# Runtime Configuration

## What it is

Runtime configuration is defined by bind mounts, labels, and environment
variables consumed by `Dockerfile`, `caddy`, `citm-utils`, and
`citm-utils-dns-forwarder`.

## Allowed values

### Required mounts

- `/certs/rootCA.pem` and `/certs/rootCA-key.pem` must exist.
- `/var/run/docker.sock` must be mounted for service discovery.

### Environment variables

- `CITM_NETWORK`: network name used for service discovery and examples.
- `CITM_DNS_NETWORK`: explicit DNS discovery network override.
- `CITM_DNS_CACHE_TTL_SECONDS`: positive float cache TTL.
- `CITM_DNS_LISTEN_HOST`: DNS forwarder bind host.
- `CITM_DNS_LISTEN_PORT`: positive integer DNS forwarder port.
- `CITM_DNS_UPSTREAM_TIMEOUT_SECONDS`: positive float timeout for upstream DNS.
- `MOCK_PATHS`: comma-separated file patterns for mock templates.
- `SUPERVISOR_SOCKET`: optional supervisor RPC socket path.

### Labels

- `citm_network=<network-name>`
- `citm_dns_names=<comma-separated-dns-names>`

## Defaults

- `CITM_DNS_CACHE_TTL_SECONDS=1.0`
- `CITM_DNS_LISTEN_HOST=0.0.0.0`
- `CITM_DNS_LISTEN_PORT=53`
- `CITM_DNS_UPSTREAM_TIMEOUT_SECONDS=2.0`
- DNS static records include `localhost` and `citm.internal` to `127.0.0.1`.
- If `CITM_DNS_NETWORK` is unset, discovery falls back to `CITM_NETWORK`.
- If `MOCK_PATHS` is unset, mock responder remains disabled.
- `SUPERVISOR_SOCKET` defaults to `/var/run/supervisor.sock`.

## Examples

```yaml
services:
  citm:
    image: fardjad/citm:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./certs:/certs:ro
      - ./mocks:/citm-mocks:ro
    environment:
      - CITM_NETWORK=my-citm-network
      - CITM_DNS_CACHE_TTL_SECONDS=1.0
      - MOCK_PATHS=/citm-mocks/**/*.mako
```

```yaml
labels:
  - citm_network=my-citm-network
  - citm_dns_names=api.internal,alt-api.internal
```

## Failure behavior

- Missing `/certs/rootCA.pem` or `/certs/rootCA-key.pem`: container exits before
  starting `supervisord`.
- Invalid numeric DNS environment values: value is ignored and defaults are
  used.
- Missing or invalid labels: service is excluded from discovery results.

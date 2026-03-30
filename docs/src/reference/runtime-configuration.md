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
- Runtime port variables are documented in [Default Ports](default-ports.md).
- `CITM_DNS_NETWORK`: explicit DNS discovery network override.
- `CITM_DNS_CACHE_TTL_SECONDS`: positive float cache TTL.
- `CITM_DNS_LISTEN_HOST`: DNS forwarder bind host.
- `CITM_DNS_LISTEN_PORT`: positive integer DNS forwarder port. See
  [Default Ports](default-ports.md).
- `CITM_DNS_UPSTREAM_NAMESERVERS`: optional explicit upstream DNS override. Use
  a comma-separated or space-separated list of IP addresses.
- `CITM_DNS_UPSTREAM_TIMEOUT_SECONDS`: positive float timeout for upstream DNS.
- `ENABLE_CADDY`: `true`, `false`, `1`, or `0`.
- `ENABLE_MITMPROXY`: `true`, `false`, `1`, or `0`.
- `ENABLE_PROXYLENS_SERVER`: `true`, `false`, `1`, or `0`.
- `PROXYLENS_NODE_NAME`: explicit ProxyLens node name for the local mitmproxy
  process. If unset, CITM defaults to the container hostname.
- `PROXYLENS_SERVER_BASE_URL`: explicit ProxyLens server base URL for the local
  mitmproxy process. If unset, CITM defaults to
  `http://127.0.0.1:${PROXYLENS_SERVER_PORT}` only when
  `ENABLE_PROXYLENS_SERVER=true`. Otherwise the addon remains disabled.
- `PROXYLENS_MAX_CONCURRENT_REQUESTS_PER_HOST`: optional positive integer
  concurrency limit per destination host for the local ProxyLens addon.
- `ENABLE_SUPERVISOR_WEBUI`: `true`, `false`, `1`, or `0`.
- `ENABLE_CITM_UTILS_DNS_FORWARDER`: `true`, `false`, `1`, or `0`.
- `MOCK_PATHS`: comma-separated file patterns for mock templates.
- `SUPERVISOR_SOCKET`: optional supervisor RPC socket path.

### Labels

- `citm_network=<network-name>`
- `citm_dns_names=<comma-separated-dns-names>`

## Defaults

- Runtime port defaults are documented in [Default Ports](default-ports.md).
- `CITM_DNS_CACHE_TTL_SECONDS=1.0`
- `CITM_DNS_LISTEN_HOST=0.0.0.0`
- `CITM_DNS_UPSTREAM_TIMEOUT_SECONDS=2.0`
- `ENABLE_CADDY=true`
- `ENABLE_MITMPROXY=true`
- `ENABLE_PROXYLENS_SERVER=false`
- `PROXYLENS_NODE_NAME=<container-hostname>`
- `PROXYLENS_SERVER_BASE_URL` is unset unless provided or derived from
  `ENABLE_PROXYLENS_SERVER=true`
- `PROXYLENS_MAX_CONCURRENT_REQUESTS_PER_HOST` is unset
- `ENABLE_SUPERVISOR_WEBUI=true`
- `ENABLE_CITM_UTILS_DNS_FORWARDER=true`
- DNS static records include `localhost` and `citm.internal` to `127.0.0.1`.
- If `CITM_DNS_NETWORK` is unset, discovery falls back to `CITM_NETWORK`.
- If `CITM_DNS_UPSTREAM_NAMESERVERS` is unset, upstream nameservers are read
  from `/etc/resolv.conf`.
- If `MOCK_PATHS` is unset, mock responder remains disabled.
- `SUPERVISOR_SOCKET` defaults to `/var/run/supervisor.sock`.
- ProxyLens Server stores data in the fixed container path `/var/lib/proxylens`.

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
      - CADDY_ADMIN_PORT=29058
      - MITMPROXY_HTTP_PROXY_PORT=29080
      - ENABLE_PROXYLENS_SERVER=true
      - PROXYLENS_NODE_NAME=gateway
      - PROXYLENS_SERVER_BASE_URL=http://proxylens-server.internal:19003
      - PROXYLENS_MAX_CONCURRENT_REQUESTS_PER_HOST=1
      - ENABLE_SUPERVISOR_WEBUI=false
      - CITM_DNS_CACHE_TTL_SECONDS=1.0
      - CITM_DNS_UPSTREAM_NAMESERVERS=1.1.1.1,8.8.8.8
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
- Invalid `CITM_DNS_UPSTREAM_NAMESERVERS` entries: invalid IPs are ignored.
- Invalid `ENABLE_*` values: value is ignored and the service remains enabled.
- Invalid `PROXYLENS_MAX_CONCURRENT_REQUESTS_PER_HOST`: startup fails in the
  local mitmproxy process.
- Missing or invalid labels: service is excluded from discovery results.

# Default Ports

## What it is

This reference defines the default runtime ports for CITM. The source of truth
is `hack/update_default_ports.py`.

## Defaults

- `CADDY_HTTP_PORT=80`: Exposed port for `caddy`. HTTP ingress.
- `CADDY_HTTPS_PORT=443`: Exposed port for `caddy`. HTTPS ingress.
- `CADDY_ADMIN_PORT=63858`: Exposed port for `caddy`. Admin and utility virtual
  hosts.
- `MITMPROXY_HTTP_PROXY_PORT=19080`: Exposed port for `mitmproxy`. HTTP proxy
  listener.
- `MITMPROXY_SOCKS_PROXY_PORT=19081`: Exposed port for `mitmproxy`. SOCKS5 proxy
  listener.
- `MITMPROXY_WEB_PORT=19082`: Internal port for `mitmweb`. Web UI backend.
- `CITM_UTILS_WEB_PORT=19000`: Internal port for `citm-utils-web`. Utility API
  listener.
- `SUPERVISOR_WEBUI_PORT=19001`: Internal port for `supervisor-webui`.
  Supervisor UI listener.
- `PROXYLENS_SERVER_PORT=19003`: Internal port for `proxylens-server`. ProxyLens
  API listener.
- `CITM_DNS_LISTEN_PORT=53`: Internal port for `citm-utils-dns-forwarder`. DNS
  listener.

## Overrides

Override any of these defaults by setting environment variables on the CITM
container.

```yaml
services:
  citm:
    image: fardjad/citm:latest
    environment:
      - CADDY_ADMIN_PORT=29058
      - MITMPROXY_HTTP_PROXY_PORT=29080
      - MITMPROXY_SOCKS_PROXY_PORT=29081
      - MITMPROXY_WEB_PORT=29082
      - CITM_UTILS_WEB_PORT=29000
      - SUPERVISOR_WEBUI_PORT=29001
      - CITM_DNS_LISTEN_PORT=5300
```

Container-side port overrides do not change host-side `ports:` mappings in
Compose. Update host mappings separately when you need fixed host ports.

If `CITM_DNS_LISTEN_PORT=53`, CITM rewrites `/etc/resolv.conf` to use
`127.0.0.1`. If `CITM_DNS_LISTEN_PORT` is not `53`, CITM leaves
`/etc/resolv.conf` unchanged and logs a startup warning.

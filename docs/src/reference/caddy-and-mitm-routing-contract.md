# Caddy and MITM Routing Contract

## What it is

Caddy terminates TLS and forwards traffic to mitmproxy. The `rewrite_host` addon
uses request headers to route the upstream target and mark flows.

## Allowed values

1. Header `X-MITM-To` is required for target rewrite. Format must be
   `<host>:<port>`. Port must be numeric and in range `1..65535`.
1. Header `X-MITM-Emoji` is optional. The value should be a supported GitHub
   emoji token such as `:rocket:` or `:one:` from the
   [GitHub Emoji API](https://api.github.com/emojis).
1. Caddy snippet `import dev_certs` enables on-demand TLS with the internal CA
   loaded from `/certs/rootCA.pem` and `/certs/rootCA-key.pem`.

## Defaults

1. Missing `X-MITM-To` means request target is not rewritten.
1. Missing `X-MITM-Emoji` means no flow mark is applied.
1. The original host header is preserved before upstream rewrite.

## Examples

```caddy
whoami.localhost {
  import dev_certs

  reverse_proxy {
    to mitm
    header_up X-MITM-To "whoami.internal:80"
    header_up X-MITM-Emoji ":one:"
    header_up Host "whoami.internal:80"
  }
}
```

## Failure behavior

1. Invalid `X-MITM-To` causes request blocking in `rewrite_host`.
1. Blocked requests are marked with warning metadata and an error comment.
1. Unknown `*.citm.*` utility hosts in base Caddyfile return HTTP `404`.

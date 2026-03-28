# Configure Caddy Layers

## Goal

Provide additional Caddy config, replace CITM-specific Caddy config, or replace
the packaged global options.

## Configuration Layers

CITM loads Caddy config in this order:

1. `/etc/caddy/global-options.Caddyfile`
1. `/etc/caddy/citm.d/*`
1. `/etc/caddy/conf.d/*`

`/etc/caddy/Caddyfile` is the loader file. It imports the three layers above.

Use each layer for a different purpose:

1. Use `/etc/caddy/conf.d/` for additional user-defined sites and snippets.
1. Replace files under `/etc/caddy/citm.d/` only when changing packaged
   CITM-specific behavior such as `dev_certs` or the `*.citm.*` admin routes.
1. Replace `/etc/caddy/global-options.Caddyfile` only when changing global Caddy
   options such as ports, logging, or PKI configuration.

## Add User Caddy Config

Mount a directory to `/etc/caddy/conf.d` when adding routes for application
hostnames.

```yaml
services:
  citm:
    image: fardjad/citm:latest
    volumes:
      - ./caddy-conf.d:/etc/caddy/conf.d:ro
```

Example file: `./caddy-conf.d/whoami.conf`

```caddy
whoami.localhost {
	import dev_certs

	reverse_proxy {
		to mitm
		header_up X-MITM-To "whoami.internal:80"
		header_up Host "whoami.internal:80"
	}
}
```

This keeps user config separate from CITM-owned files.

## Replace CITM-Specific Config

Mount a file over `/etc/caddy/citm.d/citm.Caddyfile` when changing the packaged
`dev_certs` snippet or the built-in `citm.internal` and `*.citm.*` admin routes.

```yaml
services:
  citm:
    image: fardjad/citm:latest
    volumes:
      - ./caddy-overrides/citm.Caddyfile:/etc/caddy/citm.d/citm.Caddyfile:ro
```

Use this only if the replacement still provides the behavior your deployment
needs. Removing `dev_certs` or the admin routes changes the default CITM
contract.

## Replace Global Options

Mount a file over `/etc/caddy/global-options.Caddyfile` when changing the global
options block.

```yaml
services:
  citm:
    image: fardjad/citm:latest
    volumes:
      - ./caddy-overrides/global-options.Caddyfile:/etc/caddy/global-options.Caddyfile:ro
```

Example file: `./caddy-overrides/global-options.Caddyfile`

```caddy
{
	default_bind 0.0.0.0
	http_port {$CADDY_HTTP_PORT}
	https_port {$CADDY_HTTPS_PORT}

	log {
		format console
		output stdout
		level INFO
	}

	skip_install_trust

	pki {
		ca citm {
			root {
				cert /certs/rootCA.pem
				key /certs/rootCA-key.pem
			}
		}
	}
}
```

Use this only when the default global block is insufficient. Invalid global
options can prevent Caddy from starting.

## Verification

1. Start the stack.

```bash
docker compose up -d --wait --pull always --build --force-recreate
```

2. Verify the utility API is reachable.

```bash
curl -k https://utils.citm.localhost
```

3. Verify a user-defined route if `/etc/caddy/conf.d/` was mounted.

```bash
curl -k https://whoami.localhost
```

## Troubleshooting

1. Symptom: custom application routes are missing. Action: verify the host
   directory is mounted to `/etc/caddy/conf.d`.
1. Symptom: `import dev_certs` fails. Action: verify the CITM-specific config
   still defines the `dev_certs` snippet.
1. Symptom: Caddy does not start after replacing the global options file.
   Action: validate the replacement syntax and required PKI paths.

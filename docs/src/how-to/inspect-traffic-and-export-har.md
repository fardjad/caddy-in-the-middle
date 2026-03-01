# Inspect Traffic and Export HAR

## Goal

Inspect captured requests in `mitmweb` and export flows as HAR from the CITM
utility API.

## Prerequisites

- Docker and Docker Compose
- `just`
- A running stack with CITM gateway exposure, for example
  `examples/getting-started` or `examples/gateway-and-sidecars`
- `curl`

## Steps

1. Start a stack.

```bash
cd examples/getting-started
just up
```

2. Generate traffic.

```bash
curl -k https://whoami.localhost
```

3. Open `mitmweb` through the gateway at `https://mitm.citm.localhost`.

1. Export HAR from the utility API.

```bash
curl -k https://utils.citm.localhost/har -o dump.har
```

## Verification

Run these checks:

```bash
ls -l dump.har
head -n 5 dump.har
```

Expected result: valid HAR JSON generated from `/mitm-dump/dump.flow`.

## Troubleshooting

1. Symptom: `/har` returns HTTP `409`. Cause: another HAR generation request is
   active. Action: retry after the active request completes.
1. Symptom: `/har` returns HTTP `502`. Cause: `mitmdump` HAR conversion failed.
   Action: inspect logs for `citm-utils-web` and `mitmproxy`.
1. Symptom: `mitm` UI has no flows. Cause: no traffic reached CITM. Action: send
   traffic again through configured domains or proxy settings.

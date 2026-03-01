# Configure Service Discovery

## Goal

Register container DNS names in CITM and resolve them through the internal DNS
forwarder.

## Prerequisites

- Docker and Docker Compose
- `just`
- A running network named `my-citm-network`
- One CITM container with Docker socket mounted

## Steps

1. Add labels to each discoverable container.

```yaml
labels:
  - citm_network=my-citm-network
  - citm_dns_names=api.internal,alt-api.internal
```

2. Set the gateway network in CITM.

```yaml
environment:
  - CITM_NETWORK=my-citm-network
```

3. Start services.

```bash
docker compose up -d --wait --pull always --build --force-recreate
```

4. Query registered entries through the utility endpoint.

```bash
curl -k https://utils.citm.localhost
```

## Verification

1. Confirm `dns_entries` contains expected names and IPs.
1. For proxy-mode workflow, verify direct target access by DNS name.

```bash
export http_proxy=http://127.0.0.1:8380
export https_proxy=http://127.0.0.1:8380
curl http://whoami.internal
```

Expected result: HTTP `200` from target service.

## Troubleshooting

1. Symptom: name is missing from `dns_entries`. Cause: label typo or network
   mismatch. Action: verify exact keys `citm_network` and `citm_dns_names`.
1. Symptom: name resolves intermittently. Cause: short cache TTL and container
   churn. Action: verify container is running and attached to labeled network.
1. Symptom: name is unresolved in proxy mode. Cause: proxy environment variables
   are unset. Action: export `http_proxy` and `https_proxy` to the CITM HTTP
   proxy port.

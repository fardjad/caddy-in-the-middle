# Author Mock Templates

## Goal

Create file-based mock responses loaded by the CITM `mock_responder` addon.

## Prerequisites

- Docker and Docker Compose
- `just`
- A CITM service with mounted mocks directory
- `MOCK_PATHS` environment variable configured

## Steps

1. Mount mock files into `/citm-mocks`.

```yaml
volumes:
  - ./mocks:/citm-mocks:ro
environment:
  - MOCK_PATHS=/citm-mocks/**/*.mako
```

2. Create a mock file, for example `mocks/books.mako`.

```text
GET ~*://*/books

200
Content-Type: application/json
X-Source: mock

---
[
  {"id": 10, "title": "Design Patterns"}
]
```

3. Start or restart the stack.

```bash
docker compose up -d --wait --pull always --build --force-recreate
```

4. Call the endpoint through CITM.

```bash
curl -k -i https://books.localhost/books
```

## Verification

1. Response status matches template status.
1. Response headers include template headers.
1. Response body matches rendered content after the `---` separator.

## Troubleshooting

1. Symptom: mock is not applied. Cause: `MOCK_PATHS` is unset or the glob does
   not match files. Action: verify mount path and glob pattern.
1. Symptom: parser warning for template. Cause: request line or status block
   format is invalid. Action: ensure first line is `METHOD URL` and status is
   integer.
1. Symptom: external fetch returns empty body. Cause: `@@` target fetch failed.
   Action: check target URL reachability from inside CITM container.

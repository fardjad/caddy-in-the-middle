# Mock Template Format

## What it is

Mock files define response overrides loaded by the `mock_responder` mitmproxy
addon from `MOCK_PATHS` patterns.

## Allowed values

### File layout

1. The first section is required. It must contain request line `METHOD URL`.
1. The second section is required. First line is integer status code.
1. Additional lines in section two are optional headers in `Key: Value` format.
1. The third section is optional template remainder.

### Matching contract

1. Exact match uses the URL exactly as written.
1. Wildcard match uses `~` prefix and `fnmatch` pattern matching.

### Rendering contract

1. Mako template context provides `flow`.
1. Mako code blocks such as `<% ... %>` can appear before `---`.
1. If rendered output contains `---\n`, response body is text after separator.
1. If rendered body starts with `@@`, first line target URL is fetched.
1. HTTP/2 and HTTP/3 responses remove disallowed hop-by-hop headers.

## Defaults

1. Missing remainder section produces empty body.
1. Mako render errors return raw remainder text.
1. Malformed header lines are skipped.
1. External fetch failures return mock status and headers with empty body.

## Examples

### Example 1: Exact URL JSON response

```text
GET https://books.localhost/books

200
Content-Type: application/json
X-Source: mock

---
[
  {"id": 1, "title": "Exact Match"}
]
```

### Example 2: Wildcard path match

```text
GET ~*://*/books/*

200
Content-Type: application/json

---
{"match":"wildcard path"}
```

### Example 3: Method-specific behavior

```text
POST ~*://*/books

201
Content-Type: application/json

---
{"created":true}
```

### Example 4: Header-only response with empty body

```text
GET https://api.localhost/health

204
X-Source: mock
```

### Example 5: Mako template using request URL

```text
GET ~*://*/echo

200
Content-Type: text/plain

---
${flow.request.method} ${flow.request.url}
```

### Example 6: Mako template using request host header

```text
GET ~*://*/whoami

200
Content-Type: application/json

---
{"host":"${flow.request.headers.get('Host', '')}"}
```

### Example 7: External fetch body

```text
GET https://assets.localhost/docs

200
Content-Type: text/html

@@https://example.com/
```

### Example 8: Wildcard for any scheme and host

```text
GET ~*://*/books

200
Content-Type: application/json
X-Source: mock

---
[
  {"id": 10, "title": "Scheme and Host Wildcard"}
]
```

### Example 9: HTTP error simulation

```text
GET ~*://*/upstream

502
Content-Type: application/json

---
{"error":"upstream unavailable"}
```

### Example 10: Minimal text response

```text
GET https://demo.localhost/ping

200
Content-Type: text/plain

---
ok
```

### Example 11: HTTPS wildcard with query passthrough text

```text
GET ~https://*/search*

200
Content-Type: text/plain

---
search mocked
```

### Example 12: Multiple custom headers

```text
GET https://status.localhost/info

200
Content-Type: application/json
Cache-Control: no-store
X-Source: mock

---
{"status":"ok"}
```

### Example 13: Code block before separator

```text
GET https://pre-separator.example/subscriptions/alpha

200
Content-Type: application/xml
X-Scenario: pre-separator

<%
    segments = flow.request.path.strip("/").split("/")
    resource = segments[0]
    item_id = segments[-1]
%>
---
<result resource="${resource}" id="${item_id}"/>
```

Result behavior:

1. The `<% ... %>` block executes during rendering.
1. The response body starts after `---`.
1. The resulting body is `<result resource="subscriptions" id="alpha"/>`.

## Failure behavior

1. Invalid request line causes file skip.
1. Invalid status line causes file skip.
1. Non-matching patterns pass request to upstream.
1. Unset `MOCK_PATHS` disables `mock_responder`.

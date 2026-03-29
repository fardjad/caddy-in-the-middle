GET https://external.example/data

206
Content-Type: application/json
X-Mock-Override: from-mock

---
@@${flow.request.headers["X-Upstream-URL"]}

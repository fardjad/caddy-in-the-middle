GET ~https://service.example/orders/*

202
Content-Type: text/plain
X-Scenario: wildcard

---
Matched order path ${flow.request.path}

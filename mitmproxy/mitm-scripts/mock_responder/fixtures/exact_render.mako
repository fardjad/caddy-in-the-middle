GET https://service.example/api/users

201
Content-Type: text/plain
X-Scenario: exact

---
Hello ${flow.request.host} ${flow.request.path}

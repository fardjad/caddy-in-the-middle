GET ~https://compat.example/*

200
Content-Type: text/plain

---
Host=${flow.request.headers["Host"]}

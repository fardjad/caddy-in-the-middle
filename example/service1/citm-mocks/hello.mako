GET ~*/hello

200
Content-Type: text/html

<%
    body = f"Hello from {flow.request.host}!"
%>
---
<!doctype html>
<h1>Hello</h1>

<p>${body}<p>
<p>This is a mocked response!</p>
Click <a href="https://mitm.citm.${flow.request.host}">here</a> to see the 
captured requests and responses.
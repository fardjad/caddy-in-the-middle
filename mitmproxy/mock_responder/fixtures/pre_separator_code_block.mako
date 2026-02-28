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

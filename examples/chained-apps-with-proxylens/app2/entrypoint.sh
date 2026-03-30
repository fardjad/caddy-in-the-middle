#!/bin/sh
set -eu

# Trust the shared CITM root CA before the app starts so outbound HTTPS
# requests to intercepted internal services validate successfully.
cp /certs/rootCA.pem /usr/local/share/ca-certificates/citm-root-ca.crt
update-ca-certificates >/dev/null 2>&1

exec dotnet /app/app2.dll

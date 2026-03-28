#!/usr/bin/env bash

set -euo pipefail

COMMON_TIP_MESSAGE="Did you run the certificate maker script?"

if [ ! -f /certs/rootCA.pem ]; then
	echo "ERROR: /certs/rootCA.pem not found. ${COMMON_TIP_MESSAGE}" >&2
	exit 1
fi

if [ ! -f /certs/rootCA-key.pem ]; then
	echo "ERROR: /certs/rootCA-key.pem not found. ${COMMON_TIP_MESSAGE}" >&2
	exit 1
fi

install -m 644 -o root -g root "/certs/rootCA.pem" /usr/local/share/ca-certificates/citm-root-ca.crt
update-ca-certificates

exec supervisord "$@"

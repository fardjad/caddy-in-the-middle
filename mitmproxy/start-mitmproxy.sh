#!/usr/bin/env bash

set -euo pipefail

cat /certs/rootCA-key.pem /certs/rootCA.pem >/root/.mitmproxy/mitmproxy-ca.pem
chmod -R 644 /root/.mitmproxy/*

SCRIPT_ARGS="-s /mock-responder.py -s /rewrite-host.py"
if [ -d "/mitm-scripts" ]; then
	SCRIPT_ARGS+=" $(ls /mitm-scripts/*.py | sort | awk '{print "-s "$1}')"
fi

mkdir -p /mitm-dump
rm -f /mitm-dump/dump.flow

mitmweb \
	--mode regular@8380 \
	--mode socks5@8381 \
	-w /mitm-dump/dump.flow \
	--set ssl_insecure=true \
	--set web_port=8382 \
	--set web_password=secret \
	--set block_global=false \
	--set web_host=0.0.0.0 \
	--set connection_strategy=lazy \
	--set keep_host_header=true \
	--set "dns_name_servers=127.0.0.1" \
	--set dns_use_hosts_file=false \
	${SCRIPT_ARGS}

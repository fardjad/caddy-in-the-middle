#!/usr/bin/env bash

set -euo pipefail

MITMPROXY_DATA_DIR="/var/lib/mitmproxy"

# BEGIN GENERATED DEFAULT PORTS
HTTP_PROXY_PORT="${MITMPROXY_HTTP_PROXY_PORT:-19080}"
SOCKS_PROXY_PORT="${MITMPROXY_SOCKS_PROXY_PORT:-19081}"
WEB_PORT="${MITMPROXY_WEB_PORT:-19082}"
DNS_LISTEN_PORT="${CITM_DNS_LISTEN_PORT:-53}"
# END GENERATED DEFAULT PORTS

cat /certs/rootCA-key.pem /certs/rootCA.pem >/root/.mitmproxy/mitmproxy-ca.pem
chmod -R 644 /root/.mitmproxy/*

SCRIPT_ARGS=""

if [ -d "/mitm-scripts" ]; then
	while IFS= read -r script; do
		SCRIPT_ARGS+=" -s ${script}"
	done < <(find /mitm-scripts -maxdepth 1 -type f -name "*.py" | sort)
fi

mkdir -p "${MITMPROXY_DATA_DIR}"
rm -f "${MITMPROXY_DATA_DIR}/dump.flow"

DNS_ARGS=()
if [ "${DNS_LISTEN_PORT}" = "53" ]; then
	DNS_ARGS+=(--set "dns_name_servers=127.0.0.1")
else
	echo "WARNING: CITM DNS forwarder is configured for port ${DNS_LISTEN_PORT}. mitmproxy will use the system resolver instead of CITM DNS interception." >&2
fi

uv run mitmweb \
	--mode regular@"${HTTP_PROXY_PORT}" \
	--mode socks5@"${SOCKS_PROXY_PORT}" \
	-w "${MITMPROXY_DATA_DIR}/dump.flow" \
	--set ssl_insecure=true \
	--set web_port="${WEB_PORT}" \
	--set web_password=secret \
	--set block_global=false \
	--set web_host=0.0.0.0 \
	--set connection_strategy=lazy \
	--set keep_host_header=true \
	--set dns_use_hosts_file=false \
	--set stream_large_bodies=1 \
	--set store_streamed_bodies=true \
	"${DNS_ARGS[@]}" \
	${SCRIPT_ARGS}

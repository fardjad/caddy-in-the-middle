#!/usr/bin/env bash

set -euo pipefail

COMMON_TIP_MESSAGE="Did you run the certificate maker script?"
SOURCE_CONF_DIR="/etc/supervisor/conf.d"
ENABLED_CONF_DIR="/etc/supervisor/enabled-conf.d"

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

is_enabled() {
	local env_name="$1"
	local value="${!env_name:-}"

	case "${value,,}" in
	"" | "1" | "true")
		return 0
		;;
	"0" | "false")
		return 1
		;;
	*)
		echo "WARNING: ${env_name}=${value} is invalid. Expected true, false, 1, or 0. Defaulting to enabled." >&2
		return 0
		;;
	esac
}

copy_if_enabled() {
	local env_name="$1"
	local source_file="$2"
	local target_name="$3"

	if is_enabled "${env_name}"; then
		cp "${source_file}" "${ENABLED_CONF_DIR}/${target_name}"
		return
	fi

	echo "INFO: ${env_name}=false. Skipping ${target_name}." >&2
}

mkdir -p "${ENABLED_CONF_DIR}"
find "${ENABLED_CONF_DIR}" -type f -name "*.conf" -delete

copy_if_enabled "ENABLE_CADDY" "${SOURCE_CONF_DIR}/caddy.conf" "caddy.conf"
copy_if_enabled "ENABLE_MITMPROXY" "${SOURCE_CONF_DIR}/mitmproxy.conf" "mitmproxy.conf"
copy_if_enabled "ENABLE_SUPERVISOR_WEBUI" "${SOURCE_CONF_DIR}/webui.conf" "webui.conf"
cp "${SOURCE_CONF_DIR}/citm-utils-web.conf" "${ENABLED_CONF_DIR}/citm-utils-web.conf"
copy_if_enabled \
	"ENABLE_CITM_UTILS_DNS_FORWARDER" \
	"${SOURCE_CONF_DIR}/citm-utils-dns-forwarder.conf" \
	"citm-utils-dns-forwarder.conf"

exec supervisord "$@"

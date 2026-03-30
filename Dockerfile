# syntax=docker/dockerfile:1

FROM alpine AS setup-devenv

ARG DEVCONTAINER="false"

COPY .devcontainer/setup-devenv.sh /setup-devenv.sh
COPY <<EOF /setup-devenv-noop.sh
#!/usr/bin/env bash

echo "This image is built without development tools."
echo "To install development tools, build the image with DEVCONTAINER=true build argument."
EOF
RUN /bin/ash <<EOF
if [ "${DEVCONTAINER}" = "false" ]; then
    cp /setup-devenv-noop.sh /setup-devenv.sh
fi
EOF

FROM debian:trixie

# BEGIN GENERATED DEFAULT PORT ENV
ENV CADDY_HTTP_PORT=80 \
    CADDY_HTTPS_PORT=443 \
    CADDY_ADMIN_PORT=63858 \
    MITMPROXY_HTTP_PROXY_PORT=19080 \
    MITMPROXY_SOCKS_PROXY_PORT=19081 \
    MITMPROXY_WEB_PORT=19082 \
    CITM_UTILS_WEB_PORT=19000 \
    SUPERVISOR_WEBUI_PORT=19001 \
    PROXYLENS_SERVER_PORT=19003 \
    CITM_DNS_LISTEN_PORT=53
# END GENERATED DEFAULT PORT ENV

ENV CITM_DNS_LISTEN_HOST=0.0.0.0
ENV MITMPROXY_DATA_DIR=/var/lib/mitmproxy
ENV PROXYLENS_SERVER_DATA_DIR=/var/lib/proxylens

# Common tools
RUN <<EOF
apt-get update -y
apt-get install -y bash ca-certificates curl iputils-ping socat supervisor util-linux
EOF
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Dev Env
COPY --from=setup-devenv /setup-devenv.sh /setup-devenv.sh
RUN /bin/bash /setup-devenv.sh && rm /setup-devenv.sh

# Supervisor Web UI
COPY supervisor/webui /supervisor/webui
WORKDIR /supervisor/webui
RUN rm -rf .venv __pycache__ && uv sync

# Supervisord
RUN <<EOF
rm -rf /etc/supervisor
mkdir -p /var/log/supervisor
mkdir -p /var/run
mkdir -p /etc/supervisor/conf.d
mkdir -p /etc/supervisor/enabled-conf.d
EOF
COPY supervisor/supervisord.conf /etc/supervisor/supervisord.conf
COPY supervisor/conf.d/webui.conf /etc/supervisor/conf.d/webui.conf

# Caddy
COPY --from=caddy:2 /usr/bin/caddy /usr/bin/caddy
RUN mkdir -p /etc/caddy /etc/caddy/conf.d /etc/caddy/citm.d
COPY ./caddy/Caddyfile /etc/caddy/Caddyfile
COPY ./caddy/global-options.Caddyfile /etc/caddy/global-options.Caddyfile
COPY ./caddy/citm.d /etc/caddy/citm.d
COPY supervisor/conf.d/caddy.conf /etc/supervisor/conf.d/caddy.conf

# MITM Proxy
RUN mkdir -p /root/.mitmproxy
RUN mkdir -p "${MITMPROXY_DATA_DIR}"
COPY ./mitmproxy/mitm-scripts /mitm-scripts
WORKDIR /mitm-scripts
RUN rm -rf .venv __pycache__ && uv sync
VOLUME ["/var/lib/mitmproxy"]
COPY --chown=root:root --chmod=755 ./mitmproxy/start-mitmproxy.sh /usr/local/bin/start-mitmproxy
COPY supervisor/conf.d/mitmproxy.conf /etc/supervisor/conf.d/mitmproxy.conf

# ProxyLens Server
COPY --from=docker.io/fardjad/proxylens:0.4.3 /proxy-lens /proxy-lens
WORKDIR /proxy-lens/server
RUN rm -rf .venv __pycache__ && uv sync --no-dev
RUN uv add --no-sync gunicorn
RUN uv sync --no-dev
RUN mkdir -p "${PROXYLENS_SERVER_DATA_DIR}"
VOLUME ["/var/lib/proxylens"]
COPY --chmod=755 ./proxylens/start-proxylens-server.sh /usr/local/bin/start-proxylens-server
COPY supervisor/conf.d/proxylens-server.conf /etc/supervisor/conf.d/proxylens-server.conf

# CITM Utils
COPY citm-utils /citm-utils
WORKDIR /citm-utils
RUN rm -rf .venv __pycache__ && uv sync
COPY supervisor/conf.d/citm-utils-web.conf /etc/supervisor/conf.d/citm-utils-web.conf
COPY supervisor/conf.d/citm-utils-dns-forwarder.conf /etc/supervisor/conf.d/citm-utils-dns-forwarder.conf
COPY --chmod=755 supervisor/start-supervisord.sh /start-supervisord

HEALTHCHECK --interval=5s --timeout=5s --start-period=5s --retries=60 \
    CMD curl -fsS \
    --connect-timeout 3 \
    http://127.0.0.1:${CITM_UTILS_WEB_PORT}/health \
    || exit 1

CMD ["/start-supervisord"]
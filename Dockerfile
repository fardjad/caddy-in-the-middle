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

FROM mitmproxy/mitmproxy

# Common tools
RUN <<EOF
apt-get update -y
apt-get install -y socat curl iputils-ping ca-certificates
EOF
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Dev Env
COPY --from=setup-devenv /setup-devenv.sh /setup-devenv.sh
RUN /bin/bash /setup-devenv.sh && rm /setup-devenv.sh

# Supervisord
RUN <<EOF
apt-get update -y
apt-get install -y supervisor

rm -rf /etc/supervisor
mkdir -p /var/log/supervisor
mkdir -p /var/run
mkdir -p /etc/supervisor/conf.d
EOF
COPY supervisor/supervisord.conf /etc/supervisor/supervisord.conf

# Caddy
COPY --from=caddy:2 /usr/bin/caddy /usr/bin/caddy
RUN mkdir -p /etc/caddy && mkdir -p /etc/caddy/conf.d
COPY ./caddy/Caddyfile /etc/caddy/Caddyfile
COPY supervisor/conf.d/caddy.conf /etc/supervisor/conf.d/caddy.conf

# MITM Proxy
RUN mkdir -p /root/.mitmproxy
COPY --chown=root:root --chmod=755 ./mitmproxy/start-mitmproxy.sh /usr/local/bin/start-mitmproxy
COPY ./mitmproxy/rewrite-host.py /rewrite-host.py
COPY ./mitmproxy/mock-responder.py /mock-responder.py
COPY ./mitmproxy/rewrite_host /rewrite_host
COPY ./mitmproxy/mock_responder /mock_responder
COPY supervisor/conf.d/mitmproxy.conf /etc/supervisor/conf.d/mitmproxy.conf

# CITM Utils
RUN uv pip install --system mako
COPY citm-utils /citm-utils
WORKDIR /citm-utils
RUN rm -rf .venv __pycache__ && uv sync
COPY supervisor/conf.d/citm-utils.conf /etc/supervisor/conf.d/citm-utils.conf
COPY --chmod=755 supervisor/start-supervisord.sh /start-supervisord

HEALTHCHECK --interval=5s --timeout=5s --start-period=5s --retries=60 \
    CMD curl -fsS \
    --connect-timeout 3 \
    https://utils.citm.internal:3858/health \
    || exit 1

CMD ["/start-supervisord"]
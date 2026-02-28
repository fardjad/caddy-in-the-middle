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
if [ "${DEVCONTAINER}" == "false" ]; then
    cp /setup-devenv-noop.sh /setup-devenv.sh
fi
EOF

# 2.11.1 breaks CITM
# https://github.com/caddyserver/caddy/issues/7520
FROM caddy:2.10.2 AS caddy

FROM mitmproxy/mitmproxy

# Common tools
RUN <<EOF
apt-get update -y
apt-get install -y socat curl iputils-ping ca-certificates
EOF

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

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

COPY <<EOF /etc/supervisor/supervisord.conf
; supervisor config file

[unix_http_server]
file=/var/run/supervisor.sock
chmod=0700

[supervisord]
nodaemon=true
logfile=/var/log/supervisor/supervisord.log
childlogdir=/var/log/supervisor

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock

[include]
files = /etc/supervisor/conf.d/*.conf
EOF

# Caddy

COPY --from=caddy /usr/bin/caddy /usr/bin/caddy
RUN mkdir -p /etc/caddy && mkdir -p /etc/caddy/conf.d
COPY ./caddy/Caddyfile /etc/caddy/Caddyfile

COPY <<EOF /etc/supervisor/conf.d/caddy.conf
[program:caddy]
command=/usr/bin/caddy run --watch --config /etc/caddy/Caddyfile --adapter caddyfile
environment=HTTP_PROXY="http://127.0.0.1:8380",HTTPS_PROXY="http://127.0.0.1:8380"
autostart=true
autorestart=true
startretries=3
user=root

stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

stopsignal=TERM

[program:caddy-reload]
command=/usr/bin/caddy reload --config /etc/caddy/Caddyfile
autostart=false
autorestart=false
startsecs=0
EOF

# MITM Proxy

RUN mkdir -p /root/.mitmproxy
COPY --chown=root:root --chmod=755 ./mitmproxy/start-mitmproxy.sh /usr/local/bin/start-mitmproxy
COPY ./mitmproxy/rewrite-host.py /rewrite-host.py
COPY ./mitmproxy/mock-responder.py /mock-responder.py

COPY <<EOF /etc/supervisor/conf.d/mitmproxy.conf
[program:mitmproxy]
directory=/root/.mitmproxy
command=/usr/bin/script -q -c "/usr/local/bin/start-mitmproxy" /dev/null
autostart=true
autorestart=true
startretries=3
user=root

stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

stopsignal=TERM
EOF

# CITM Utils

RUN <<EOF
uv pip install --system mako
EOF

COPY citm-utils /citm-utils
WORKDIR /citm-utils

RUN <<EOF
rm -rf .venv __pycache__
uv sync
EOF

COPY <<EOF /etc/supervisor/conf.d/citm-utils.conf
[program:citm-utils-web]
directory=/citm-utils
command=uv run gunicorn -w 4 -b 0.0.0.0:5000 --enable-stdio-inheritance app:app
autostart=true
autorestart=true
startretries=3
user=root

stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

stopsignal=TERM

[program:citm-utils-dns-forwarder]
directory=/citm-utils
command=uv run python dns_forwarder.py
autostart=true
autorestart=true
startretries=3
user=root

stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

stopsignal=TERM
EOF

COPY <<EOF /start-supervisord
#!/usr/bin/env bash

set -euo pipefail

COMMON_TIP_MESSAGE="Did you run the certificate maker script?"

if [ ! -f /certs/rootCA.pem ]; then
    echo "ERROR: /certs/rootCA.pem not found. \${COMMON_TIP_MESSAGE}" >&2
    exit 1
fi

if [ ! -f /certs/rootCA-key.pem ]; then
    echo "ERROR: /certs/rootCA-key.pem not found. \${COMMON_TIP_MESSAGE}" >&2
    exit 1
fi

install -m 644 -o root -g root "/certs/rootCA.pem" /usr/local/share/ca-certificates/citm-root-ca.crt
update-ca-certificates

exec supervisord "\$@"
EOF

RUN chmod 755 /start-supervisord

HEALTHCHECK --interval=5s --timeout=5s --start-period=5s --retries=60 \
    CMD curl -fsS \
    --connect-timeout 3 \
    https://utils.citm.internal:3858/health \
    || exit 1

CMD ["/start-supervisord"]
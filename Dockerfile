# syntax=docker/dockerfile:1

FROM caddy:2-builder AS caddy-builder

RUN xcaddy build \
    --with github.com/abiosoft/caddy-yaml

FROM mitmproxy/mitmproxy

# Supervisord
RUN <<EOF
apt-get update -y
apt-get install -y supervisor

rm -rf /etc/supervisor
mkdir -p /var/log/supervisor
mkdir -p /var/run
mkdir -p /etc/supervisor/conf.d
EOF

COPY --chown=root:root --chmod=644 <<EOF /etc/supervisor/supervisord.conf
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

[inet_http_server]
port=0.0.0.0:9001

[include]
files = /etc/supervisor/conf.d/*.conf
EOF

# Caddy
COPY --from=caddy-builder /usr/bin/caddy /usr/bin/caddy
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
EOF

# Dnsmasq
RUN <<EOF
apt-get update -y
apt-get install -y dnsmasq
mkdir -p /etc/default
echo "CONFIG_DIR=/etc/dnsmasq.d,.dpkg-dist,.dpkg-old,.dpkg-new\nIGNORE_RESOLVCONF=yes" > /etc/default/dnsmasq
rm -f /etc/dnsmasq.conf
rm -rf /etc/dnsmasq.d
mkdir -p /etc/dnsmasq.d /etc/dnsmasq-user.d
EOF

COPY ./dnsmasq/dnsmasq.conf /etc/dnsmasq.conf
COPY --chown=root:root --chmod=755 ./dnsmasq/start-dnsmasq.sh /usr/local/sbin/start-dnsmasq

COPY <<EOF /etc/supervisor/conf.d/dnsmasq.conf
[program:dnsmasq]
command=/usr/local/sbin/start-dnsmasq
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

# MITM Proxy

RUN <<EOF
pip3 install flask --root-user-action=ignore
pip3 install gunicorn --root-user-action=ignore
EOF

RUN mkdir -p /root/.mitmproxy
COPY --chown=root:root --chmod=755 ./mitmproxy/start-mitmproxy.sh /usr/local/bin/start-mitmproxy
COPY ./mitmproxy/rewrite-host.py /rewrite-host.py

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

COPY --chown=root:root --chmod=755 <<EOF /start-supervisord
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

exec supervisord "\$@"
EOF

# CITM Utils
COPY citm-utils /citm-utils

COPY <<EOF /etc/supervisor/conf.d/citm-utils.conf
[program:citm-utils]
directory=/citm-utils
command=python3 -m gunicorn -w 1 -b 0.0.0.0:5000 app:app
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

CMD [ "/start-supervisord" ]

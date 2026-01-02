# syntax=docker/dockerfile:1

FROM caddy:2-builder AS caddy-builder

RUN xcaddy build \
    --with github.com/abiosoft/caddy-yaml

FROM mitmproxy/mitmproxy

# Common tools
RUN <<EOF
apt-get update -y
apt-get install -y socat curl iputils-ping ca-certificates
EOF

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
command=/usr/bin/caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
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
echo "CONFIG_DIR=/etc/dnsmasq.d,.dpkg-dist,.dpkg-old,.dpkg-new\nIGNORE_RESOLVCONF=yes" >/etc/default/dnsmasq
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

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

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
command=uv run gunicorn -w 1 -b 0.0.0.0:5000 --enable-stdio-inheritance app:app
autostart=true
autorestart=true
startretries=3
user=root

stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0

stopsignal=TERM

[program:citm-utils-dnsmasq-updater]
directory=/citm-utils
command=uv run python dnsmasq-updater.py
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

ARG DEVCONTAINER=false
RUN /bin/bash <<EOF
if [ "${DEVCONTAINER}" != "false" ]; then

  chsh -s /bin/zsh \$USERNAME

  apt-get install -y \
    build-essential \
    git \
    git-lfs \
    golang \
    jq \
    neovim \
    tmux \
    vim \
    zsh

  uv tool install black
  uv tool install rust-just

  # Go tools
  go install github.com/google/yamlfmt/cmd/yamlfmt@latest
  go install github.com/reteps/dockerfmt@latest

  # Node.js 24.x
  curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
  apt-get update
  apt-get install -y --no-install-recommends nodejs

  npm install -g dclint

  # starship
  curl -fsSL https://starship.rs/install.sh -o /tmp/install_starship.sh
  chmod +x /tmp/install_starship.sh
  /tmp/install_starship.sh -y
  rm -f /tmp/install_starship.sh
  
  # Docker
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  
  tee /etc/apt/sources.list.d/docker.sources <<INEOF
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: \$(. /etc/os-release && echo "\$VERSION_CODENAME")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
INEOF

apt-get update -y
apt-get install -y docker-ce-cli docker-buildx-plugin docker-compose-plugin

  cat > "\$HOME/.zshrc" <<'INEOF'
export PATH="\$HOME/.local/bin:\$HOME/go/bin:\$PATH"

mkdir -p "\$HOME/.zsh/completion"
just --completions=zsh > "\$HOME/.zsh/completion/_just"

fpath=("\$HOME/.zsh/completion" \$fpath)
autoload -U compinit
compinit
eval "\$(starship init zsh)"
INEOF
fi
EOF

CMD ["/start-supervisord"]